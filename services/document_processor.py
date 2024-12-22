import asyncio
import fitz  # PyMuPDF
import json
import os
import logging
from docx2pdf import convert
from dotenv import load_dotenv
from openai import AsyncOpenAI
from os.path import join, dirname
from utils.prompts import SYSTEM_PROMPT, EXTRACT_FORMAT, COMPARE_FORMAT, RentalAgreement, ComparisonReport
from typing import List
from pydantic import BaseModel
from utils.utils import TempFolderManager, FileHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Main Class for Document Processing
class DocumentProcessor:
    """Process documents to extract text and images or compare them."""

    def __init__(self):
        self.temp_manager = TempFolderManager()
        dotenv_path = join(dirname(__file__), '.env')
        load_dotenv(dotenv_path)
        self.api_key = os.environ.get("OPEN_AI_API_KEY")  # add constants

    async def extract_text_and_images(self, pdf_data: bytes = None, pdf_file: str = None) -> dict:
        """Extract data from PDF binary or file."""
        logger.info("Starting data extraction.")
        temp_folders = set()

        try:
            if pdf_data:
                logger.info("Extracting data from binary input.")
                page_text, images = await self._extract_from_binary(pdf_data)
            elif pdf_file:
                logger.info(f"Extracting data from file: {pdf_file}")
                page_text, images = await self._extract_from_file(pdf_file)
            else:
                raise ValueError("Either pdf_data or pdf_file must be provided.")

            for image_path in images:
                temp_folders.add(os.path.dirname(image_path))

            content = self._prepare_extraction_messages(images, page_text)
            return await self._get_openai_response(content, RentalAgreement)

        finally:
            for folder in temp_folders:
                self.temp_manager.delete_temp_folder(folder)

    async def compare_documents(self, doc1: dict, doc2: dict) -> dict:
        """Compare two documents and generate a comparison report."""
        logger.info("Starting document comparison.")
        comparison_messages = self._prepare_comparison_messages(doc1, doc2)
        return await self._get_openai_response(comparison_messages, ComparisonReport)

    async def _extract_from_binary(self, pdf_data: bytes) -> tuple:
        """Extract text and images from binary PDF data."""
        temp_folder = self.temp_manager.create_temp_folder()
        temp_pdf_path = FileHandler.save_file(temp_folder, "temp_input.pdf", pdf_data)
        return await self._extract_from_file(temp_pdf_path)

    async def _extract_from_file(self, file_path: str) -> tuple:
        """Extract text and images from a PDF or Word file."""
        temp_folder = self.temp_manager.create_temp_folder()
        if file_path.endswith('.docx'):
            logger.info("Converting Word document to PDF.")
            temp_pdf_path = os.path.join(temp_folder, "converted.pdf")
            convert(file_path, temp_pdf_path)
            file_path = temp_pdf_path
        return await self._extract_from_pdf(file_path)

    async def _extract_from_pdf(self, pdf_file: str) -> tuple:
        """Extract text and images from a PDF file."""
        document = fitz.open(pdf_file)
        images, extracted_text = [], ""
        temp_folder = self.temp_manager.create_temp_folder()

        for page_num in range(len(document)):
            page = document.load_page(page_num)
            extracted_text += page.get_text()
            temp_img_path = os.path.join(temp_folder, f"page_{page_num + 1}.png")
            page.get_pixmap().save(temp_img_path)
            images.append(temp_img_path)

        return extracted_text, images

    def _prepare_extraction_messages(self, images: List[str], page_text: str) -> List[dict]:
        """Prepare messages for text and image extraction."""
        messages = [{"type": "text", "role": "system", "content": SYSTEM_PROMPT}]
        for image in images:
            base64_image = FileHandler.encode_image_to_base64(image)
            messages.append(
                {
                    "type": "image_url",
                    "role": "user",
                    "content": "parse Image",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"},
                }
            )
        messages.append(
            {"type": "text", "role": "user", "content": f"META DATA: Use this Text Parsed from Document for your Response:\n\n {page_text}"}
        )
        messages.append({"type": "text", "role": "user", "content": EXTRACT_FORMAT})
        return messages

    def _prepare_comparison_messages(self, doc1: dict, doc2: dict) -> List[dict]:
        """Prepare messages for document comparison."""
        messages = [
            {"type": "text", "role": "system", "content": SYSTEM_PROMPT + "\nYou are a smart agreement comparer for generating a subjective comparison report in JSON."},
            {"type": "text", "role": "user", "content": f"Document-1 Data:\n {json.dumps(doc1, indent=2)}"},
            {"type": "text", "role": "user", "content": f"Document-2 Data:\n {json.dumps(doc2, indent=2)}"},
            {"type": "text", "role": "user", "content": COMPARE_FORMAT},
        ]
        return messages

    async def _get_openai_response(self, content: List[dict], format: BaseModel) -> dict:
        """Get response from OpenAI's API."""
        logger.info("Sending request to OpenAI API.")
        client = AsyncOpenAI(api_key=self.api_key)
        temperature = 0.0125
        maxtokens = 2000
        fpenalty = 0.007
        presencepenalty = 0.007
        response = await client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            response_format=format,
            messages=content,
            temperature=temperature,
            max_tokens=maxtokens,
            frequency_penalty=fpenalty,
            presence_penalty=presencepenalty,
        )
        try:
            final_response = response.choices[0].message.parsed
            logger.info("Received response from OpenAI API.")
            return final_response.dict(by_alias=True)
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {}

# Example Usage
if __name__ == "__main__":
    processor = DocumentProcessor()
    # Add example calls or test cases as required
