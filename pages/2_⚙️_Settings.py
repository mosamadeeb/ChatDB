import json

import streamlit as st

# For clarity
from cryptography.fernet import InvalidToken as InvalidEncryptionKey

from backup import backup_settings, load_settings
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

NEW_VECTOR_STORE_TEXT = "➕ Add new vector store"
NEW_DATABASE_TEXT = "➕ Add new database"

# Initialize session state variables
init_session_state()

st.title("⚙️ Settings")

st.divider()

st.markdown("## OpenAI API key")
with st.form("openai_key_form", clear_on_submit=True):
    api_key = st.text_input("API key")

    if st.form_submit_button():
        st.session_state.openai_key = api_key

if st.session_state.openai_key:
    st.info("API key is set.", icon="ℹ️")
else:
    st.warning("API key is not set.", icon="⚠️")

st.divider()

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

with st.expander("View vector stores"):
    st.table({k: v.get_props() for k, v in st.session_state.vector_stores.items()})

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

with st.expander("View databases"):
    st.table({k: {"URI": st.session_state.databases[k].uri} for k in st.session_state.databases})

st.divider()

st.markdown("## Backup settings")

st.markdown("- ### Backup")
password = st.text_input(
    "Encryption password",
    help="This will be used to encrypt your API keys before backup. If no password is provided, the data will still be encrypted but using a common encryption key",
)

with st.empty():
    if st.button("Prepare backup"):
        # Prepare JSON file
        backup_file = json.dumps(backup_settings(password), indent=2)

        if password:
            st.info("Your backup is encrypted with the password you provided.", icon="ℹ️")

        st.download_button("Download settings JSON", data=backup_file, file_name="chatdb_settings.json")

st.markdown("- ### Restore")
upload_file = st.file_uploader("Restore settings from JSON")

if upload_file:
    backup_file = json.load(upload_file)

    loaded = False
    try:
        if "use_default_key" in backup_file and not backup_file["use_default_key"]:
            st.markdown("Backup is encrypted!")
            password = st.text_input(
                "Decryption password",
                help="This is the same password you used to encrypt your backup. Leave this empty if you did not use a password when backing up.",
            )

            if st.button("Decrypt and restore"):
                load_settings(backup_file, password)
                loaded = True
        else:
            load_settings(backup_file, None)
            loaded = True
    except InvalidEncryptionKey:
        st.error("Invalid decryption key.", icon="🚨")
    else:
        if loaded:
            st.success("Settings restored!", icon="✔️")
