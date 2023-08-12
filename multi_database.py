from typing import Callable, Dict, Iterable, List, Optional

from llama_hub.tools.database.base import DatabaseToolSpec
from llama_index import Document
from llama_index.readers.base import BaseReader
from llama_index.tools.tool_spec.base import BaseToolSpec
from sqlalchemy import text
from sqlalchemy.exc import InvalidRequestError


class NoSuchDatabaseError(InvalidRequestError):
    """Database does not exist or is not visible to a connection."""


class TrackingDatabaseToolSpec(DatabaseToolSpec):
    handler: Callable[[str, str, Iterable], None]
    database_name: str

    def set_handler(self, func: Callable) -> None:
        self.handler = func

    def set_database_name(self, database_name: str) -> None:
        self.database_name = database_name

    def load_data(self, query: str) -> List[Document]:
        """Query and load data from the Database, returning a list of Documents.

        Args:
            query (str): an SQL query to filter tables and rows.

        Returns:
            List[Document]: A list of Document objects.
        """
        documents = []
        with self.sql_database.engine.connect() as connection:
            if query is None:
                raise ValueError("A query parameter is necessary to filter the data")
            else:
                result = connection.execute(text(query))

            items = result.fetchall()

            if self.handler:
                self.handler(self.database_name, query, items)

            for item in items:
                # fetch each item
                doc_str = ", ".join([str(entry) for entry in item])
                documents.append(Document(text=doc_str))
        return documents


class MultiDatabaseToolSpec(BaseToolSpec, BaseReader):
    database_specs: Dict[str, TrackingDatabaseToolSpec]
    handler: Callable[[str, str, Iterable], None]

    spec_functions = ["load_data", "describe_tables", "list_tables", "list_databases"]

    def __init__(
        self,
        database_toolspec_mapping: Optional[Dict[str, TrackingDatabaseToolSpec]] = None,
        handler: Optional[Callable[[str, str, Iterable], None]] = None,
    ) -> None:
        self.database_specs = database_toolspec_mapping or dict()
        self.handler = handler

        for spec in self.database_specs.values():
            spec.set_handler(self.handler)

    def add_connection(self, database_name: str, uri: str) -> None:
        spec = TrackingDatabaseToolSpec(uri=uri)
        spec.set_handler(self.handler)
        spec.set_database_name(database_name)
        self.database_specs[database_name] = spec

    def add_database_tool_spec(self, database_name: str, tool_spec: TrackingDatabaseToolSpec) -> None:
        tool_spec.set_handler(self.handler)
        tool_spec.set_database_name(database_name)
        self.database_specs[database_name] = tool_spec

    def load_data(self, database: str, query: str) -> List[Document]:
        """Query and load data from the given Database, returning a list of Documents.

        Args:
            database (str): A database name to query and load data from
            query (str): an SQL query to filter tables and rows.

        Returns:
            List[Document]: A list of Document objects.
        """

        if database not in self.database_specs:
            raise NoSuchDatabaseError(f"Database '{database}' does not exist.")

        return self.database_specs[database].load_data(query)

    def describe_tables(self, database: str, tables: Optional[List[str]] = None) -> str:
        """
        Describes the specifed tables in the given database

        Args:
            database (str): A database name to retrieve the table details from
            tables (List[str]): A list of table names to retrieve details about
        """

        if database not in self.database_specs:
            raise NoSuchDatabaseError(f"Database '{database}' does not exist.")

        return self.database_specs[database].describe_tables(tables)

    def list_tables(self, database: str) -> List[str]:
        """
        Returns a list of available tables in the database.
        To retrieve details about the columns of specfic tables, use
        the describe_tables endpoint

        Args:
            database (str): A database name to retrieve the list of tables from
        """

        if database not in self.database_specs:
            raise NoSuchDatabaseError(f"Database '{database}' does not exist.")

        return self.database_specs[database].list_tables()

    def list_databases(self) -> List[str]:
        """
        Returns a list of available databases.
        To retrieve details about the tables of a specfic database, use
        the list_tables endpoint
        """
        return list(self.database_specs.keys())
