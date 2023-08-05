from datetime import datetime
from enum import IntEnum
from typing import Dict, List

import streamlit as st


class BaseVectorStoreProps:
    id: str

    def __init__(self, id) -> None:
        self.id = id


class InMemoryVectorStoreProps(BaseVectorStoreProps):
    pass


class PineconeVectorStoreProps(BaseVectorStoreProps):
    api_key: str
    environment: str
    index_name: str

    def __init__(
        self, id: str, api_key: str, environment: str, index_name: str
    ) -> None:
        super().__init__(id)

        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name


class VectorStoreType(IntEnum):
    InMemory = 0
    PineconeDB = 1

    def __str__(self) -> str:
        match self:
            case VectorStoreType.InMemory:
                return "In-memory"
            case VectorStoreType.PineconeDB:
                return "Pinecone DB"


# Matching by type name to avoid a weird bug where isinstance does not work
def get_vector_store_type(vector_store) -> VectorStoreType:
    match type(vector_store).__name__:
        case InMemoryVectorStoreProps.__name__:
            return VectorStoreType.InMemory
        case PineconeVectorStoreProps.__name__:
            return VectorStoreType.PineconeDB
        case _:
            # TODO: do something better here
            return None


class DatabaseProps:
    id: str
    uri: str

    def __init__(self, id, uri) -> None:
        self.id = id
        self.uri = uri


class Message:
    role: str
    content: str

    def __init__(self, role, content) -> None:
        self.role = role
        self.content = content


class Conversation:
    id: str

    vector_store_id: str
    database_ids: List[str]

    messages: List[Message]

    # Used to invalidate get_agent() cache
    # Whenever we update the vector stores/database ids of a conversation, we update this timestamp
    # so that get_agent() will be re-executed
    last_update_timestamp: float

    def __init__(
        self,
        id,
        vector_store_id: str,
        database_ids: List[str],
        messages: List[Message] = None,
    ) -> None:
        self.id = id
        self.vector_store_id = vector_store_id
        self.database_ids = list(database_ids)

        self.messages = list(messages) if messages else list()

        self.update_timestamp()

    def add_message(self, role, content):
        self.messages.append(Message(role, content))

    def update_timestamp(self):
        self.last_update_timestamp = datetime.now().timestamp()


# TODO: add support for loading a serialized session state from json
def init_session_state():
    if "vector_stores" not in st.session_state:
        st.session_state.vector_stores: Dict[str, BaseVectorStoreProps] = dict()

    if "databases" not in st.session_state:
        st.session_state.databases: Dict[str, DatabaseProps] = dict()

    if "conversations" not in st.session_state:
        st.session_state.conversations: Dict[str, Conversation] = dict()

    if "current_conversation" not in st.session_state:
        st.session_state.current_conversation: str = ""
