from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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

            logger.info(f"Selected program: {program_name}")
            print(f"Selected program: {program_name}")

        except TimeoutException:
            print("Dropdown not visible within timeout.")
            logger.error("Dropdown not visible within timeout.")
        except NoSuchElementException:
            print(f"Option '{program_name}' not found in dropdown.")
            logger.error(f"Option '{program_name}' not found in dropdown.")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}")

    # This function locates the company name input field using the provided XPath, clears any existing text, and enters the specified company name.
    def enter_text(self, text, xpath):
        try:
            company_input = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )

            company_input.clear()
            company_input.send_keys(text) # Enter the company name in the input field

            logger.info(f"Entered text: {text}")
            print(f"Entered text: {text}")
            return text
        except TimeoutException:
            print("Input field not visible within timeout.")
            logger.error("Input field not visible within timeout.")
        except NoSuchElementException:
            print(f"Text '{text}' not found in input field.")
            logger.error(f"Text '{text}' not found in input field.")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}")


    # Button click function to click the dynamic buttons in website y specifying dynamic xpath as parameter. It waits for the button to be clickable and then clicks it.
    def click_button(self, xpath):
        try:
            find_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            find_button.click()

            print("Clicked button")
            logger.info(f"Clicked {find_button.get_attribute('value')} button")
        except TimeoutException:
            print("Button not clickable within timeout.")
            logger.error("Button not clickable within timeout.")
        except NoSuchElementException:
            print(f"Button '{find_button.get_attribute('value')}' not found.")
            logger.error(f"Button '{find_button.get_attribute('value')}' not found.")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}")


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
                logger.error("Option not visible within timeout.")
            except NoSuchElementException:
                print(f"Option '{tariff_program_text}' not found.")
                logger.error(f"Option '{tariff_program_text}' not found.")
            except Exception as e:
                print(f"Unexpected error: {e}")
                logger.error(f"Unexpected error: {e}")


    def check_visibility_of_element(self, xpath):
        try:
            value = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            return value.text.strip()
        except TimeoutException:
            print("Element not visible within timeout.")
            logger.error("Element not visible within timeout.")
            return False
        except NoSuchElementException:
            print(f"Element with XPath '{xpath}' not found.")
            logger.error(f"Element with XPath '{xpath}' not found.")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}")
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
                logger.error("Option not visible within timeout.")
        except NoSuchElementException:
            print(f"Option '{company_name_text}' not found.")
            logger.error(f"Option '{company_name_text}' not found.")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}")


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
                print("No records found in the table.")
                return None
        except TimeoutException:
            print("Option not visible within timeout.")
            logger.error("Option not visible within timeout.")
        except NoSuchElementException:
            print(f"Option '{effective_button.text}' not found.")
            logger.error(f"Option '{effective_button.text}' not found.")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}")

        
        # This function checks for presence of iframe using the provided XPath and switches to it if found. It includes error handling to catch any exceptions that may occur during the process, such as NoSuchElementException or TimeoutException, and prints appropriate error messages.
    def switch_to_iframe(self, name):
        try:
            self.wait.until(
                EC.frame_to_be_available_and_switch_to_it(name)
            )
            # self.driver.switch_to.frame(iframe_element)
            print("Switched to iframe")
        except TimeoutException:
            print("Option not visible within timeout.")
            logger.error("Option not visible within timeout.")
        except NoSuchElementException:
            print(f"Iframe not found.")
            logger.error(f"Iframe not found.")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}")

    
    def switch_to_default_content(self):
        try:
            self.driver.switch_to.default_content()
            print("Switched to default content")
        except WebDriverException as e:
            print(f"Error switching to default content: {e}")
            logger.error(f"Error switching to default content: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}")


# # This function finds the last record in the table and checks if the effective file option is present in the last record. If it is present, it clicks on the effective link. If not, it returns False.
# def find_last_record_in_table(driver, table_xpath):
#     try:
#         table = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.XPATH, table_xpath))
#         )
#         rows = table.find_elements(By.TAG_NAME, "tr")
#         if len(rows) > 1:
#             last_row = rows[-1]
#             cells = last_row.find_elements(By.TAG_NAME, "td")
#             # return [cell.text.strip() for cell in cells]
#             effective_button = cells[3].find_element(By.TAG_NAME, "a")
#             return effective_button
#         else:
#             print("No records found in the table.")
#             return None
#     except (Exception, NoSuchElementException, TimeoutException) as e:
#         print(f"Error finding last record in table: {e}")
#         return None

    

