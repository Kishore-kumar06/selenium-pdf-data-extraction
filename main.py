from utils.pandas_operations import ReadPipelines
from utils.logfiles import setup_logger
from utils.tracker import File_And_Tracker
from src.selenium_operations.driver_setup import DriverSetup
from pages.tariff_list_page import TariffListPage
from pages.tariff_browser_page import TariffBrowserPage
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
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as r:
        print(f"An error occured while connecting to internet. {r}")
        return False
    

# Function to get pipelines
def get_pipeline_name():
    try:
        data = ReadPipelines(os.getenv("INPUT_FILE"))
        df = data.read_and_clean_csv()
        pipeline_name = df['PipelineName']
        return pipeline_name
    except Exception as e:
        logger.error(f"Error getting pipeline name: {e} \n")
        print(f"Error getting pipeline name: {e}")


def download_files(driver, driver_setup, pipelines, current_dir):
    try:      

        for pipeline_name in pipelines:
            logger.info(f"Retrived pipeline {pipeline_name}. \n")
        
            start_time = time.time()
            tracker_file = File_And_Tracker(main_path=current_dir, pipelines=pipeline_name)
            pipeline_folder = tracker_file.create_pipeline_folder()
            logger.info(f"Created folder for to store {pipeline_name} file. \n")

            download_dir = os.path.abspath(pipeline_folder)

            driver_setup.set_download_path(download_dir)
            
            process_first_page = TariffListPage(driver, pipelinename=pipeline_name)
            process_second_page = TariffBrowserPage(driver)

            company_name, tariff_option, tariff_text = (
                process_first_page.process_tariff_list()
            )

            print(tariff_text)

            # Skip pipeline if no tariff exists
            if tariff_option is None:

                logger.info(
                    f"Skipping {pipeline_name} - no files available"
                )

                print(
                    f"Skipping {pipeline_name} - no files available"
                )

                tracker_file.create_excel_tracker_files(
                    company_name=company_name,
                    tariff_program=tariff_text,
                    is_effective="No",
                    file_status="No File Available",
                    time_taken=0
                )

                driver_setup.navigate_back()
                continue


            tariff_option.click()

            process_second_page.process_tariff_browser()

            file = tracker_file.get_latest_file(file_path=download_dir)
            if file:
                logger.info(f"Latest downloaded file: {file}. \n")

            end_time = time.time() 
            time_taken = end_time - start_time
            
            tracker_file.create_excel_tracker_files(
                company_name=company_name, 
                tariff_program=tariff_text, 
                is_effective="Yes", 
                file_status="Downloaded", 
                time_taken=time_taken
            )

            driver_setup.navigate_back()
            driver_setup.navigate_back()

    except Exception as e:
        logger.error(f"An error occurred while downloading pipeline files: {e} \n")
        print(f"An error occurred while downloading pipeline files: {e} \n")


def selenium_process():
    try:
        retries = 3
        wait_time = 2

        for attempt in range(retries + 1):


            if check_connection() == False:
                logger.error("Internet Disconnected")
                raise Exception("Internet Disconnected")
            
            driver_setup = DriverSetup(browser_name="chrome", headless=True)

            current_dir = os.getcwd()
            pipelines = get_pipeline_name()

            driver = driver_setup.setup_browser()
            driver_setup.open_url(os.getenv("URL"))

            download_files(driver, driver_setup, pipelines, current_dir)


    except Exception as e:
        logger.error(f"An error occurred at main process: {e} \n")
        print(f"An error occurred at main process: {e} \n")
        logger.error(f"Retrying in {wait_time} seconds... \n")

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
        logger.error(f"An error occurred during PDF extraction: {e} \n")
        print(f"An error occurred during PDF extraction: {e}")


def main():
    # selenium_process()

    pdf_extraction_process()


if __name__=="__main__":
    main()
