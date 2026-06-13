from utils.pandas_operations import ReadPipelines
from utils.logfiles import setup_logger
from src.selenium_operations.driver_setup import DriverSetup
from src.selenium_operations.download_files import download_files
from src.pdf_operations.pdf_extraction.final_export import export_data
import time
import os
from dotenv import load_dotenv
import requests

load_dotenv()
logger = setup_logger("main")


def check_connection():
    try:
        response = requests.get("https://www.google.com", timeout=5)
        if response:
            return True
        else:
            return False
    except Exception as r:
        logger.error(f"An error occured while connecting to internet. {r}")
        return False
    

# function to get pipeline names from the source csv file
def get_pipeline_name():
    try:
        data = ReadPipelines(os.getenv("INPUT_FILE"))

        df = data.read_and_clean_csv()

        pipeline_name = df['PipelineName']
        
        return pipeline_name
    except Exception as e:
        logger.error(f"Error getting pipeline name: {e}")
        return None


def selenium_process():
    try:
        retries = 3
        wait_time = 2

        for attempt in range(retries + 1):

            if check_connection() == False:
                logger.error("Internet Disconnected")
            
            driver_setup = DriverSetup(browser_name="chrome", headless=True)

            current_dir = os.getcwd()
            pipelines = get_pipeline_name() # fetching pipelines

            if pipelines is None:
                logger.error("Pipelines are not available in the file, or the CSV file path is invalid or not available.")

            driver = driver_setup.setup_browser() # driver setup
            driver_setup.open_url(os.getenv("URL"))

            download_files(driver, driver_setup, pipelines, current_dir)


    except Exception as e:
        logger.error(f"An error occurred at main process: {e}")
        print(f"An error occurred at main process: {e}")
        logger.error(f"Retrying in {wait_time} seconds...")

        if attempt > retries:
            return
        
        time.sleep(wait_time)
        wait_time *= 2  
    finally:
        if driver:
            driver_setup.quit_browser()


def pdf_extraction_process():
    try:
        export_data()
    except Exception as e:
        logger.error(f"An error occurred during PDF extraction: {e} ")
        print(f"An error occurred during PDF extraction: {e}")


def main():
    selenium_process()

    # pdf_extraction_process()


if __name__=="__main__":
    main()
