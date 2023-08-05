import streamlit as st

from common import (
    DatabaseProps,
    InMemoryVectorStoreProps,
    PineconeVectorStoreProps,
    VectorStoreType,
    get_vector_store_type,
    init_session_state,
)

st.set_page_config(
    page_title="Settings",
    page_icon="⚙️",
)

# Initialize session state variables
init_session_state()

st.title("⚙️ Settings")

st.divider()

NEW_VECTOR_STORE_TEXT = "➕ Add new vector store"
NEW_DATABASE_TEXT = "➕ Add new database"

# Vector stores
st.markdown("## Vector stores")
with st.expander("Configure"):
    vector_store_selection = st.selectbox(
        "Select vector store", (NEW_VECTOR_STORE_TEXT, *st.session_state.vector_stores.keys())
    )

    props = None
    if vector_store_selection != NEW_VECTOR_STORE_TEXT:
        props = st.session_state.vector_stores[vector_store_selection]

    id = props.id if props else ""
    index = int(get_vector_store_type(props)) if props else 0

    vector_store_id = st.text_input(
        "Vector store identifier",
        value=id,
        help="Identifying name for choosing a vector store when creating a conversation",
    )

    # Disable type selection for existing vector stores
    select_disabled = props is not None
    vector_store_type = st.selectbox(
        "Vector store type",
        (VectorStoreType.InMemory, VectorStoreType.PineconeDB),
        index=index,
        disabled=select_disabled,
    )

    # Set the correct type for existing vector stores
    if select_disabled:
        vector_store_type = get_vector_store_type(props)

    match vector_store_type:
        case VectorStoreType.InMemory:
            pass
        case VectorStoreType.PineconeDB:
            api_key = props.api_key if props else ""
            environment = props.environment if props else ""
            index_name = props.index_name if props else ""

            st.text_input("Pinecone API Key", value=api_key, key="pinecone_api_input", type="password")
            st.text_input("Pinecone Environment", value=environment, key="pinecone_env_input")
            st.text_input("Pinecone Index Name", value=index_name, key="pinecone_index_name_input")

    if st.button("Submit", key="vector_submit_button"):
        if props and props.id != vector_store_id:
            # Remove existing vector store if we're going to rename it
            st.session_state.vector_stores.pop(props.id)

        match vector_store_type:
            case VectorStoreType.InMemory:
                st.session_state.vector_stores[vector_store_id] = InMemoryVectorStoreProps(vector_store_id)
            case VectorStoreType.PineconeDB:
                pinecone_api = st.session_state["pinecone_api_input"]
                pinecone_env = st.session_state["pinecone_env_input"]
                pinecone_index_name = st.session_state["pinecone_index_name_input"]

                st.session_state.vector_stores[vector_store_id] = PineconeVectorStoreProps(
                    vector_store_id, pinecone_api, pinecone_env, pinecone_index_name
                )

        st.toast("Vector store saved!", icon="✔️")

st.divider()

# Databases
st.markdown("## Databases")
with st.expander("Configure"):
    database_selection = st.selectbox("Select database", (NEW_DATABASE_TEXT, *st.session_state.databases.keys()))

    id = ""
    uri = ""

    props = None
    if database_selection != NEW_DATABASE_TEXT:
        props = st.session_state.databases[database_selection]

        id = props.id
        uri = props.uri

    database_id = st.text_input(
        "Database identifier", value=id, help="Identifying name for choosing a database when creating a conversation"
    )

    database_uri = st.text_input("Connection URI", value=uri)

    if st.button("Submit", key="database_submit_button"):
        if props and props.id != database_id:
            # Remove existing database if we're going to rename it
            st.session_state.databases.pop(props.id)

        st.session_state.databases[database_id] = DatabaseProps(database_id, database_uri)
        st.toast("Database saved!", icon="✔️")
