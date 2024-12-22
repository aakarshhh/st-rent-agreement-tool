import asyncio
import base64
import fitz  # PyMuPDF
import json
import os
from docx2pdf import convert
from dotenv import load_dotenv
from openai import AsyncOpenAI
from os.path import join, dirname
from prompts import SYSTEM_PROMPT, EXTRACT_FORMAT, COMPARE_FORMAT , RentalAgreement , ComparisonReport
from typing import List
from uuid import uuid4
from pydantic import BaseModel
import shutil

def delete_temp_folder(folder_path: str):
    """Delete a temporary folder and its contents."""
    print(f"[LOG] Deleting temporary folder: {folder_path}")
    try:
        shutil.rmtree(folder_path)
    except Exception as e:
        print(f"[ERROR] Failed to delete temporary folder {folder_path}: {e}")

# Load environment variables from .env file
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# OpenAI API Key
OPEN_AI_API_KEY = os.environ.get("OPEN_AI_API_KEY")

BASE_DIR = "./processed_files"
os.makedirs(BASE_DIR, exist_ok=True)

def create_folder_with_uuid() -> str:
    """Create a folder with a UUID as its name."""
    folder_path = os.path.join(BASE_DIR, str(uuid4()))
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def save_file_in_folder(folder_path: str, filename: str, data: bytes):
    """Save a file in the specified folder."""
    file_path = os.path.join(folder_path, filename)
    with open(file_path, "wb") as file:
        file.write(data)
    return file_path

async def extract_text_and_images_from_binary(pdf_data: bytes) -> tuple:
    """Extract text and images from a PDF binary data."""
    print("[LOG] Extracting text and images from binary PDF data.")
    temp_folder = create_folder_with_uuid()
    temp_pdf_path = save_file_in_folder(temp_folder, "temp_input.pdf", pdf_data)
    print(f"[LOG] Temporary PDF file created: {temp_pdf_path}")
    extracted_text, images = await extract_text_and_images_from_file(temp_pdf_path)
    return extracted_text, images


async def extract_text_and_images_from_file(file_path: str) -> tuple:
    """Extract text and images from a PDF or Word file."""
    print(f"[LOG] Extracting text and images from file: {file_path}")
    temp_folder = create_folder_with_uuid()
    if file_path.endswith('.docx'):
        print("[LOG] Converting Word document to PDF.")
        temp_pdf_path = os.path.join(temp_folder, "converted.pdf")
        convert(file_path, temp_pdf_path)
        file_path = temp_pdf_path
    return await extract_text_and_images_from_pdf(file_path)

async def extract_text_and_images_from_pdf(pdf_file: str) -> tuple:
    """Extract text and images from a PDF file."""
    print(f"[LOG] Extracting text and images from PDF: {pdf_file}")
    document = fitz.open(pdf_file)
    images = []
    extracted_text = ""
    temp_folder = create_folder_with_uuid()
    for page_num in range(len(document)):
        print(f"[LOG] Processing page {page_num + 1} of {len(document)}.")
        page = document.load_page(page_num)
        extracted_text += page.get_text()
        # Save page as an image
        temp_img_path = os.path.join(temp_folder, f"page_{page_num + 1}.png")
        pixmap = page.get_pixmap()
        pixmap.save(temp_img_path)
        print(f"[LOG] Saved page image to: {temp_img_path}")
        images.append(temp_img_path)
    return extracted_text, images


def encode_image_to_base64(image_path: str) -> str:
    """Encode an image file to base64."""
    print(f"[LOG] Encoding image to base64: {image_path}")
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def prepare_extraction_messages(images: List[str], page_text: str) -> List[dict]:
    """Prepare messages for text and image extraction."""
    print("[LOG] Preparing extraction messages.")
    messages = [
        {"type": "text", "role":"system", "content": SYSTEM_PROMPT}
    ]
    for image in images:
        base64_image = encode_image_to_base64(image)
        messages.append(
            {
                "type": "image_url",
                "role":"user",
                "content":"parse Image",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"},
            }
        )
    messages.append(
        {"type": "text","role":"user", "content": f"META DATA: Use this Text Parsed from Document for your Response:\n\n {page_text}"}
    )
    messages.append({"type": "text","role":"user", "content": EXTRACT_FORMAT})
    return messages

async def get_openai_response(content: List[dict] , format:BaseModel) -> dict:
    """Get response from OpenAI's API."""
    print("[LOG] Sending request to OpenAI API.")
    client = AsyncOpenAI(api_key=OPEN_AI_API_KEY)
    response = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        response_format=format,
        messages=content,
        temperature=0.0125,
        max_tokens=2000,
        frequency_penalty=0.007,
        presence_penalty=0.007,
    )
    try:
        final_response :format= response.choices[0].message.parsed
        print("[LOG] Received response from OpenAI API.")
    except Exception as e:
        print(f"[ERROR] Error parsing response: {e}")
        return {}
    return final_response.dict(by_alias=True)

async def extract_data(pdf_data: bytes = None, pdf_file: str = None) -> dict:
    """Extract data from PDF binary or file."""
    print("[LOG] Starting data extraction.")
    temp_folders = set()  # Use a set to store unique folder paths from image paths

    try:
        if pdf_data:
            print("[LOG] Extracting data from binary input.")
            page_text, images = await extract_text_and_images_from_binary(pdf_data)
        elif pdf_file:
            print(f"[LOG] Extracting data from file: {pdf_file}")
            page_text, images = await extract_text_and_images_from_file(pdf_file)
        else:
            raise ValueError("Either pdf_data or pdf_file must be provided.")

        # Extract folder paths from image paths
        for image_path in images:
            folder = os.path.dirname(image_path)
            temp_folders.add(folder)

        content = prepare_extraction_messages(images, page_text)
        final_response = await get_openai_response(content, RentalAgreement)
        print("[LOG] Data extraction complete.")
        return final_response

    finally:
        # Cleanup all identified folders
        for folder in temp_folders:
            try:
                shutil.rmtree(folder)
                print(f"[LOG] Deleted temporary folder: {folder}")
            except Exception as e:
                print(f"[ERROR] Failed to delete temporary folder {folder}: {e}")

def prepare_comparison_messages(doc1: dict, doc2: dict) -> List[dict]:
    """Prepare messages for document comparison."""
    print("[LOG] Preparing comparison messages.")
    messages = [
        {"type": "text", "role":"system","content": SYSTEM_PROMPT + "\nYou are a smart agreement comparer for generating a subjective comparison report in JSON."}
    ]
    messages.append(
        {"type": "text","role":"user", "content": f"Document-1 Data:\n {json.dumps(doc1, indent=2)}"}
    )
    messages.append(
        {"type": "text","role":"user", "content": f"Document-2 Data:\n {json.dumps(doc2, indent=2)}"}
    )
    messages.append({"type": "text","role":"user", "content": COMPARE_FORMAT})
    return messages

async def compare_documents(doc1: dict, doc2: dict) -> dict:
    """Compare two documents and generate a comparison report."""
    print("[LOG] Starting document comparison.")
    comparison_messages = prepare_comparison_messages(doc1, doc2)
    final_response = await get_openai_response(comparison_messages , ComparisonReport)
    print("[LOG] Document comparison complete.")
    return final_response
