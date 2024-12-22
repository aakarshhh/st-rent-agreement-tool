import os
import shutil
from uuid import uuid4
import base64
from utils.constants import DocumentProcessorConstants

class TempFolderManager:
    """Manage temporary folders for file operations."""

    BASE_DIR = DocumentProcessorConstants.PROCESSED_FILES

    def __init__(self):
        os.makedirs(self.BASE_DIR, exist_ok=True)

    def create_temp_folder(self) -> str:
        """Create a temporary folder with a UUID."""
        folder_path = os.path.join(self.BASE_DIR, str(uuid4()))
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    def delete_temp_folder(self, folder_path: str):
        """Delete a temporary folder and its contents."""
        print(f"[LOG] Deleting temporary folder: {folder_path}")
        try:
            shutil.rmtree(folder_path)
        except Exception as e:
            print(f"[ERROR] Failed to delete temporary folder {folder_path}: {e}")


class FileHandler:
    """Handle file-related operations."""

    @staticmethod
    def save_file(folder_path: str, filename: str, data: bytes) -> str:
        """Save a file in the specified folder."""
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "wb") as file:
            file.write(data)
        return file_path

    @staticmethod
    def encode_image_to_base64(image_path: str) -> str:
        """Encode an image file to base64."""
        print(f"[LOG] Encoding image to base64: {image_path}")
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")