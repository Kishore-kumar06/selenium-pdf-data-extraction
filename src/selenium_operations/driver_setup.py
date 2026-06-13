from selenium import webdriver
from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from utils.logfiles import setup_logger

logger = setup_logger("driver_setup")

# initializing the Selenium driver and driver components
class DriverSetup:
    def __init__(self, browser_name="chrome", headless=False):
        self.browser_name = browser_name.lower()
        self.headless = headless
        self.driver = None

    # Chrome Options
    def _chrome_options(self):
        options = ChromeOptions()

        prefs = {
            "profile.managed_default_content_settings.images": 2
        }

        options.add_experimental_option("prefs", prefs)

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")

        return options


    # creating browser instance
    def setup_browser(self):
        try:
            if self.browser_name == "chrome":
                logger.info("Setting up Chrome browser with options.")
                options = self._chrome_options()
                self.driver = webdriver.Chrome(options=options)

            elif self.browser_name == "firefox":
                logger.info("Setting up Firefox browser with options.")
                options = self._firefox_options()
                self.driver = webdriver.Firefox(options=options)

            elif self.browser_name == "edge":
                logger.info("Setting up Edge browser with options.")
                options = self._edge_options()
                self.driver = webdriver.Edge(options=options)
            
            else:
                logger.warning(f"Unsupported browser: {self.browser_name}.")
                raise ValueError(f"Unsupported browser: {self.browser_name}")

            self.driver.maximize_window()
            return self.driver

        except WebDriverException as e:
            logger.error(f"Error while initializing the browser: {e}.")
            return None

    # Open URL
    def open_url(self, url):
        try:
            if self.driver:
                logger.info(f"Opening URL: {url}.")
                self.driver.get(url)
                
                self.driver.set_page_load_timeout(30)
            else:
                logger.warning("Driver not initialized. Call setup_browser().")
        except TimeoutException as er:
            logger.error(f"Page load timeout: {er}")
            self.driver.refresh()


    # Quit browser (BEST practice)
    def quit_browser(self):
        if self.driver:
            logger.info("Quiting browser...")
            self.driver.quit()
            self.driver = None
        else:
            logger.warning("No active browser session.")


    # Close window
    def close_browser(self):
        if self.driver:
            logger.info("Closing Browser...")
            self.driver.close()
            self.driver = None
        else:
            logger.warning("No active current window.")


    # Navigate back
    def navigate_back(self):
        if self.driver:
            logger.info("Navigating to previous page...")
            self.driver.back()
        else:
            logger.warning("Driver not initialized.")

    
    def set_download_path(self, path):
        try:
            self.driver.execute_cdp_cmd(
                "Page.setDownloadBehavior",
                {
                    "behavior": "allow",
                    "downloadPath": path
                }
            )
        except Exception as er:
            logger.warning(f"File download path has not initialized properly. {path} - {er}.")

