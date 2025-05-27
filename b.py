import re
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Setup headless Chrome
options = Options()
driver = webdriver.Chrome(options=options)

# Load the page
url = "https://www.amazon.in/Cadbury-Dairy-Milk-Silk-Chocolate/dp/B019Z82RVC?ref_=ast_sto_dp&th=1&psc=1"
driver.get(url)

# Get HTML content
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

# Find all <script> tags
scripts = soup.find_all("script")
# Search for JSON containing 'colorImages'
image_data_script = None
for script in scripts:
    if str(script) and "colorImages" in str(script):
        image_data_script = script.string
        break

hires_urls = []

if image_data_script:
    # Try extracting the JSON array of images
    matches = re.findall(r'^.*colorImages.*$', image_data_script, re.MULTILINE)
    if matches:
        json_str = matches[0]
        # Clean the JSON string
        json_str = json_str.replace("'", '"')
        # Extract all hiRes image links
        hires_links = re.findall(r'"hiRes"\s*:\s*"([^"]+)"', json_str)
        print(hires_links)

if hires_urls:
    for i, url in enumerate(hires_urls, 1):
        print(f"[{i}] High-Res Image: {url}")
else:
    print("❌ Could not find high-res image URLs.")

driver.quit()
