import streamlit as st
from llama_index.agent import OpenAIAgent
from llama_index.agent.openai_agent import ChatMessage
from llama_index.llms import OpenAI

from common import Conversation, DatabaseProps
from multi_database import MultiDatabaseToolSpec, TrackingDatabaseToolSpec


@st.cache_resource(show_spinner="Loading LLM...")
def get_llm(model: str, api_key: str):
    # API key is a parameter here to force invalidate the cache whenever the API key is changed
    _ = api_key
    return OpenAI(model=model)


@st.cache_resource(show_spinner="Connecting to database...")
def get_database_spec(database_id: str) -> TrackingDatabaseToolSpec:
    database: DatabaseProps = st.session_state.databases[database_id]

    db_spec = TrackingDatabaseToolSpec(
        uri=database.uri,
    )

    # Set the database name for query tracking
    db_spec.database_name = database_id

    return db_spec


def database_spec_handler(database, query, items):
    conversation = st.session_state.conversations[st.session_state.current_conversation]
    conversation.query_results_queue.append((database, query, items))


@st.cache_resource(show_spinner="Creating agent...")
def get_agent(conversation_id: str, last_update_timestamp: float):
    # Used for invalidating the cache when we want to force create a new agent
    _ = last_update_timestamp

    conversation: Conversation = st.session_state.conversations[conversation_id]

    # Set a handler that can be called whenever a query is executed
    database_tools = MultiDatabaseToolSpec(handler=database_spec_handler)

    # Create tools
    for database_id in conversation.database_ids:
        db_spec = get_database_spec(database_id)
        database_tools.add_database_tool_spec(database_id, db_spec)

    tools = database_tools.to_tool_list()

    # Load chat history from the conversation's messages
    chat_history = list(map(lambda m: ChatMessage(role=m.role, content=m.content), conversation.messages))

    # Create an LLM with the specified model
    llm = get_llm(conversation.agent_model, st.session_state.openai_key)

    # Create the Agent with our tools
    agent = OpenAIAgent.from_tools(tools, llm=llm, chat_history=chat_history)

    return agent
