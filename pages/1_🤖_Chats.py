import json
import re

import streamlit as st
from sqlalchemy.exc import DBAPIError

from agent import get_agent
from backup import backup_conversation, load_conversation
from common import Conversation, init_session_state

st.set_page_config(
    page_title="Chats",
    page_icon="🤖",
)

# Initialize session state variables
init_session_state()


def new_chat_button_on_click():
    st.session_state.current_conversation = ""


def set_conversation(conversation_id):
    st.session_state.current_conversation = conversation_id


def retry_chat(prompt: str, stream: bool):
    st.session_state.retry = {"stream": stream, "prompt": prompt}


def conversation_exists(id: str) -> bool:
    return id != "" and id in st.session_state.conversations


def conversation_valid(id: str):
    if conversation_exists(id):
        conversation: Conversation = st.session_state.conversations[id]
        return conversation.vector_store_id in st.session_state.vector_stores and all(
            [x in st.session_state.databases for x in conversation.database_ids]
        )

    return False


# Sidebar
with st.sidebar:
    st.markdown("## Chats")

    st.button("➕ New chat", on_click=new_chat_button_on_click)

    upload_file = st.file_uploader("Restore conversation from JSON")

    if upload_file:
        conversation = load_conversation(json.load(upload_file))
        st.session_state.conversations[conversation.id] = conversation

        st.toast("Conversation restored!", icon="✔️")

    st.divider()

    if conversation_exists(st.session_state.current_conversation):
        st.markdown("## Current conversation")

        conversation_id = st.session_state.current_conversation
        with st.expander(conversation_id):
            # TODO: put fields to update conversation params here and update last_update_timestamp whenever they're submitted
            with st.empty():
                if st.button("Backup conversation"):
                    backup_file = json.dumps(backup_conversation(conversation_id))

                    no_whitespace_name = re.sub(r"\s+", '_', conversation_id)
                    st.download_button("Download backup JSON", data=backup_file, file_name=f"chatdb_{no_whitespace_name}.json")

        st.divider()

    st.markdown("## Select conversation")
    for conversation_id in st.session_state.conversations.keys():
        st.button(conversation_id, on_click=set_conversation, args=[conversation_id])

# Main view
if not conversation_exists(st.session_state.current_conversation):
    st.title("New conversation")

    # Display form for creating a new conversation
    with st.form("new_conversation_form"):
        conversation_id = st.text_input("Conversation title")

        agent_model = st.text_input("Agent model", value="gpt-3.5-turbo-0613")
        predictor_model = st.text_input("Predictor model", value="text-davinci-003")

        vector_store_id = st.selectbox("Select vector store", tuple(st.session_state.vector_stores.keys()))
        database_ids = st.multiselect("Select databases", tuple(st.session_state.databases.keys()), max_selections=1)

        if st.form_submit_button():
            if conversation_id in st.session_state.conversations:
                st.error("Conversation title has to be unique!", icon="🚨")
            else:
                st.session_state.conversations[conversation_id] = Conversation(
                    conversation_id, agent_model, predictor_model, vector_store_id, database_ids
                )
                set_conversation(conversation_id)

elif not conversation_valid(st.session_state.current_conversation):
    st.title(st.session_state.current_conversation)

    st.markdown("### Could not load conversation due to missing parameters!\n\nDid you forget to restore the settings?")

elif not st.session_state.openai_key:
    st.error("OpenAI API key not set. Go to ⚙️ Settings page!", "🚨")

else:
    conversation_id = st.session_state.current_conversation
    conversation: Conversation = st.session_state.conversations[conversation_id]

    st.title(conversation_id)

    # Display chat messages from history on app rerun
    for message in conversation.messages:
        with st.chat_message(message.role):
            st.markdown(message.content)

            for query, results in message.query_results:
                with st.expander("View SQL query..."):
                    st.markdown(f"`{query}`")
                    st.table(results)

    # Initialize the agent
    get_agent(conversation_id, conversation.last_update_timestamp)

    if len(conversation.messages) == 0:
        # Add initial message
        conversation.add_message("assistant", "How can I help you today?")

    use_streaming = True
    prompt = st.chat_input("Your query")

    # Allow retrying if the prompt failed last time
    if not prompt and st.session_state.retry:
        use_streaming = st.session_state.retry["stream"]
        prompt = st.session_state.retry["prompt"]
        st.session_state.retry = None

    # Accept user input
    if prompt:
        # Display message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Add user message to chat history
        conversation.add_message("user", prompt)

        # Retrieve agent
        agent = get_agent(conversation_id, conversation.last_update_timestamp)
        full_response = ""

        show_retry_buttons = False

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            try:
                if use_streaming:
                    # Incrementally display response as it is streamed from the agent
                    for response in agent.stream_chat(prompt).response_gen:
                        full_response += response
                        message_placeholder.markdown(full_response + "▌")
                else:
                    # Receive the whole response before displaying it
                    message_placeholder.markdown("*Thinking...*")
                    full_response = agent.chat(prompt).response

            except DBAPIError as e:
                # Show the error to the user
                full_response = "[System] An SQL error has occurred:\n\n"
                full_response += f'Error type: "{type(e.orig).__name__}"\n\n'
                full_response += "```" + str(e.orig).replace("\n", "\n\n") + "```"

            except Exception as e:
                # Show the error to the user and add a "retry" button
                full_response = "[System] An error has occurred:\n\n"
                full_response += "```" + str(e).replace("\n", "\n\n") + "```"

                show_retry_buttons = True
            else:
                if full_response == "":
                    # Something wrong happened
                    full_response = "[System] An error has occurred, possibly related to streaming."
                    show_retry_buttons = True

            # Display full message once it is retrieved
            message_placeholder.markdown(full_response)

            if show_retry_buttons:
                st.button("Retry", on_click=retry_chat, args=[prompt, True])
                st.button("Retry without streaming", on_click=retry_chat, args=[prompt, False])

            # Show expandable elements for every SQL query generated by this prompt
            query_results = []
            for query, results in conversation.query_results_queue:
                query_results.append((query, results))
                with st.expander("View SQL query..."):
                    st.markdown(f"`{query}`")
                    st.table(results)

            conversation.query_results_queue = []

            # Add assistant message to chat history
            conversation.add_message("assistant", full_response, query_results)
