"""
Module contains the WebApp for using RAG ChatBot.

Author: Ivan Khrop
Date: 08.04.2025
"""
# basic imports
import streamlit as st
import os
import logging
import torch

# custom imports
from src.query_processing import reply_query
from src.metadata import MetaData
from src.document_storage import (
    add_document,
    index_document,
    retrieve_reference,
    index_tabular_document,
)
from streamlit_pdf_viewer import pdf_viewer

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# initialize torch to prevent path error
torch.classes.__path__ = [os.path.join(torch.__path__[0], torch.classes.__file__)]


# create session state variables
def init():
    """Define all variables in streamlit.session_state."""
    # 1. Sign In Status of a User
    if "is_signed_in" in st.session_state:
        del st.session_state.is_signed_in
        del st.session_state.user_login
    # assign values
    st.session_state.is_signed_in = False
    st.session_state.user_login = ""

    # 2. Last Answered Question of a User and Last Answer
    if "messages" not in st.session_state:
        st.session_state.messages = list()


def drop_state():
    """Drop the current session state."""
    st.session_state.messages = list()


# set the title and some initial information
st.set_page_config(layout="wide")
st.title("RAG PoC Application")


def main():
    """Run the application."""
    # request login and password from a user
    if "is_signed_in" not in st.session_state or not st.session_state.is_signed_in:
        # read login and password from env. variables
        login_str = os.environ.get("USER_LOGIN", default="user")
        password_str = os.environ.get("USER_PASSWORD", default="user")
        # check if they are ok
        assert (
            login_str and password_str
        ), "Please provide account details as environmental variables REDACTION_LOGIN and REDACTION_PASSWORD"

        # parse all available logins and passwords
        logins = login_str.split(";")
        passwords = password_str.split(";")
        assert len(logins) == len(
            passwords
        ), "Amount of logins does not correspond to the amount of passwords"
        # define final logging keys
        login_keys = set(
            [(login + ";" + password) for login, password in zip(logins, passwords, strict=True)]
        )

        # get user login and password and check it
        user_login = st.text_input(label="login")
        user_password = st.text_input(label="password", type="password")
        key = user_login + ";" + user_password

        if st.button("Sign In"):
            if key in login_keys:
                # log the sucessful logging
                logging.info(msg=f"User {user_login} singned up in the application.")

                # basic initialization of the App
                init()

                # save login data
                st.session_state.is_signed_in = True
                st.session_state.user_login = user_login
                st.rerun()
            else:
                # log the failed logging
                logging.info(msg=f"User {user_login} failed to sign in.")
                st.error("Please enter valid login and password.")

    # show interface to a user
    else:
        # sidebar navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to", ["RAG Chat", "Update Database"])

        # Asking Questions
        if page == "RAG Chat":
            # show the page header
            st.header("Ask AI Assistant")

            # display all messages in the history
            for message_id, message in enumerate(st.session_state.messages):
                with st.chat_message(name=message["role"]):
                    st.markdown(message["content"])

                    # also show references if they exist
                    if message.get("references") is not None:
                        selection_event = st.dataframe(
                            message["references"],
                            selection_mode="single-row",
                            on_select="rerun",
                            key=message_id,
                        )

                        # if there is a selected document, then visualize it
                        if (
                            selection_event
                            and selection_event.selection
                            and len(selection_event.selection.rows) > 0
                        ):
                            # get the selected and create reference
                            idx = selection_event.selection.rows[0]

                            reference = retrieve_reference(
                                doc_name=message["references"].iloc[idx]["Document"],
                                page_from=int(message["references"].iloc[idx]["Page From"]),
                                page_to=int(message["references"].iloc[idx]["Page To"]),
                            )

                            # visualize the reference
                            if reference is not None:
                                _, center, _ = st.columns([1, 5, 1])
                                with center:
                                    pdf_viewer(reference, width=700)

            # ask question
            if user_query := st.chat_input("Ask something ..."):
                # save a user message
                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": user_query,
                    }
                )

                # now try to response the query
                with st.chat_message("ai"):
                    # run a spinner
                    with st.spinner("Searching for references ..."):
                        # get the answer
                        answer, metadatas = reply_query(
                            user_query=user_query,
                            use_refinement=False,
                            n_retrieve=70,  # select 20 closest chunks from the database
                            n_select=5,  # identify 3 the most appropriate using cross encoder
                            reranking_strategy="cross_encoder",
                            min_reranking_score=0.15,
                        )

                        # convert metadata to DataFrame
                        df = MetaData.build_df_for_metadatas(metadatas)

                # save the answer and rerun the application to show it
                message = {"role": "ai", "content": answer}
                if len(df) > 0:
                    message["references"] = df
                st.session_state.messages.append(message)

                st.rerun()

        # Uploading Documents
        if page == "Update Database":
            # show the page header
            st.header("Uploading New Document in Database")

            # create a file uploader for PDF files
            uploaded_files = st.file_uploader(
                "Upload a PDF file", type=["pdf", "xlsx"], accept_multiple_files=True
            )
            comment = st.text_input("Add a comment for uploading files", value="")

            if uploaded_files and st.button("Update Database"):
                # iterate through the uploaded files and try to incorporate them in Vector Database
                for uploaded_file in uploaded_files:
                    # save the document
                    add_document(name=uploaded_file.name, content=uploaded_file.getbuffer())

                    # add the document to Database depending on the format
                    if uploaded_file.name.endswith(".xlsx"):
                        index_tabular_document(
                            content=uploaded_file.getbuffer(),
                            doc_name=uploaded_file.name,
                            author=st.session_state.user_login,
                            comment=comment,
                        )
                    else:
                        index_document(
                            content=uploaded_file.getbuffer(),
                            doc_name=uploaded_file.name,
                            author=st.session_state.user_login,
                            comment=comment,
                        )


# run main function
if __name__ == "__main__":
    main()
