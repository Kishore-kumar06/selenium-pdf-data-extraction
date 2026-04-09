from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logfiles import setup_logger

logger = setup_logger("tariff_list_page")

class BrowserActions:
    def __init__(self, driver, timeout=30):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, timeout)

    # Select dropdown value by visible text
    def select_dropdown(self, program_name, xpath):
        try:
            dropdown = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )

            select = Select(dropdown)
            select.select_by_visible_text(program_name)
        except TimeoutException:
            print(f"Dropdown {program_name} not visible within timeout.")
            logger.error(f"Dropdown {program_name} not visible within timeout. \n")
        except NoSuchElementException:
            print(f"Option {program_name} not found in dropdown.")
            logger.error(f"Option {program_name} not found in dropdown. \n")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}. \n")

    # This function locates the company name input field using the provided XPath, clears any existing text, and enters the specified company name.
    def enter_text(self, text, xpath):
        try:
            company_input = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )

            company_input.clear()
            company_input.send_keys(text) # Enter the company name in the input field
            return text
        except TimeoutException:
            print(f"Input field {text} not visible within timeout.")
            logger.error(f"Input field {text} not visible within timeout. \n")
        except NoSuchElementException:
            print(f"Text '{text}' not found in input field.")
            logger.error(f"Text '{text}' not found in input field. \n")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}. \n")


    # Button click function to click the dynamic buttons in website y specifying dynamic xpath as parameter. It waits for the button to be clickable and then clicks it.
    def click_button(self, xpath):
        try:
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            ).click()
            
        except TimeoutException:
            print("Button not clickable within timeout.")
            logger.error("Button not clickable within timeout. \n")
        except NoSuchElementException:
            print(f"Button not found.")
            logger.error(f"Button not found. \n")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}. \n")


    # This function checks for presence of tariff title in the results page. If it is present, it returns the tariff title text. If not, it checks for the presence of a "no files" message and returns that text if found.
    def get_oil_tariff_program_from_results(self, xpath, no_files_xpath): 
        try:
            tariff_program_text = ""

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
                return tariff_program_text
            except TimeoutException:
                print("Option not visible within timeout.")
                logger.error("Option not visible within timeout. \n")
            except NoSuchElementException:
                print(f"Option not found.")
                logger.error(f"Option not found. \n")
            except Exception as e:
                print(f"Unexpected error: {e}")
                logger.error(f"Unexpected error: {e}. \n")


    def check_visibility_of_element(self, xpath):
        try:
            value = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            return value.text.strip()
        except TimeoutException:
            print("Element not visible within timeout.")
            logger.error("Element not visible within timeout. \n")
            return False
        except NoSuchElementException:
            print(f"Element with XPath '{xpath}' not found.")
            logger.error(f"Element with XPath '{xpath}' not found. \n")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}. \n")
            return False


        # This function gets the company name from the results page using the provided XPath. It waits for the element to be present, retrieves its text, and returns it.
    def get_company_name_from_results(self, xpath):
        try:
            company_name_element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            company_name_text = company_name_element.text.strip()
            return company_name_text
        except TimeoutException:
                print("Option not visible within timeout.")
                logger.error("Option not visible within timeout. \n")
        except NoSuchElementException:
            print(f"Option '{company_name_text}' not found.")
            logger.error(f"Option '{company_name_text}' not found. \n")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}. \n")


    def find_last_value(self, table_xpath):
        try:
            table = self.wait.until(
                EC.presence_of_element_located((By.XPATH, table_xpath))
            )

            rows = table.find_elements(By.TAG_NAME, "tr")
            if len(rows) > 1:
                last_row = rows[-1]
                cells = last_row.find_elements(By.TAG_NAME, "td")
                logger.info(f"Last row values: {[cell.text.strip() for cell in cells]}")
                effective_button = cells[3].find_element(By.TAG_NAME, "a")
                return effective_button
            else:
                logger.info("No records found in table. \n")
                print("No records found in the table.")
                return None
        except TimeoutException:
            print("Option not visible within timeout.")
            logger.error("Option not visible within timeout. \n")
        except NoSuchElementException:
            print(f"Option '{effective_button.text}' not found.")
            logger.error(f"Option '{effective_button.text}' not found. \n")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}. \n")

        
        # This function checks for presence of iframe using the provided XPath and switches to it if found. It includes error handling to catch any exceptions that may occur during the process, such as NoSuchElementException or TimeoutException, and prints appropriate error messages.
    def switch_to_iframe(self, name):
        try:
            self.wait.until(
                EC.frame_to_be_available_and_switch_to_it(name)
            )
        except TimeoutException:
            print("Option not visible within timeout.")
            logger.error("Option not visible within timeout. \n")
        except NoSuchElementException:
            print(f"Iframe not found.")
            logger.error(f"Iframe not found. \n")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}. \n")

    
    def switch_to_default_content(self):
        try:
            self.driver.switch_to.default_content()
            
        except WebDriverException as e:
            print(f"Error switching to default content: {e}")
            logger.error(f"Error switching to default content: {e}. \n")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}. \n")
