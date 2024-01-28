from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from pathlib import PurePath

UNDETECTED = True

class SeleniumLoader():
    def __init__(self):

        if UNDETECTED:
            import undetected_chromedriver as uc
            self.driver = uc.Chrome(headless=False, use_subprocess=False)
        else:
            # Chrome driver options
            opts = Options()
    #        opts.add_argument(' — headless')
            opts.binary_location = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
            opts.binary_location = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'


            # Create the chrome driver
            chrome_driver = PurePath('Utilities', 'chromedriver.exe').joinpath()
            self.driver = webdriver.Chrome(options=opts, executable_path=str(chrome_driver))

    def close(self):
        self.driver.quit()

    def soup_from_url(self, url: str):
        """
        Return the soup from the URL
        :param url: URL to read
        :return: soup
        """
        self.driver.get(url)
        if UNDETECTED and False:
            self.driver.save_screenshot(r"c:/temp/selenium_screenshot.png")
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        return soup
