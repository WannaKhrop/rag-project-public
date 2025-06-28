"""
Module to create TenneT RAG Tool for integration with OpenWebUI.

Title: Tennet RAG Tool
Author: Ivan Khrop
Date: 2025-06-13
"""

import requests
from pydantic import Field, BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Tools:
    """Tool class which is used inside OpenWebUI as extended functionality."""

    class Valves(BaseModel):
        """Configuration data for the tool."""

        # RAG Server URL
        rag_server_url: str = Field(
            default=None,
            description="URL where RAG Server is running.",
        )

        # RAG Server Port
        rag_server_port: str = Field(default=None, description="Port for RAG Server.")

    def __init__(self):
        self.valves = self.Valves()

    # Add your custom tools using pure Python code here, make sure to add type hints and descriptions
    def retrieve_from_rag(
        self, query: str = Field(default=None, description="Answer the provided query using RAG.")
    ) -> str:
        """
        Answer the query using Retrieval Augumented Generation.

        :param query: query, received from a user.
        """
        # add call information to the log
        logger.info(msg=f"New query: {query}")

        if self.valves.rag_server_url is None:
            return "Server URL is not configured."

        if self.valves.rag_server_port is None:
            return "Server Port is not configured."

        if query is None:
            return "There is nothing to response."

        base_url = f"{self.valves.rag_server_url}:{self.valves.rag_server_port}/query"
        params = {"query": query}

        try:
            response = requests.post(base_url, json=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)

            logger.info(f"Query Result: {response.json()}")

            return response.json()

        except requests.RequestException as e:
            return f"Error fetching data: {str(e)}"
