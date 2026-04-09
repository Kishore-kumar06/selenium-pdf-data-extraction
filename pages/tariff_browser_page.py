from src.selenium_operations.base_page import BrowserActions
from utils.logfiles import setup_logger
from dotenv import load_dotenv
import os
from selenium.webdriver.common.by import By
import time

logger = setup_logger("tariff_list_page")
load_dotenv()

class TariffBrowserPage(BrowserActions):
    
    def process_tariff_browser(self):
        try:
            self.click_button(xpath=os.getenv("ACTUAL_TARIFF_PROGRAM_XPATH"))
            
            is_effective = self.find_last_value(table_xpath=os.getenv("TABLE_ROWS_XPATH")) 
            is_effective.click()
            time.sleep(2)   
            logger.info("Effective file found and clicked for the tariff program.  \n")
            
            self.switch_to_iframe(name=os.getenv("IFRAME_NAME"))
            self.switch_to_iframe(name=os.getenv("IFRAME_NAME"))

            self.click_button(xpath=os.getenv("DOWNLOAD_BUTTON_XPATH"))
            logger.info("Download button clicked successfully. Waiting for file to download. \n")
            time.sleep(5)  # Wait for the download to start

            self.click_button(xpath=os.getenv("CLOSE_PAGE"))
           
           
        except Exception as e:
            print(f"An error occurred while processing the tariff browser: {e}")
            logger.error(f"An error occurred while processing the tariff browser: {e}. \n")
    

    