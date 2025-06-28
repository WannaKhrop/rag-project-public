"""
Module contains functions and wrappers that can be used to work with the developed RAG System using API Calls.

Author: Ivan Khrop
Date: 15.05.2025
"""

from src.query_processing import reply_query
from src.document_storage import retrieve_reference
from src.metadata import MetaData

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

import logging
import json

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI()


@app.post("/query")
def query_rag(payload: dict) -> str:
    """Ask RAG System."""
    logging.info(msg=payload)

    # get query text
    query = payload.get("query")

    # log query data
    logging.info(msg=f"Query Received: {query}")

    # get response
    answer, references = reply_query(
        user_query=query,
        use_refinement=True,
        n_retrieve=100,
        n_select=10,
        reranking_strategy="cross_encoder",
        min_reranking_score=0.2,
    )

    # convert metadata to DataFrame
    df = MetaData.build_df_for_metadatas(references)

    # build string to answer
    response = {"answer": answer}
    if len(df) > 0:
        response["references"] = df.to_dict(index=True)

    # log the output
    logging.info(msg=f"RAG Reply: {json.dumps(response)}")

    # create a string from response
    return JSONResponse(content=response)


@app.get("/document")
def get_document(doc_name: str, page_from: int, page_to: int) -> Response:
    """Get document view for a reference."""
    # return reference
    content = retrieve_reference(doc_name=doc_name, page_from=page_from, page_to=page_to)

    # return the answer depending on the type
    if doc_name.endswith(".pdf"):
        return Response(content=content, media_type="application/pdf")
    elif doc_name.endswith(".xlsx"):
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
