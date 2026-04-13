import os
from dotenv import load_dotenv

load_dotenv()

def load_pdf_files():
    try:
        transformed_files_path = os.path.join(os.getenv("INPUT_PDF_FILES_PATH"))

        for root, _, files in os.walk(transformed_files_path):
            for file in files:
                full_path = os.path.join(root, file)
                yield full_path

    except Exception as er:
        print(f"An error occurred while fetching transformed files: {er}")
