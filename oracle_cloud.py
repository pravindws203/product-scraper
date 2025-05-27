from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# Step 1: Chrome options setup for automatic download
download_dir = "/path/to/your/download/folder"

USER_ID = "IND-PARTHP"
PASSWORD = "apparel123"

chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

# Step 2: Launch browser
driver = webdriver.Chrome(options=chrome_options)

# Step 3: Open website
driver.get("https://ediu.fa.em2.oraclecloud.com")
time.sleep(2)

user_input = driver.find_element(By.ID, "userid")
user_input.send_keys(USER_ID)
pass_input = driver.find_element(By.ID, "password")
pass_input.send_keys(PASSWORD)
time.sleep(4)
sign_in_button = driver.find_element(By.ID, "btnActive")
sign_in_button.click()

# Step 5: Wait for download to complete (can be improved with file check logic)
time.sleep(10)

driver.quit()
