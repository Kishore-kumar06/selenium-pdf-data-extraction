from src.selenium_operations.base_page import BrowserActions
from utils.logfiles import setup_logger
from dotenv import load_dotenv
import os

logger = setup_logger("tariff_list_page")
load_dotenv()

class TariffListPage(BrowserActions):

    def __init__(self, driver, timeout=30, pipelinename=None):
        super().__init__(driver, timeout)
        self.pipeline_name = pipelinename

    def process_tariff_list(self):
        try:
            self.select_dropdown(program_name="Oil", xpath=os.getenv("TARIFF_PROGRAM_DROPDOWN_XPATH"))
            
            pipeline = self.enter_text(text=self.pipeline_name, xpath=os.getenv("COMPANY_NAME_INPUT_XPATH"))
            logger.info(f"Entered pipeline name: {pipeline} \n")
            print(f"Entered pipeline name: {pipeline}")
            
            self.click_button(xpath=os.getenv("SEARCH_BUTTON_XPATH"))
            
            company_name = self.get_company_name_from_results(xpath=os.getenv("COMPANY_NAME_RESULT_XPATH")) 

            tariff_option, tariff_text = self.get_oil_tariff_program_from_results(xpath=os.getenv("TARIFF_PROGRAM_RESULT_XPATH"), no_files_xpath=os.getenv("No_FILES_MESSAGE_XPATH"))
            
            return company_name, tariff_option, tariff_text
        except Exception as e:
            print(f"An error occurred while processing the tariff list: {e}")
            logger.error(f"An error occurred while processing the tariff list: {e}. \n")
    

    