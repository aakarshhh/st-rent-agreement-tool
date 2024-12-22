import streamlit as st
import asyncio
import pandas as pd
import shutil
from uuid import uuid4
from copy import deepcopy

import sys
import os
# Add the root directory (where 'services' is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.document_processor import DocumentProcessor
from utils.constants import FrontendConstants

# Streamlit multipage setup
st.set_page_config(page_title="Rent Agreement Tool", layout="wide")

# Base directory for uploaded files
BASE_DIR = FrontendConstants.UPLOAD_DIR
os.makedirs(BASE_DIR, exist_ok=True)

# Initialize session state variables
if "acr" not in st.session_state:
    st.session_state["acr"] = False
if "doc1_data" not in st.session_state:
    st.session_state["doc1_data"] = None
if "doc2_data" not in st.session_state:
    st.session_state["doc2_data"] = None

# Initialize DocumentProcessor
processor = DocumentProcessor()

class FileManager:
    """Handles file saving and cleanup operations."""

    @staticmethod
    def save_uploaded_file(uploaded_file):
        """
        Save the uploaded file to a folder with a UUID.

        Args:
            uploaded_file: The uploaded file object from Streamlit.

        Returns:
            A tuple containing the file path and folder path.
        """
        folder_path = os.path.join(BASE_DIR, str(uuid4()))
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        return file_path, folder_path

    @staticmethod
    def cleanup_folder(folder_path):
        """
        Clean up the temporary folder created for uploaded files.

        Args:
            folder_path: The path of the folder to delete.
        """
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

async def extract_and_set_state(file_path, doc_key):
    """
    Extract data asynchronously and update session state.

    Args:
        file_path: The path to the uploaded file.
        doc_key: The session state key to update with extracted data.
    """
    try:
        extracted_data = await processor.extract_text_and_images(pdf_file=file_path)
        st.session_state[doc_key] = extracted_data
    except Exception as e:
        st.error(f"An error occurred during data extraction: {e}")

def main_page():
    """
    Main page for the tool, allowing users to upload and extract data from documents.
    """
    st.title("Rent Agreement Data Extraction")
    st.write("Upload documents to extract key details.")

    if not st.session_state["doc1_data"] and not st.session_state["doc2_data"]:
        col1, col2 = st.columns(2)
        with col1:
            doc1 = st.file_uploader("Document-1", type=["pdf", "docx"], key="doc1", help="Upload the first document.")
        with col2:
            doc2 = st.file_uploader("Document-2", type=["pdf", "docx"], key="doc2", help="Upload the second document.")

        if st.button("Extract Data"):
            if not doc1 or not doc2:
                st.error("Please upload both documents to proceed.")
            else:
                doc1_path, folder1 = FileManager.save_uploaded_file(doc1)
                doc2_path, folder2 = FileManager.save_uploaded_file(doc2)

                with st.spinner("Extracting data from documents, please wait..."):
                    asyncio.run(extract_and_set_state(doc1_path, "doc1_data"))
                    asyncio.run(extract_and_set_state(doc2_path, "doc2_data"))
                    FileManager.cleanup_folder(folder1)
                    FileManager.cleanup_folder(folder2)

                if st.session_state["doc1_data"] and st.session_state["doc2_data"]:
                    st.rerun()

    if st.session_state["doc1_data"] and st.session_state["doc2_data"]:
        extracted_data_page()

def extracted_data_page():
    """
    Page to display extracted data from the uploaded documents.
    """
    st.title("Extracted Data")

    st.subheader("Extracted Data from Document 1")
    doc1_data = deepcopy(st.session_state["doc1_data"])
    critical_terms_doc1 = doc1_data.pop("CriticalTerms", None)
    doc1_df = pd.DataFrame.from_dict(doc1_data, orient="index", columns=["Value"])
    st.table(doc1_df)
    if critical_terms_doc1:
        st.subheader("Critical Terms Document 1")
        st.table(critical_terms_doc1)

    st.subheader("Extracted Data from Document 2")
    doc2_data = deepcopy(st.session_state["doc2_data"])
    critical_terms_doc2 = doc2_data.pop("CriticalTerms", None)
    doc2_df = pd.DataFrame.from_dict(doc2_data, orient="index", columns=["Value"])
    st.table(doc2_df)
    if critical_terms_doc2:
        st.subheader("Critical Terms Document 2")
        st.table(critical_terms_doc2)

    if st.button("Agreement Comparison Report") and st.session_state["acr"]!=True:
        st.session_state["acr"] = True
        st.rerun()

def comparison_page():
    """
    Page to compare the extracted data from both documents.
    """
    st.title("Agreement Comparison Report")

    with st.spinner("Comparing documents, please wait..."):
        try:
            comparison = asyncio.run(
                processor.compare_documents(st.session_state["doc1_data"], st.session_state["doc2_data"])
            )
            st.subheader("Comparison Report")
            # Convert the comparison response into a DataFrame
            comparison_df = pd.DataFrame(comparison['ComparisonReport'])
            st.table(comparison_df)
        except Exception as e:
            st.error(f"An error occurred during comparison: {e}")

    st.title("Extracted Data")

    st.subheader("Extracted Data from Document 1")
    doc1_data = deepcopy(st.session_state["doc1_data"])
    critical_terms_doc1 = doc1_data.pop("CriticalTerms", None)
    doc1_df = pd.DataFrame.from_dict(doc1_data, orient="index", columns=["Value"])
    st.table(doc1_df)
    if critical_terms_doc1:
        st.subheader("Critical Terms Document 1")
        st.table(critical_terms_doc1)

    st.subheader("Extracted Data from Document 2")
    doc2_data = deepcopy(st.session_state["doc2_data"])
    critical_terms_doc2 = doc2_data.pop("CriticalTerms", None)
    doc2_df = pd.DataFrame.from_dict(doc2_data, orient="index", columns=["Value"])
    st.table(doc2_df)
    if critical_terms_doc2:
        st.subheader("Critical Terms Document 2")
        st.table(critical_terms_doc2)


# Page routing logic
if st.session_state.get("acr"):
    comparison_page()
elif st.session_state.get("doc1_data") and st.session_state["doc2_data"]:
    extracted_data_page()
else:
    main_page()
