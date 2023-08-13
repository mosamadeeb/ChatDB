import json

import streamlit as st

# For clarity
from cryptography.fernet import InvalidToken as InvalidEncryptionKey

from backup import backup_settings, load_settings
from common import DatabaseProps, init_session_state, set_openai_api_key

st.set_page_config(
    page_title="Settings",
    page_icon="⚙️",
)

NEW_DATABASE_TEXT = "➕ Add new database"

# Initialize session state variables
init_session_state()

st.title("⚙️ Settings")

st.divider()

st.markdown("## OpenAI API key")
with st.form("openai_key_form", clear_on_submit=True):
    api_key = st.text_input("API key", type="password")

    if st.form_submit_button():
        set_openai_api_key(api_key)

if st.session_state.openai_key:
    st.info("API key is set.", icon="ℹ️")
else:
    st.warning("API key is not set.", icon="⚠️")

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
        "Database identifier",
        value=id,
        help="Choose a proper, relevant name or just the database name. Used by the model to distinguish between different databases.",
    )

    database_uri = st.text_input(
        "Connection URI",
        value=uri,
        help="Use the format: `dialect://username:password@host:port/database`, where dialect can be postgresql, mysql, oracle, etc.",
    )

    if st.button("Submit", key="database_submit_button"):
        if props and props.id != database_id:
            # Remove existing database if we're going to rename it
            st.session_state.databases.pop(props.id)

        if not props and database_id in st.session_state.databases:
            # A new entry is being added, so it should have a unique id
            st.error("Database identifier has to be unique!", icon="🚨")
        else:
            st.session_state.databases[database_id] = DatabaseProps(database_id, database_uri)
            st.success("Database saved!", icon="✔️")

with st.expander("View databases"):
    st.table({k: {"URI": st.session_state.databases[k].get_uri_without_password()} for k in st.session_state.databases})

st.divider()

st.markdown("## Backup settings")

st.markdown("- ### Backup")
password = st.text_input(
    "Encryption password",
    help="This will be used to encrypt your API keys before backup. If no password is provided, the data will still be encrypted but using a common encryption key",
    type="password",
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
                type="password",
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
