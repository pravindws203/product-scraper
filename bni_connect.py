"""
HyugalifeNow Web Scraper - Complete Version
Author: Pravin Prajapati
This script scrapes product data from HyugalifeNow website including:
1. AJAX API data (primary source)
2. Product page details (secondary source)
pip install blinker==1.9

"""

import time
import json
import re
import csv
import os
import random
import cloudscraper
import gzip
import logging
import io
from typing import Any, Dict, List, Optional, Literal
from tqdm import tqdm
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
  WebDriverException,
  TimeoutException,
  NoSuchElementException,
  StaleElementReferenceException
)
from selenium import webdriver

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(levelname)s - %(message)s',
  handlers=[
    logging.FileHandler('logs/bniconnect_scraper.log'),
  ]
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://bniconnect.com"
API_DOMAIN = "api.bniconnectnow.com"
USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
]
MAX_SCROLL_RETRIES = 15
SCROLL_PAUSE_TIME = 4
MAX_RETRIES = 3
PAGE_LOAD_TIMEOUT = 20


def get_random_user_agent() -> str:
  """Return a random user agent from predefined list."""
  return random.choice(USER_AGENTS)


def init_driver() -> webdriver.Chrome:
  """Initialize and return a Chrome WebDriver with configured options."""
  options = webdriver.ChromeOptions()
  # options.add_argument('--headless')
  options.add_argument('--no-sandbox')
  options.add_argument('--disable-dev-shm-usage')
  options.add_argument(f'user-agent={get_random_user_agent()}')
  options.add_argument('--disable-blink-features=AutomationControlled')
  options.add_argument('--window-size=1920,1080')
  
  driver = webdriver.Chrome(options=options)
  driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
  return driver


def safe_get(driver: webdriver.Chrome, url: str) -> bool:
  """Safely navigate to URL with retries and proper waiting."""
  for attempt in range(MAX_RETRIES):
    try:
      logger.info(f"Attempt {attempt + 1} to load {url}")
      driver.get(url)
      time.sleep(2)
      # Fill in the username and password
      username_input = driver.find_element(By.NAME, "username")
      password_input = driver.find_element(By.NAME, "password")
      
      username_input.send_keys("bhargavi@dolphinwebsolution.com")
      time.sleep(2)

      password_input.send_keys("Ness@1940")
      time.sleep(2)
      
      # Submit the form
      password_input.send_keys(Keys.RETURN)
      return True
    
    except TimeoutException:
      logger.warning(f"Page elements not found after loading {url}")
    except WebDriverException as e:
      logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
    
    if attempt == MAX_RETRIES - 1:
      logger.error(f"Failed to load {url} after {MAX_RETRIES} attempts")
      return False
    time.sleep(SCROLL_PAUSE_TIME * (attempt + 1))
  return False

def save_to_csv(data: List[Dict[str, Any]], filename: str) -> None:
  """Save data to CSV file with error handling."""
  if not data:
    return
  try:
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as f:
      writer = csv.DictWriter(f, fieldnames=data[0].keys())
      print()
      if not file_exists:
        writer.writeheader()
      writer.writerows(data)
    logger.info(f"Saved {len(data)} items to {filename}")
  except Exception as e:
    logger.error(f"Failed to save CSV: {e}")


def advanced_search(driver: webdriver.Chrome):
  """Perform an advanced search and return the updated driver after submission."""
  wait = WebDriverWait(driver, 10)
  
  # Click the "Advanced Search" link
  advanced_search_link = wait.until(EC.element_to_be_clickable((By.ID, "advancedSearch")))
  advanced_search_link.click()
  
  # Select Singapore (value="7585")
  wait.until(EC.presence_of_element_located((By.ID, "memberIdCountry")))
  country_dropdown = Select(driver.find_element(By.ID, "memberIdCountry"))
  country_dropdown.select_by_value("7585")
  
  # Select "Computer & Programming" (value="62")
  wait.until(EC.presence_of_element_located((By.ID, "memberPrimaryCategory")))
  category_dropdown = Select(driver.find_element(By.ID, "memberPrimaryCategory"))
  category_dropdown.select_by_value("62")
  
  # Wait for secondary category dropdown to populate before selecting "IT Consultants" (value="620975")
  wait.until(EC.presence_of_element_located((By.ID, "memberSecondaryCategory")))
  subcategory_dropdown = Select(driver.find_element(By.ID, "memberSecondaryCategory"))
  subcategory_dropdown.select_by_value("620975")
  
  # Wait for loading icon to disappear
  wait.until(EC.invisibility_of_element_located((By.ID, "loading")))
  
  # Click the "Search Members" button
  search_button = wait.until(EC.element_to_be_clickable((By.ID, "searchConnections")))
  search_button.click()


