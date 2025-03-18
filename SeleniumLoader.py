import logging

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)
# Import undetected_chromedriver only if you're planning to use it
try:
    import undetected_chromedriver as uc

    UNDETECTED_AVAILABLE = True
except ImportError:
    UNDETECTED_AVAILABLE = False


class SeleniumLoader:
    def __init__(self, undetected: bool = False):
        self.undetected = undetected
        if self.undetected and UNDETECTED_AVAILABLE:
            self.driver = uc.Chrome()  # uc manages driver itself
        else:
            # Setup Chrome options
            opts = Options()
            # opts.add_argument("--headless")  # Uncomment if headless is needed
            opts.add_argument(
                "--log-level=3"
            )  # Set log level to warning or higher severity

            # Initialize the Chrome Driver using webdriver-manager
            installer = ChromeDriverManager().install()
            service = Service(installer)
            self.driver = webdriver.Chrome(service=service, options=opts)

    def close(self):
        """Closes the Selenium WebDriver session."""
        self.driver.quit()

    def soup_from_url(self, url: str):
        """
        Loads a web page in the current browser session and returns its BeautifulSoup representation.

        :param url: URL to load.
        :return: BeautifulSoup object of the page source.
        """
        try:
            self.driver.get(url)
            # Screenshot for debugging (optional)
            if self.undetected:
                self.driver.save_screenshot(r"c:/temp/selenium_screenshot.png")
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
        except Exception as e:
            logger.info(f"Error loading {url}: {e}")
            soup = None

        return soup
