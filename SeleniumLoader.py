from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from pathlib import PurePath


class SeleniumLoader():
    def __init__(self):

        # Chrome driver options
        opts = Options()
#        opts.add_argument(' — headless')
        opts.binary_location = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'

        # Create the chrome driver
        chrome_driver = PurePath('Utilities', 'chromedriver.exe').joinpath()
        self.driver = webdriver.Chrome(options=opts, executable_path=chrome_driver)

    def soup_from_url(self, url: str):
        """
        Return the soup from the URL
        :param url: URL to read
        :return: soup
        """
        self.driver.get(url)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        return soup
