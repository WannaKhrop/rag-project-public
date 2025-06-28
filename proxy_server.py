"""
Module describes a proxy server between OpenWebUI and Azure Endpoint Model.

Author: Ivan Khrop
Date: 17.06.2025
"""

# run uvicorn proxy_server:app --host 0.0.0.0 --port 8500 in the terminal

from fastapi import FastAPI, Request
import requests
from typing import Any
import os

app = FastAPI()

AZURE_ENDPOINT = os.getenv("BASE_ENDPOINT_URL")
AZURE_API_KEY = os.getenv("ENDPOINT_API_KEY")

assert AZURE_ENDPOINT is not None and AZURE_API_KEY is not None

AZURE_DEPLOYMENT = "azure-deployed-prod"  # or hardcode


@app.get("/v1/models")
def list_models() -> dict[str, Any]:
    """Describe all available models."""
    # Return dummy list with your deployment name
    return {
        "object": "list",
        "data": [
            {
                "id": AZURE_DEPLOYMENT,
                "object": "model",
                "owned_by": "azure",
            }
        ],
    }


@app.post("/v1/chat/completions")
async def proxy_chat(request: Request):
    """Initiate chat with Azure Endpoint."""
    body = await request.json()

    body.setdefault("temperature", 0.01)
    body.setdefault("max_tokens", 4096)
    body.setdefault("top_p", 0.95)
    body.setdefault("frequency_penalty", 0.0)
    body.setdefault("presence_penalty", 0.0)
    body["model"] = AZURE_DEPLOYMENT  # Force model name

    headers = {
        "Authorization": f"Bearer {AZURE_API_KEY}",
        "Content-Type": "application/json",
        "azureml-model-deployment": AZURE_DEPLOYMENT,
    }

    response = requests.post(str(AZURE_ENDPOINT), json=body, headers=headers)
    return response.json()
