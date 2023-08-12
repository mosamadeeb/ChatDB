import pinecone
import streamlit as st
from llama_index import Document, ServiceContext, StorageContext, VectorStoreIndex
from llama_index.agent import OpenAIAgent
from llama_index.agent.openai_agent import ChatMessage
from llama_index.llms import OpenAI
from llama_index.tools import QueryEngineTool
from llama_index.tools.types import ToolMetadata
from llama_index.vector_stores import PineconeVectorStore, SimpleVectorStore

from common import Conversation, DatabaseProps, VectorStoreType, get_vector_store_type
from multi_database import MultiDatabaseToolSpec, TrackingDatabaseToolSpec


@st.cache_resource(show_spinner="Loading LLM...")
def get_llm(model: str, api_key: str):
    # API key is a parameter here to force invalidate the cache whenever the API key is changed
    _ = api_key
    return OpenAI(model=model)


@st.cache_resource(show_spinner="Retrieving vector store...")
def get_storage_context(vector_store_id: str):
    vector_store_props = st.session_state.vector_stores[vector_store_id]

    vector_store = None
    match get_vector_store_type(vector_store_props):
        case VectorStoreType.InMemory:
            vector_store = SimpleVectorStore()

        case VectorStoreType.PineconeDB:
            # Initialize connection to pinecone
            pinecone.init(
                api_key=vector_store_props.api_key,
                environment=vector_store_props.environment,
            )

            # Create the index if it does not exist already
            index_name = vector_store_props.index_name
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(index_name, dimension=1536, metric="cosine")

            # Connect to the index
            pinecone_index = pinecone.Index(index_name)
            vector_store = PineconeVectorStore(pinecone_index=pinecone_index)

    # Setup our storage (vector db)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    return storage_context


@st.cache_resource(show_spinner="Connecting to database...")
def get_database_spec(database_id: str) -> TrackingDatabaseToolSpec:
    database: DatabaseProps = st.session_state.databases[database_id]

    db_spec = TrackingDatabaseToolSpec(
        uri=database.uri,
    )

    # Set the database name for query tracking
    db_spec.database_name = database_id

    return db_spec


@st.cache_resource(show_spinner="Generating tools...")
def get_query_tool(vector_store_id: str, database_id: str, predictor_model: str) -> QueryEngineTool:
    # This function is cached as a resource, so calling it here is fine
    db_spec = get_database_spec(database_id)

    table_list = db_spec.list_tables()

    documents = []
    for table in table_list:
        description = db_spec.describe_tables([table])
        documents.append(Document(text=f'Definition of "{table}" table:\n{description}'))

    # Create LLM with the specified model
    llm = get_llm(predictor_model, st.session_state.openai_key)
    service_context = ServiceContext.from_defaults(llm=llm)

    # Get the storage context to create a vector index with it
    storage_context = get_storage_context(vector_store_id)
    index = VectorStoreIndex.from_documents(
        documents=documents, storage_context=storage_context, service_context=service_context
    )

    clean_database_id = database_id.replace(" ", "_")

    engine = index.as_query_engine()
    query_tool = QueryEngineTool(
        query_engine=engine,
        metadata=ToolMetadata(
            name=f"{clean_database_id}_query_engine",
            description=f"Contains table descriptions for the {clean_database_id} database",
        ),
    )

    return query_tool


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