def extract_member_page(driver: webdriver.Chrome, url):
  # We still navigate using passed driver to be consistent
  driver.get(url)
  time.sleep(5)
  soup = BeautifulSoup(driver.page_source, 'html.parser')
  
  container = soup.find('div', class_='MuiBox-root css-1jklqt5')
  personal_details = {}
  
  if container:
    # Phone
    phone_tags = container.find_all("svg", {"aria-label": "Phone"})
    for phone_tag in phone_tags:
      number = phone_tag.find_next("p").text.strip()
      personal_details['phone'] = number
    
    # Mobile
    mobile_tags = container.find_all("svg", {"aria-label": "Mobile Number"})
    for mobile_tag in mobile_tags:
      number = mobile_tag.find_next("p").text.strip()
      personal_details['mobile'] = number
    
    # Email
    email_tags = container.find_all("svg", {"aria-label": "Email"})
    for email_tag in email_tags:
      email = email_tag.find_next("a").text.strip()
      personal_details['email'] = email
    
    # Website
    website_tags = container.find_all("svg", {"aria-label": "Website"})
    for website_tag in website_tags:
      website = website_tag.find_next("a")["href"]
      personal_details['website'] = website
    
    # LinkedIn Links
    a_tags = container.find_all('a', href=True)
    linkedin_links = [a['href'] for a in a_tags if 'linkedin.com' in a['href']]
    personal_details['linkedin_links'] = ', '.join(linkedin_links)
  
  return personal_details

def update_csv_with_product_data(driver: webdriver.Chrome, csv_path: str) -> None:
  """Update CSV file with product page data."""
  try:
    df = pd.read_csv(csv_path)
    
    # Ensure required columns exist
    required_fields = ['phone', 'mobile', 'email', 'website', 'linkedin_links']
    for field in required_fields:
      if field not in df.columns:
        df[field] = ""
    
    processed_count = 0
    total_rows = len(df)
    
    with tqdm(total=total_rows, initial=processed_count,
              desc="Processing API Products", unit="product") as pbar:
      for i in range(processed_count, total_rows):
        url = df.at[i, 'url'] if 'url' in df.columns else None
        if pd.notna(url):
          data = extract_member_page(driver, url)
          if data:
            for field in required_fields:
              df.at[i, field] = data.get(field, "")
        
        df.to_csv(csv_path, index=False)
        pbar.update(1)
  
  except Exception as e:
    logger.error(f"[✖] Error processing file: {str(e)}")
    raise


def extract_member_info(driver):
  time.sleep(3)
  wait = WebDriverWait(driver, 10)
  soup = BeautifulSoup(driver.page_source, 'html.parser')
  table_body = soup.find("tbody", {"id": "tableBody"})
  rows = table_body.find_all("tr") if table_body else []
  member_data = []
  for row in rows:
    try:
      cols = row.find_all("td")
      if len(cols) < 6:
        continue  # Skip malformed rows
      
      name_element = cols[0].find("a")
      name = name_element.get_text(strip=True)
      url = name_element.get("href")
      
      company = cols[1].get_text(strip=True)
      role = cols[2].get_text(strip=True)
      location = cols[3].get_text(strip=True)
      category = cols[4].get_text(strip=True)
      
      member_info = {
        "name": name,
        "url": f"https://www.bniconnectglobal.com/web/secure/{url}",
        "company": company,
        "chapter": role,
        "city": location,
        "classification": category
      }
      member_data.append(member_info)
    
    except Exception as e:
      logger.error(f"Error extracting data from row: {e}")
      continue
  
  logger.info(f"Extracted {len(member_data)} members")
  return member_data

def scrape_bni_connect(url: str, filename: str) -> None:
  """Main function to scrape a Hyugalife category."""
  driver = None
  try:
    driver = init_driver()
    logger.info(f"Starting scraping for URL: {url}")
    print(f"Starting scraping for URL: {url}")
    
    if not safe_get(driver, url):
      logger.error("Failed to load category page")
      return
    
    advanced_search(driver)
    
    while True:
      try:
        update_csv_with_product_data(driver, filename)
        break
      
      except (NoSuchElementException, StaleElementReferenceException) as e:
        print(f"Error occurred: {e}. Stopping pagination.")
        break
      
    logger.info(f"Completed scraping. Saved {None} products")
  
  except KeyboardInterrupt:
    logger.info("\nScraping stopped by user")
  except Exception as e:
    logger.error(f"Critical error: {e}", exc_info=True)
  finally:
    if driver:
      driver.quit()


if __name__ == "__main__":
  # category_url = input("Enter BNI Connect - Local Business - Global Network URL: ").strip()
  # filename = input("Enter CSV filename: ").strip()
  category_url = "https://www.bniconnectglobal.com/web/secure/networkAddConnections"
  filename = "networkAddConnections"
  scrape_bni_connect(category_url, f"{filename}.csv")