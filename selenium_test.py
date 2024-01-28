from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from pathlib import PurePath

# Instantiate options
opts = Options()
# opts.add_argument(" — headless") # Uncomment if the headless version needed
opts.binary_location = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'

# Set the location of the webdriver
chrome_driver = PurePath('./Utilities', 'chromedriver.exe').joinpath()

# Instantiate a webdriver
driver = webdriver.Chrome(options=opts, executable_path=chrome_driver)

# Load the HTML page
driver.get('https://www.carnegiehall.org/calendar/2022/09/29/Carnegie-Halls-Opening-Night-Gala-The-Philadelphia-Orchestra-0700PM')

# Parse processed webpage with BeautifulSoup
soup = BeautifulSoup(driver.page_source)
print(soup.find(id="test").get_text())

