
from utils.logfiles import setup_logger
from src.selenium_operations.download_files import download_files
from src.pdf_operations.pdf_extraction.final_export import export_data
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
logger = setup_logger("main")

    
def pdf_extraction_process():
    try:
        export_data()
    except Exception as e:
        logger.error(f"An error occurred during PDF extraction: {e} ")
        print(f"An error occurred during PDF extraction: {e}")


def main():

    start = datetime.now()
    download_files()
    end = datetime.now()

    print(f"Downloaded the file in {end - start}")

    # pdf_extraction_process()


if __name__=="__main__":
    main()


# 57 files in 0:25:09.484016
# 6 files in 0:08:06.835463