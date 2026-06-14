from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException, NoSuchFrameException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logfiles import setup_logger
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = setup_logger("base_page")

# setting browser actions and operations
class BrowserActions:
    def __init__(self, driver, timeout=30):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, timeout)

    # Select dropdown value by visible text
    def select_dropdown(self, tariff_program, xpath):
        try:

            dropdown = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )

            select = Select(dropdown)
            if tariff_program != "Oil":
                error_message = (f"Invalid program name '{tariff_program}'. Only 'Oil' is supported.")

                logger.error(error_message)
                raise ValueError(error_message)
                
            select.select_by_visible_text(tariff_program)

            logger.info(f"Successfully selected {tariff_program} from the dropdown")

        except TimeoutException:
            logger.error(f"Dropdown element for {tariff_program} is not visible within the time.")
            raise

        except NoSuchElementException:
            logger.error(f"Dropdown element for {tariff_program} is not found in page.")
            raise
        
        except ValueError:
            raise

        except Exception as e:
            logger.exception(f"Unexpected error while locating dropdown: {e}.")
            raise


    # This function locates the company name input field using the provided XPath, clears any existing text, and enters the specified company name.
    def enter_text(self, text, xpath):
        try:
            company_input = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )

            company_input.clear()
            company_input.send_keys(text) # Enter the company name in the input field

            logger.info(f"Successfully entered pipeline name {text}.")

            return text

        except TimeoutException:
            logger.error(f"Text Field element for {text} is not visible within the time.")
            raise

        except NoSuchElementException:
            logger.error(f"Text Field element for {text} is not found in page.")
            raise

        except Exception as e:
            logger.exception(f"Unexpected error while locating textbox: {e}.")
            raise


    # Button click function to click the dynamic buttons in website y specifying dynamic xpath as parameter. It waits for the button to be clickable and then clicks it.
    def click_button(self, xpath):
        try:
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            ).click()
            
        except TimeoutException:
            logger.error(f"Buttom element is not visible within the time.")
            raise

        except NoSuchElementException:
            logger.error(f"Buttom element is not found in page.")
            raise

        except Exception as e:
            logger.exception(f"Unexpected error while locating button: {e}.")
            raise


    # This function checks for presence of tariff title in the results page. If it is present, it returns the tariff title text. If not, it checks for the presence of a "no files" message and returns that text if found.
    def get_oil_tariff_program_from_results(self, xpath, no_files_xpath): 
        try:
            tariff_program_element = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            tariff_program_text = tariff_program_element.text.strip()
            
            return tariff_program_element, tariff_program_text
        
        except:
            try:
                message_element = self.wait.until(
                    EC.visibility_of_element_located((By.XPATH,  no_files_xpath))
                )
                tariff_program_text = message_element.text.strip()
                
                return None, tariff_program_text
            
            except TimeoutException:
                logger.error(f"Tariff link element is not visible within the time.")
                return None, None

            except NoSuchElementException:
                logger.error(f"Tariff link element is not found in page.")
                return None, None

            except Exception as e:
                logger.exception(f"Unexpected error while locating link: {e}.")
                return None, None


    # function to check expect value/text is available in the page
    def get_visible_value(self, xpath):
        try:
            value = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            if value:
                return value.text.strip()
        except TimeoutException:
            logger.error(f"Expected value/text element is not visible within the time.")
            raise

        except NoSuchElementException:
            logger.error(f"Expected value/text element is not found in page.")
            raise

        except Exception as e:
            logger.exception(f"Unexpected error while locating visible value/text: {e}.")
            raise


    def find_last_value(self, table_xpath):
        try:
            table = self.wait.until(
                EC.presence_of_element_located((By.XPATH, table_xpath))
            )

            rows = table.find_elements(By.TAG_NAME, "tr")

            if len(rows) <= 1:
                logger.error("No records found in table.")
                return None
            
            for row in reversed(rows[1:]):

                cells = row.find_elements(By.TAG_NAME, "td")

                if len(cells) < 4:
                    continue

                effective_button = cells[3].find_element(By.TAG_NAME, "a")

                status = (effective_button.text.strip())

                if status == "Effective":
                    logger.info("Effective pipeline record found.")
                    
                    return effective_button
            
        except TimeoutException:
            logger.error(f"Effective text element is not visible within the time.")
            return None

        except NoSuchElementException:
            logger.error(f"Effective text element is not found in page.")
            return None

        except Exception as e:
            logger.exception(f"Unexpected error while locating text: {e}.")
            return None
        

    # This function checks for presence of iframe using the provided XPath and switches to it if found. It includes error handling to catch any exceptions that may occur during the process, such as NoSuchElementException or TimeoutException, and prints appropriate error messages.
    def switch_to_iframe(self, name):
        try:
            self.wait.until(
                EC.frame_to_be_available_and_switch_to_it(name)
            )
        except TimeoutException:
            logger.error(f"iframe is not visible within the time.")
            return None

        except NoSuchFrameException:
            logger.error(f"iframe is not found in page.")
            return None

        except Exception as e:
            logger.exception(f"Unexpected error while switching to iframe: {e}.")
            return None
    

    def switch_to_default_content(self):
        try:
            self.driver.switch_to.default_content()
            
        except TimeoutException:
            logger.error(f"parent frame is not visible within the time.")
            return None

        except Exception as e:
            logger.exception(f"Unexpected error while switching to parent frame: {e}.")
            return None

    
    def save_failed_scheenshots(self, file):
        try:
            if self.driver:
                
                screenshot_path = os.getenv("FAILED_SCREENSHOTS_PATH")

                if not screenshot_path:
                    logger.error("FAILED_SCREENSHOTS_PATH not found in .env")
                    return
                
                os.makedirs(screenshot_path, exist_ok=True)
                
                # # screenshot_file = f"{screenshot_path}_{file}.png"
                # # full_path = os.path.join(screenshot_path, screenshot_file)

                timestamp = (
                    datetime.now()
                    .strftime(
                        "%Y%m%d_%H%M%S"
                    )
                )

                screenshot_file = (
                    f"{file}_"
                    f"{timestamp}.png"
                )

                full_path = os.path.join(
                    screenshot_path,
                    screenshot_file
                )

                self.driver.save_screenshot(full_path)
                logger.info(f"Successfully saved failed screenshot. at {full_path}")

        except Exception as er:
            logger.exception(f"An error occured while saving failed screenshots {er}.")
