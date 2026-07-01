import os
from dotenv import load_dotenv
import random
import time

load_dotenv()

def load_pdf_files():
    try:
        if not os.path.exists(os.getenv("INPUT_PDF_FILES_PATH")):
           os.makedirs(os.getenv("INPUT_PDF_FILES_PATH"))
           print(f"Created directory for transformed files at: {os.getenv('INPUT_PDF_FILES_PATH')}")
           
        transformed_files_path = os.path.join(os.getenv("INPUT_PDF_FILES_PATH"))

        for root, _, files in os.walk(transformed_files_path):
            for file in files:
                full_path = os.path.join(root, file)
                yield full_path

    except Exception as er:
        print(f"An error occurred while fetching transformed files: {er}")


def delay_process():
    delay = random.uniform(1.0, 3.0)
    return delay