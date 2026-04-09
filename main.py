from utils.pandas_operations import ReadPipelines
from utils.logfiles import setup_logger
from utils.tracker import File_And_Tracker
from src.selenium_operations.driver_setup import DriverSetup
from pages.tariff_list_page import TariffListPage
from pages.tariff_browser_page import TariffBrowserPage
import time
import os
from dotenv import load_dotenv


load_dotenv()
logger = setup_logger("main")

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

def main():
    try:
        
        current_dir = os.getcwd()
        pipelines = get_pipeline_name()
        for pipeline_name in pipelines:
            logger.info(f"Retrived pipeline {pipeline_name}. \n")
        
            start_time = time.time()
            tracker_file = File_And_Tracker(main_path=current_dir, pipelines=pipeline_name)
            pipeline_folder = tracker_file.create_pipeline_folder()
            logger.info(f"Created folder for to store {pipeline_name} file. \n")

            download_dir = os.path.abspath(pipeline_folder)

            driver_setup = DriverSetup(browser_name="chrome", download_folder=download_dir, headless=False)

            driver = driver_setup.setup_browser()
            driver_setup.open_url(os.getenv("URL"))
            
            process_first_page = TariffListPage(driver, pipelinename=pipeline_name)
            process_second_page = TariffBrowserPage(driver)

            company_name, tariff_option, tariff_text = process_first_page.process_tariff_list()

            if tariff_text.startswith("Currently"):
                print(f"No tariff files available for {company_name}.")
                logger.info(f"No tariff files available for {company_name}. \n")
                driver_setup.quit_browser()
            
            tariff_option.click()
            
            process_second_page.process_tariff_browser()

            file = tracker_file.get_latest_file(file_path=download_dir)
            if file:
                print(f"Latest downloaded file: {file}")
                logger.info(f"Latest downloaded file: {file}. \n")

            end_time = time.time() 
            time_taken = end_time - start_time
            
            tracker_file.create_excel_tracker_files(company_name=company_name, tariff_program=tariff_text, is_effective="Yes", file_status="Downloaded", time_taken=time_taken)
            driver_setup.quit_browser()

    except Exception as e:
        logger.error(f"An error occurred in the main function: {e} \n")
        print(f"An error occurred in the main function: {e}")



if __name__=="__main__":
    main()
