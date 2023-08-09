from abc import ABC, abstractmethod
from datetime import datetime
from enum import IntEnum
from typing import Dict, List, Tuple

import openai
import streamlit as st


class BaseVectorStoreProps(ABC):
    id: str

    def __init__(self, id) -> None:
        self.id = id

    @abstractmethod
    def get_props(self) -> dict:
        pass


class InMemoryVectorStoreProps(BaseVectorStoreProps):
    def get_props(self) -> dict:
        return {"Type": "In-memory"}


class PineconeVectorStoreProps(BaseVectorStoreProps):
    api_key: str
    environment: str
    index_name: str

    def __init__(self, id: str, api_key: str, environment: str, index_name: str) -> None:
        super().__init__(id)

        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name

    def get_props(self) -> dict:
        return {
            "Type": "Pinecone",
            "API key": self.api_key,
            "Environment": self.environment,
            "Index name": self.index_name,
        }


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

    query_results: List[Tuple[str, list]]

    def __init__(self, role, content, query_results=None) -> None:
        self.role = role
        self.content = content

        self.query_results = query_results or []


class Conversation:
    id: str

    agent_model: str
    predictor_model: str

    vector_store_id: str
    database_ids: List[str]

    messages: List[Message]
    query_results_queue: List[Tuple[str, list]]

    # Used to invalidate get_agent() cache
    # Whenever we update the vector stores/database ids of a conversation, we update this timestamp
    # so that get_agent() will be re-executed
    last_update_timestamp: float

    def __init__(
        self,
        id: str,
        agent_model: str,
        predictor_model: str,
        vector_store_id: str,
        database_ids: List[str],
        messages: List[Message] = None,
    ) -> None:
        self.id = id
        self.agent_model = agent_model
        self.predictor_model = predictor_model

        self.vector_store_id = vector_store_id
        self.database_ids = list(database_ids)

        self.messages = list(messages) if messages else list()
        self.query_results_queue = list()

        self.update_timestamp()

    def add_message(self, role, content, query_results=None):
        self.messages.append(Message(role, content, query_results))

    def update_timestamp(self):
        self.last_update_timestamp = datetime.now().timestamp()


def init_session_state():
    if "openai_key" not in st.session_state:
        st.session_state.openai_key = ""

    if "vector_stores" not in st.session_state:
        st.session_state.vector_stores: Dict[str, BaseVectorStoreProps] = dict()

    if "databases" not in st.session_state:
        st.session_state.databases: Dict[str, DatabaseProps] = dict()

    if "conversations" not in st.session_state:
        st.session_state.conversations: Dict[str, Conversation] = dict()

    if "current_conversation" not in st.session_state:
        st.session_state.current_conversation: str = ""

    if "retry" not in st.session_state:
        st.session_state.retry = None


def set_openai_api_key(api_key):
    # Set API key in openai module
    openai.api_key = api_key
    st.session_state.openai_key = api_key
