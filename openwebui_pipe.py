"""
Module to create custom RAG Pipeline for integration with OpenWebUI.

Title: RAG Pipeline
Author: Ivan Khrop
Date: 2025-06-13
"""

import requests
from pydantic import Field, BaseModel
from typing import List, Union, Generator, Iterator, Any, Optional


class Pipeline:
    """RAG Pipeline Class with methods required for OpenWebUI."""

    class Valves(BaseModel):
        """Important configuration data for Pipeline."""

        pipelines: List[str] = ["*"]
        rag_server_url: str = "http://host.docker.internal"
        rag_server_port: str = "8100"

    def __init__(self):
        # Optionally, you can set the id and name of the pipeline.
        # Best practice is to not specify the id so that it can be automatically inferred from the filename, so that users can install multiple versions of the same pipeline.
        # The identifier must be unique across all pipelines.
        # The identifier must be an alphanumeric string that can include underscores or hyphens. It cannot contain spaces, special characters, slashes, or backslashes.

        self.name = "RAG Pipeline"
        self.valves = self.Valves()
        self.tools = None

    def retrieve_from_rag(
        self, query: str = Field(default=None, description="Answer the provided query using RAG.")
    ) -> dict[str, Any]:
        """
        Answer the query using Retrieval Augumented Generation external server.

        Parameters
        ----------
        query: str
            Query from user to be answered.

        Returns
        -------
        dict[str, Any]
            Answer as JSON-dict like {"answer": "...", "references": "..." }.
        """
        # append server data
        base_url = f"{self.valves.rag_server_url}:{self.valves.rag_server_port}/query"
        params = {"query": query}

        try:
            response = requests.post(base_url, json=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)

            return response.json()

        except requests.RequestException as e:
            return {"answer": f"Error fetching data: {str(e)}"}

    async def on_startup(self):
        """Do something when the server is started."""
        # Add you code here
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        """Do something when the server is stopped."""
        # Add you code here
        print(f"on_shutdown:{__name__}")
        pass

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Apply filter to the form data BEFORE it is sent to the LLM API."""
        # Add you code here
        print(f"inlet:{__name__}")
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Apply filter to the form data AFTER it is sent to the LLM API."""
        # Add you code here
        print(f"outlet:{__name__}")
        return body

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        Call the selected LLM model using the user message and message history.

        Parameters
        ----------
        user_message: str
            Query from the user side.
        model_id: str
            Model that must be called .
        messages: list[dict]
            List of messages in the chat.
        body: dict
            Chat information including messages and other data.
        """
        # skip useless messages to not spam RAG server
        if "</chat_history>" in user_message:
            return ""

        try:
            # call RAG
            answer = self.retrieve_from_rag(query=user_message)

            # parse the answer
            text_answer: str = ""
            if "answer" in answer:
                text_answer = str(answer["answer"])

            references: dict = dict()
            if "references" in answer:
                references = answer["references"]

            # format table to string
            md_table = ""
            if references and isinstance(references, dict) and len(references) > 0:
                columns = list(references.keys())
                num_rows = len(references[columns[0]])

                # Header
                md_table += "| " + " | ".join(columns) + " |\n"
                md_table += "| " + " | ".join(["---"] * len(columns)) + " |\n"

                # Rows
                for i in range(num_rows):
                    row = [str(references[col].get(str(i), "-")) for col in columns]
                    md_table += "| " + " | ".join(row) + " |\n"

            # return the final string
            if md_table:
                return text_answer + "\n\n" + "References: \n" + md_table
            else:
                return text_answer

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            raise
