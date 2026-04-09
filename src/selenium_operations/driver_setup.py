from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from utils.logfiles import setup_logger

logger = setup_logger("driver_setup")

class DriverSetup:
    def __init__(self, browser_name="chrome", download_folder=None, headless=False):
        self.browser_name = browser_name.lower()
        self.download_folder = download_folder
        self.headless = headless
        self.driver = None

    # Chrome Options
    def _chrome_options(self):
        options = ChromeOptions()

        prefs = {
            "download.default_directory": self.download_folder,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }

        options.add_experimental_option("prefs", prefs)

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")

        return options


    # Create browser instance
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
                raise ValueError(f"Unsupported browser: {self.browser_name}")

            self.driver.maximize_window()
            return self.driver

        except Exception as e:
            logger.error(f"Error opening the browser: {e}")
            return None

    # Open URL
    def open_url(self, url):
        if self.driver:
            logger.info(f"Opening URL: {url}")
            self.driver.get(url)
        else:
            logger.warning("Driver not initialized. Call setup_browser() first.")


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
    def back_browser(self):
        if self.driver:
            logger.info("Navigating back...")
            self.driver.back()
        else:
            logger.warning("Driver not initialized.")
