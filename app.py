import streamlit as st
import asyncio
import os
import pandas as pd
import shutil
from uuid import uuid4
from get_openai_response import extract_data, compare_documents
from copy import deepcopy

# Streamlit multipage setup
st.set_page_config(page_title="Rent Agreement Tool", layout="wide")

BASE_DIR = "./uploaded_files"
os.makedirs(BASE_DIR, exist_ok=True)

if "acr" not in st.session_state:
    st.session_state["acr"] = False
if "doc1_data" not in st.session_state:
    st.session_state["doc1_data"] = None
if "doc2_data" not in st.session_state:
    st.session_state["doc2_data"] = None

def save_uploaded_file(uploaded_file):
    """Save the uploaded file to a folder with a UUID."""
    folder_path = os.path.join(BASE_DIR, str(uuid4()))
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    return file_path, folder_path

async def extract_and_set_state(file_path, doc_key):
    """Extract data asynchronously and update session state."""
    try:
        extracted_data = await extract_data(pdf_file=file_path)
        st.session_state[doc_key] = extracted_data
    except Exception as e:
        st.error(f"An error occurred during data extraction: {e}")

def cleanup_folder(folder_path):
    """Clean up the temporary folder."""
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

# Page navigation
def main_page():
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
                # Save uploaded files with UUID folder structure
                doc1_path, folder1 = save_uploaded_file(doc1)
                doc2_path, folder2 = save_uploaded_file(doc2)

                with st.spinner("Extracting data from documents, please wait..."):
                    asyncio.run(extract_and_set_state(doc1_path, "doc1_data"))
                    asyncio.run(extract_and_set_state(doc2_path, "doc2_data"))
                    cleanup_folder(folder1)
                    cleanup_folder(folder2)

                if st.session_state["doc1_data"] and st.session_state["doc2_data"]:
                    st.rerun()

    if st.session_state["doc1_data"] and st.session_state["doc2_data"]:
        extracted_data_page()

# Page to show extracted data
def extracted_data_page():
    st.title("Extracted Data")

    st.subheader("Extracted Data from Document 1")
    dc1 = deepcopy(st.session_state["doc1_data"])
    ctdc1 = dc1.pop("CriticalTerms", None)
    doc1_df = pd.DataFrame.from_dict(dc1, orient="index", columns=["Value"])
    st.table(doc1_df)
    if ctdc1:
        st.subheader("Critical Terms Document 1")
        st.table(ctdc1)

    st.subheader("Extracted Data from Document 2")
    dc2 = deepcopy(st.session_state["doc2_data"])
    ctdc2 = dc2.pop("CriticalTerms", None)
    doc2_df = pd.DataFrame.from_dict(dc2, orient="index", columns=["Value"])
    st.table(doc2_df)
    if ctdc2:
        st.subheader("Critical Terms Document 2")
        st.table(ctdc2)

    if st.button("Agreement Comparison Report"):
        st.session_state["acr"] = True
        st.rerun()

# Page to compare documents
def comparison_page():
    st.title("Agreement Comparison Report")
    with st.spinner("Comparing documents, please wait..."):
        try:
            comparison = asyncio.run(
                compare_documents(st.session_state["doc1_data"], st.session_state["doc2_data"])
            )
            st.subheader("Comparison Report")
            # Convert the comparison response into a DataFrame
            comparison_df = pd.DataFrame(comparison['ComparisonReport'])
            st.table(comparison_df)
        except Exception as e:
            st.error(f"An error occurred during comparison: {e}")

    # Show extracted data below the comparison report
    st.title("Extracted Data")

    st.subheader("Extracted Data from Document 1")
    dc1 = deepcopy(st.session_state["doc1_data"])
    ctdc1 = dc1.pop("CriticalTerms", None)
    doc1_df = pd.DataFrame.from_dict(dc1, orient="index", columns=["Value"])
    st.table(doc1_df)
    if ctdc1:
        st.subheader("Critical Terms Document 1")
        st.table(ctdc1)

    st.subheader("Extracted Data from Document 2")
    dc2 = deepcopy(st.session_state["doc2_data"])
    ctdc2 = dc2.pop("CriticalTerms", None)
    doc2_df = pd.DataFrame.from_dict(dc2, orient="index", columns=["Value"])
    st.table(doc2_df)
    if ctdc2:
        st.subheader("Critical Terms Document 2")
        st.table(ctdc2)

# Page routing
if st.session_state.get("acr"):
    comparison_page()
elif st.session_state.get("doc1_data") and st.session_state.get("doc2_data"):
    extracted_data_page()
else:
    main_page()
