"""
Flipkart Web Scraper Module
Author: Pravin Prajapati
A modular scraper for Flipkart product data with:
- AJAX API data extraction
- Product page details scraping
"""

import os
import re
import time
import json
import random
import requests
import traceback
from logger_config import setup_logger
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
  WebDriverException,
  TimeoutException,
  NoSuchElementException
)
from seleniumwire import webdriver
from tqdm import tqdm


class Flipkart:
  def __init__(self, headless: bool = True):
    """
    Initialize the Flipkart scraper

    Args:
        headless (bool): Run browser in headless mode
    """
    self._setup_logging()
    self.headless = headless
    self.driver = None
    self._configure_constants()
  
  def _configure_constants(self):
    """Initialize scraper constants"""
    self.BASE_URL = "https://www.flipkart.com"
    self.USER_AGENTS = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edge/114.0.1823.67',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 OPR/90.0.4480.80',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_2) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0.3 Safari/537.36',
      'Mozilla/5.0 (Linux; Android 11; Pixel 4 XL Build/RQ3A.210805.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; AS; Desktop) like Gecko',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Brave/1.43.88',
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Vivaldi/5.8.2945.60'
    ]
    self.MAX_SCROLL_RETRIES = 15
    self.SCROLL_PAUSE_TIME = 4
    self.MAX_RETRIES = 3
    self.PAGE_LOAD_TIMEOUT = 20
    self.REQUEST_TIMEOUT = 30
  
  def _setup_logging(self):
    """Configure logging settings"""
    self.logger = setup_logger("FLIPKART", "flipkart_scraper.log")
  
  def _get_random_user_agent(self) -> str:
    """Return a random user agent from predefined list."""
    return random.choice(self.USER_AGENTS)
  
  def init_driver(self) -> webdriver.Chrome | None:
    """Initialize and return a Chrome WebDriver with configured options, or None on failure."""
    try:
        options = webdriver.ChromeOptions()

        if self.headless:
            options.add_argument('--headless')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={self._get_random_user_agent()}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(self.PAGE_LOAD_TIMEOUT)

        self.driver = driver  # Store in instance variable
        return driver
    except WebDriverException as e:
        self.logger.error(f"Driver initialization failed: {e}")
        self.logger.debug(traceback.format_exc())
        return None
  
  def _safe_get(self, url: str) -> bool:
    """Safely navigate to URL with retries and proper waiting."""
    for attempt in range(self.MAX_RETRIES):
      try:
        self.logger.info(f"Attempt {attempt + 1} to load {url}")
        self.driver.get(url)
        return True
      except TimeoutException:
        self.logger.warning(f"Timeout loading {url}")
      except WebDriverException as e:
        self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
      
      if attempt == self.MAX_RETRIES - 1:
        self.logger.error(f"Failed to load {url} after {self.MAX_RETRIES} attempts")
        return False
      time.sleep(self.SCROLL_PAUSE_TIME * (attempt + 1))
    return False
  
  @staticmethod
  def _clean_text(text: str) -> str:
    """Clean text by removing special characters and extra whitespace"""
    if not text:
      return ""
    return re.sub(r'[\u200e\u200f]', '', text).strip()
  
  def _extract_product_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract product details from the product page"""
    general_data = {}
    
    general_section = soup.find('div', class_='_4BJ2V+', string='General')
    if general_section:
      general_table = general_section.find_next('table')
      
      for row in general_table.find_all('tr', class_='WJdYP6'):
        cols = row.find_all('td')
        if len(cols) == 2:
          key = cols[0].get_text(strip=True).lower()
          value = cols[1].get_text(strip=True)
          general_data[key] = value
    
    return general_data
  
  def get_technical_details(self, soup: BeautifulSoup) -> Dict[str, str]:
    """Extract technical details from the product page"""
    
    details = {}
    try:
      rows = soup.select('#productDetails_techSpec_section_1 tr')
      for row in rows:
        key_el = row.find('th')
        value_el = row.find('td')
        if key_el and value_el:
          key = self._clean_text(key_el.get_text())
          value = self._clean_text(value_el.get_text())
          details[key.lower()] = value
      return details
    except Exception as e:
      self.logger.error(f"Error extracting technical details: {e}")
      return details
  
  def get_additional_information(self, soup: BeautifulSoup) -> Dict[str, str]:
    """Extract additional information from the product page"""
    details = {}
    try:
      additional_info = soup.select('#productDetails_detailBullets_sections1 tr')
      for row in additional_info:
        key_el = row.find('th')
        value_el = row.find('td')
        if key_el and value_el:
          key = self._clean_text(key_el.get_text())
          value = self._clean_text(value_el.get_text())
          details[key.lower()] = value
      return details
    except Exception as e:
      self.logger.error(f"Error extracting technical details: {e}")
      return details
  
  def _get_images(self, soup: BeautifulSoup) -> List[str]:
    """
    Extract product image URLs from Flipkart product page soup.
    First tries JavaScript 'colorImages' block, then falls back to direct HTML.
    """
    image_urls = []
    try:
      ul = soup.find("ul", class_="ZqtVYK")
      urls = [img['src'] for img in ul.find_all('img') if img.get('src')]
      for url in urls:
        cleaned_url = url.replace("/128/128", "")
        image_urls.append(cleaned_url)
    except Exception as e:
      self.logger.error(f"Error extracting images from JS: {e}")
    
    return list(set(image_urls))
  
  def get_mass_measurement_unit(self, unit: str):
    """
    Extracts and standardizes the mass or volume measurement unit from a string
    by removing numeric parts and mapping common variations to standard forms.
    """
    if not unit:
      return None
    
    # Remove numeric parts (integers and decimals)
    cleaned_unit = re.sub(r'\d+(\.\d+)?', '', str(unit)).strip().lower()
    
    # Define mappings from variations to standard units
    unit_mappings = {
      'grams': ['gram', 'grams', 'kilogram', 'kilograms', 'kg', 'g'],
      'millilitre': ['ml', 'millilitre', 'millilitres', 'milliliter', 'milliliters', 'liter', 'litre', 'liters',
                     'litres',
                     'l']
    }
    
    for standard_unit, variations in unit_mappings.items():
      if any(var in cleaned_unit for var in variations):
        return standard_unit.upper()
    
    return None
  
  def get_diet(self, diet: str):
    if not diet:
      return None
    diet = diet.lower()
    if diet == 'vegan':
      return "Vegan"
    elif diet == 'non veg':
      return 'Non Veg'
    elif diet in ('vegetarian', 'veg', 'natural'):
      return 'Veg'
    else:
      return None
  
  def extract_image_urls_text(self, image_urls) -> str:
    """
    Extracts image URLs from the tuple (starting from index 22),
    filters only valid URLs (starts with http),
    and returns them as a JSON string in the format:
    { "image_urls": [ ... ] }
    """
    # image_urls = [url for url in image_url[22:] if isinstance(url, str) and url.startswith("http")]
    if not image_urls:
      return ""
    return json.dumps({"image_urls": image_urls}, indent=2)
  
  def _load_all_products(self) -> None:
    """Load all products on the page by scrolling and clicking 'Load More'"""
    time.sleep(self.SCROLL_PAUSE_TIME + random.random())
    last_height = self.driver.execute_script("return document.body.scrollHeight")
    footer_height = self.driver.execute_script("""
                    const footer = document.querySelector('footer');
                    return footer ? footer.offsetHeight : 0;
                    """)
    retries = 0
    
    while retries < self.MAX_SCROLL_RETRIES:
      try:
        wait = WebDriverWait(self.driver, 10)
        self.driver.execute_script(
          f"window.scrollTo(0, {last_height - footer_height - random.randint(600, 700)});")
        time.sleep(self.SCROLL_PAUSE_TIME + random.random())
        new_height = self.driver.execute_script("return document.body.scrollHeight")
        
        button = wait.until(EC.element_to_be_clickable(
          (By.CSS_SELECTOR, "button.Button__secondary__sMAVa")))
        button.click()
        
        if new_height == last_height:
          retries += 1
        else:
          last_height = new_height
          retries = 0
      
      except Exception as e:
        self.logger.error(f"Error during scrolling: {e}")
        break
  
  def click_next_button(self) -> bool:
    """
    Clicks the 'Next' button on pagination until it becomes disabled.
    """
    try:
      if self.driver.find_elements(By.CSS_SELECTOR, 'span.s-pagination-item.s-pagination-next.s-pagination-disabled'):
        self.logger.warning("Reached last page. Stopping.")
        return False
      
      next_btn = self.driver.find_element(By.CSS_SELECTOR, 'a.s-pagination-item.s-pagination-next')
      self.logger.info("Clicking Next...")
      next_btn.click()
      return True
    
    except NoSuchElementException:
      self.logger.error("No Next button found. Exiting.")
      return False
  
  def get_product_urls(self, url: str) -> List[str]:
    """Scrape product URLs from an Flipkart category page."""
    if not self._safe_get(url):
      return []
    
    self._load_all_products()
    product_urls = set()
    
    while True:
      try:
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        divs = soup.find_all('div', class_ = "DOjaWF gdgoEp" )
        for a_tag in divs[0].find_all("a", class_="VJA3rP"):
          href = a_tag.get("href")
          if href:
            full_url = self.BASE_URL + href
            product_urls.add(full_url)
          
        self.logger.info(f"Collected {len(product_urls)} unique product URLs so far.")
        print(product_urls)
        if not self.click_next_button():
          break
        
        time.sleep(self.SCROLL_PAUSE_TIME + random.random())
      
      except Exception as e:
        self.logger.error(f"Error while extracting product URLs: {e}")
        break
    
    self.logger.info(f"Total product URLs collected: {len(product_urls)}")
    return list(product_urls)
  
  def get_product_details(self, url: str) -> Dict[str, Any]:
    """Extract detailed product information from product page"""
    for attempt in range(self.MAX_RETRIES):
      try:
        if not self._safe_get(url):
          continue
        
        time.sleep(self.SCROLL_PAUSE_TIME + random.randint(3, 6))
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        details = self._extract_product_details(soup)
        images = self._get_images(soup)
        def safe_find(by, value):
          try:
            return self._clean_text(self.driver.find_element(by, value).text)
          except:
            return None
        
        product = {
          "variant_id": None,
          "name": safe_find(By.CLASS_NAME, 'VU-ZEz'),
          "product_url": url,
          "brand_name": details.get('brand'),
          "category": None,
          "sub_category": None,
          "diet": self.get_diet(details.get('food preference')),
          "allergen_information": details.get('allergen_information'),
          "mass_measurement_unit": self.get_mass_measurement_unit(details.get('net quantity')) or self.get_mass_measurement_unit(details.get('quantity')),
          "net_weight": details.get('net quantity') or details.get('quantity'),
          "mrp": safe_find(By.CLASS_NAME, 'Nx9bqj CxhGGd') or safe_find(By.CLASS_NAME, 'Nx9bqj'),
          "ingredients_main_ocr": None,
          "nutrients_main_ocr": None,
          "images": self.extract_image_urls_text(images),
          "front_img": None,
          "back_img": None,
          "nutrients_img": None,
          "ingredients_img": None,
          "source": "Flipkart",
          "status": "raw",
        }
        print(product)
        return product
      
      except Exception as e:
        self.logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
        if attempt == self.MAX_RETRIES - 1:
          return {}
        time.sleep(self.SCROLL_PAUSE_TIME * (attempt + 1))
    
    return {}
  
  def scrape_category(self, category_url: str) -> None:
    """Main method to scrape an Flipkart category"""
    try:
      if not self.init_driver():
        raise WebDriverException("Failed to initialize WebDriver")
      
      self.logger.info(f"Starting scraping for URL: {category_url}")
      print(f"Starting scraping for URL: {category_url}")
      product_urls = self.get_product_urls(category_url)
      # product_urls = ["https://www.flipkart.com/indie-flavors-flipkart-khatta-meetha/p/itmec0440ae12fa1?pid=SNSHFS4BHXSBK2G7&lid=LSTSNSHFS4BHXSBK2G7FX1L0C&marketplace=FLIPKART&store=eat%2F0we&srno=b_1_1&otracker=product_breadCrumbs_Indie%20Flavors%20by%20Flipkart%20Namkeen&fm=organic&iid=891f3172-d51b-4fba-afd2-7c795e5aff53.SNSHFS4BHXSBK2G7.SEARCH&ppt=browse&ppn=browse&ssid=82m32i63740000001748006109202"]
      if not product_urls:
        self.logger.error("No product URLs found")
        return
      self.logger.info(f"Found {len(product_urls)} product URLs to scrape")
      print(f"Found {len(product_urls)} product URLs to scrape")
      
      # Create a progress bar
      pbar = tqdm(total=len(product_urls), initial=0, desc="Flipkart Scrapped Products", unit="products",
                  dynamic_ncols=True)
      
      for i, url in enumerate(product_urls, 1):
        product_data = self.get_product_details(url)
        if product_data:
          # print(f"Scraped product {i}/{len(product_urls)}: {product_data}")
          url = "http://10.0.101.153:10000/insert"
          response = requests.post(url, json=product_data)
          if response.status_code == 200:
            self.logger.info(f"Inserted product with ID: {response.json().get('id')}")
          else:
            self.logger.error(f"Failed to insert product data: {response.status_code}")

          data = response.json()
          pbar.set_postfix({"Inserted product with ID": data.get('id', None)})
        else:
          self.logger.error(f"Failed to scrape product {i}/{url}")
        
        time.sleep(random.randint(2, 5))
        pbar.update(1)
      
      self.logger.info(f"Completed scraping. Results saved in DATABASE")
    
    except KeyboardInterrupt:
      self.logger.info("\nScraping stopped by user")
    except Exception as e:
      self.logger.error(f"Critical error: {e}", exc_info=True)
    finally:
      if self.driver:
        self.driver.quit()
  
  def scrape_product(self, product_url: str) -> None:
    """Main method to scrape an Amazon category"""
    try:
      if not self.init_driver():
        raise WebDriverException("Failed to initialize WebDriver")
      
      if not product_url:
        self.logger.error("No product URLs found")
        return
      
      product_data = self.get_product_details(product_url)
      if product_data:
        # print(f"Scraped product {i}/{len(product_urls)}: {product_data}")
        url = "http://10.0.101.153:10000/insert"
        response = requests.post(url, json=product_data)
        if response.status_code == 200:
          self.logger.info(f"Inserted product with ID: {response.json().get('id')}")
        else:
          self.logger.error(f"Failed to insert product data: {response.status_code}")
      
      else:
        self.logger.error(f"Failed to scrape product {product_url}")
        
        time.sleep(random.randint(2, 5))
      
      self.logger.info(f"Completed scraping. Results saved in DATABASE")
    
    except KeyboardInterrupt:
      self.logger.info("\nScraping stopped by user")
    except Exception as e:
      self.logger.error(f"Critical error: {e}", exc_info=True)
    finally:
      if self.driver:
        self.driver.quit()

if __name__ == "__main__":
  obj = Flipkart(headless=False)
  obj.scrape_category(
    category_url="https://www.flipkart.com/food-products/namkeen/indie-flavors-by-flipkart~brand/pr?sid=eat,0we&marketplace=FLIPKART&otracker=product_breadCrumbs_Indie+Flavors+by+Flipkart+Namkeen")
