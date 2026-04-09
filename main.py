from utils.pandas_operations import ReadPipelines
from utils.logfiles import setup_logger
from utils.tracker import File_And_Tracker
import os
from dotenv import load_dotenv
from src.selenium_operations.driver_setup import DriverSetup
from src.selenium_operations.base_page import BrowserActions
from pages.tariff_list import TariffListPage
from pages.tariff_browser import TariffBrowserPage
from selenium import webdriver
import time

load_dotenv()
logger = setup_logger("main")

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
        
            start_time = time.time()
            tracker_file = File_And_Tracker(main_path=current_dir, pipelines=pipeline_name, company_name="", tariff_program="", is_effective="", file_status="", time_taken="", file_path=None)
            pipeline_folder = tracker_file.create_pipeline_folder()
            print(pipeline_folder)

            download_dir = os.path.abspath(pipeline_folder)

            driver_setup = DriverSetup(browser_name="chrome", download_folder=download_dir, headless=False)

            driver = driver_setup.setup_browser()
            driver_setup.open_url(os.getenv("URL"))
            driver.implicitly_wait(5)
            
            process_first_page = TariffListPage(driver, pipelinename=pipeline_name)
            process_second_page = TariffBrowserPage(driver)

            company_name, tariff_option, tariff_text = process_first_page.process_tariff_list()

            if tariff_text.startswith("Currently"):
                print(f"No tariff files available for {company_name}.")
                logger.info(f"No tariff files available for {company_name}.")
                driver_setup.quit_browser()
            else:
                tariff_option.click()
                print(f"Tariff option for {company_name}: {tariff_option}")
                logger.info(f"Tariff option for {company_name}: {tariff_option}")
            
                process_second_page.process_tariff_browser()

                # file = tracker_file.get_latest_file(pipeline_name=download_dir)
                # if file:
                #     print(f"Latest downloaded file: {file}")
                #     logger.info(f"Latest downloaded file: {file}")

                end_time = time.time() 
                time_taken = end_time - start_time
                driver_setup.quit_browser()
                tracker_file.create_excel_tracker_files(main_path=current_dir, pipelines=pipeline_name, company_name=company_name, tariff_program=tariff_text, is_effective="Yes", file_status="Downloaded", time_taken=str(time_taken))
               

    except Exception as e:
        logger.error(f"An error occurred in the main function: {e} \n")
        print(f"An error occurred in the main function: {e}")
    
if __name__=="__main__":
    main()
