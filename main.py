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

def main():
    # try:
    #     data = ReadPipelines(os.getenv("INPUT_FILE"))
    #     df = data.read_and_clean_csv()
    #     logger.info("CSV file read and cleaned successfully.\n")  
    #     print(df.head())  # Print the first few rows of the cleaned DataFrame for verification
        
    # except Exception as e:
    #     print(f"An error occurred in the main function: {e}")
    #     logger.error(f"An error occurred in the main function: {e}\n")

    current_dir = os.getcwd()
    tracker_file = File_And_Tracker(main_path=current_dir, pipelines=os.getenv("PIPELINE_NAME"), company_name="", tariff_program="", is_effective="", file_status="", time_taken="", file_path=None)
    pipeline_folder = tracker_file.create_pipeline_folder()
    print(f"Pipeline folder created at: {pipeline_folder}")

    driver_setup = DriverSetup(browser_name="chrome", download_folder=pipeline_folder, headless=False)

    driver = driver_setup.setup_browser()
    print(driver.name)
    driver_setup.open_url(os.getenv("URL"))
    time.sleep(3)

    
    process_first_page = TariffListPage(driver)
    process_second_page = TariffBrowserPage(driver)

    company_name, tariff_option, tariff_text = process_first_page.process_tariff_list()

    if tariff_text.startswith("Currently"):
        print(f"No tariff files available for {company_name}.")
        logger.info(f"No tariff files available for {company_name}.")
        driver_setup.quit_browser()
        return
    else:
        tariff_option.click()
        print(f"Tariff option for {company_name}: {tariff_option}")
        logger.info(f"Tariff option for {company_name}: {tariff_option}")
    
        process_second_page.process_tariff_browser()

        file = tracker_file.get_latest_file(pipeline_name=os.getenv("PIPELINE_NAME"))
        if file:
            print(f"Latest downloaded file: {file}")
            logger.info(f"Latest downloaded file: {file}")


    driver_setup.quit_browser()

if __name__=="__main__":
    main()
