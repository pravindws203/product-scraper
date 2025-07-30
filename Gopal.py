"""
Gopal Web Scraper Module
Author: Pravin Prajapati
A modular scraper for Gopal product data with:
- AJAX API data extraction
- Product page details scraping
"""

import os
import re
import time
import json
import random
import requests
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


class Gopal:
  def __init__(self, headless: bool = True):
    """
    Initialize the Gopal scraper

    Args:
        headless (bool): Run browser in headless mode
    """
    self._setup_logging()
    self.headless = headless
    self.driver = None
    self._configure_constants()
  
  def _configure_constants(self):
    """Initialize scraper constants"""
    self.BASE_URL = "https://www.gopalnamkeen.com/"
    self.USER_AGENTS = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edge/114.0.1823.67',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; AS; Desktop) like Gecko',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Brave/1.43.88',
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Vivaldi/5.8.2945.60'
    ]
    self.MAX_SCROLL_RETRIES = 15
    self.SCROLL_PAUSE_TIME = 4
    self.MAX_RETRIES = 3
    self.PAGE_LOAD_TIMEOUT = 60
    self.REQUEST_TIMEOUT = 30
  
  def _setup_logging(self):
    """Configure logging settings"""
    self.logger = setup_logger("GOPAL", "gopal_scraper.log")
  
  def _get_random_user_agent(self) -> str:
    """Return a random user agent from predefined list."""
    return random.choice(self.USER_AGENTS)
  
  def init_driver(self) -> webdriver.Chrome:
    """Initialize and return a Chrome WebDriver with configured options."""
    try:
      options = webdriver.ChromeOptions()
      
      if self.headless:
        options.add_argument('--headless')
      
      options.add_argument('--no-sandbox')
      options.add_argument('--disable-dev-shm-usage')
      options.add_argument(f'user-agent={self._get_random_user_agent()}')
      options.add_argument('--disable-blink-features=AutomationControlled')
      options.add_argument('--window-size=1920,1080')
      
      self.driver = webdriver.Chrome(options=options)
      self.driver.set_page_load_timeout(self.PAGE_LOAD_TIMEOUT)
      return True
    except WebDriverException as e:
      self.logger.error(f"Driver initialization failed: {str(e)}")
      return False
  
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
  
  def _extract_product_details(self, soup: BeautifulSoup) -> Dict[str, str]:
    """Extract product details from the product page"""
    details = {
      "asin": None,
      "weight": None,
      "brand": None,
      "additives": None,
      "net_quantity": None,
      "allergen_information": None,
      "ingredients": None,
      "ingredient_type": None,
      'generic_name': None
    }
    
    # Extract from technical details table
    rows = soup.select('#productDetails_techSpec_section_1 tr')
    for row in rows:
      key_el = row.find('th')
      value_el = row.find('td')
      if key_el and value_el:
        key = self._clean_text(key_el.get_text())
        value = self._clean_text(value_el.get_text())
        self._process_detail_row(key.lower(), value, details)
    
    # Extract from additional information section
    additional_info = soup.select('#productDetails_detailBullets_sections1 tr')
    for row in additional_info:
      key_el = row.find('th')
      value_el = row.find('td')
      if key_el and value_el:
        key = self._clean_text(key_el.get_text())
        value = self._clean_text(value_el.get_text())
        self._process_detail_row(key.lower().strip(), value, details)
    
    return details
  
  def _process_detail_row(self, key: str, value: str, details: Dict[str, str]):
    """Process a single detail row and update the details dictionary"""
    if key == "weight" and not details["weight"]:
      details["weight"] = value
    elif key == "brand":
      details["brand"] = value
    elif key == "additives":
      details["additives"] = value
    elif key == "net quantity":
      details["net_quantity"] = value
    elif key == "allergen information":
      details["allergen_information"] = value
    elif key == "ingredient type":
      details["ingredient_type"] = value
    elif key == "ingredients":
      if "Allergen Information:" in value:
        parts = value.split("Allergen Information:")
        details["ingredients"] = self._clean_text(parts[0])
        details["allergen_information"] = self._clean_text(parts[1])
      elif "Allergen information:" in value:
        parts = value.split("Allergen information:")
        details["ingredients"] = self._clean_text(parts[0])
        details["allergen_information"] = self._clean_text(parts[1])
      else:
        details["ingredients"] = value
    elif key == "asin":
      details["asin"] = value
    elif key == "item weight" and not details["weight"]:
      details["weight"] = value
    elif key == "generic name":
      details["generic_name"] = value
  
  def _extract_ingredients(self, soup: BeautifulSoup) -> Optional[str]:
    """Extract ingredients from product page"""
    sections = soup.select('#important-information .content')
    for section in sections:
      heading = section.find('h4')
      if heading and 'Ingredients' in heading.text:
        paragraphs = section.find_all('p')
        for p in paragraphs:
          text = p.get_text(strip=True)
          if text:
            return text
    return None
  
  def _get_images(self, soup: BeautifulSoup) -> List[str]:
    """
    Extract product image URLs from Gopal product page soup.
    First tries JavaScript 'colorImages' block, then falls back to direct HTML.
    """
    image_urls = []
    try:
      imgs = soup.find_all('img', class_='img-thumbnail')
      image_urls = [img['src'] for img in imgs if img.has_attr('src')]
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
    footer_height = self.driver.execute_script(
      "return document.getElementById('web-footer').offsetHeight;")
    retries = 0
    
    while retries < self.MAX_SCROLL_RETRIES:
      try:
        self.driver.execute_script(
          f"window.scrollTo(0, {last_height - footer_height - random.randint(600, 700)});")
        time.sleep(self.SCROLL_PAUSE_TIME + random.random())
        new_height = self.driver.execute_script("return document.body.scrollHeight")
        
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
    """Scrape product URLs from an Gopal category page."""
    if not self._safe_get(url):
      return []
    
    self._load_all_products()
    product_urls = set()
    
    while True:
      try:
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        product_divs = soup.find_all('div', class_='col-xl-4 col-sm-6 product-item col-md-6')
        
        for product in product_divs:
          anchor_tags = product.find_all('a', href=True)
          for a in anchor_tags:
            href = a['href']
            if href:
              product_urls.add(href)
              break
        
        self.logger.info(f"Collected {len(product_urls)} unique product URLs so far.")
        
        if not self.click_next_button():
          break
        
        time.sleep(self.SCROLL_PAUSE_TIME + random.random())
      
      except Exception as e:
        self.logger.error(f"Error while extracting product URLs: {e}")
        break
    
    self.logger.info(f"Total product URLs collected: {len(product_urls)}")
    return list(product_urls)
  
  def get_product_details(self, url: str) ->List[Dict[str, Any]]:
    """Extract detailed product information from product page"""
    product_data = []
    for attempt in range(self.MAX_RETRIES):
      try:
        if not self._safe_get(url):
          continue
        
        time.sleep(self.SCROLL_PAUSE_TIME + random.randint(10, 15))
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        images = self._get_images(soup)
        
        def safe_find(by, value):
          try:
            return self._clean_text(self.driver.find_element(by, value).text)
          except:
            return None
        
        for i in range(1, 5):
          product_data.append({
            "variant_id": None,
            "name": safe_find(By.CLASS_NAME, 'section-title.text-break'),
            "product_url": url,
            "barcode": safe_find(By.ID, 'bar-code'),
            "brand_name": "Gopal Namkeen",
            "diet": self.get_diet('veg'),
            "mass_measurement_unit": self.get_mass_measurement_unit(safe_find(By.ID, 'current_product_weight')),
            "net_weight": safe_find(By.ID, 'current_product_weight'),
            "mrp": safe_find(By.CLASS_NAME, 'total_price_update'),
            "nutrients_main_ocr": None,
            "images": self.extract_image_urls_text(images),
            "source": "Gopal Side",
            "status": "raw",
          })
          
          try:
            element = self.driver.find_element(By.ID, f"modal_weight_{i}")
            if element.is_displayed() and element.is_enabled():
              element.click()
              time.sleep(12)
              self.logger.info(f"Clicked on 'modal_weight_{i}'")
            else:
              self.logger.info("'modal_weight_1' found but not clickable")
              break
              
          except Exception as e:
            self.logger.info("'modal_weight_1' not found — skipping click")
            break
          
        return product_data
      
      except Exception as e:
        self.logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
        if attempt == self.MAX_RETRIES - 1:
          return product_data
        time.sleep(self.SCROLL_PAUSE_TIME * (attempt + 1))
    
    return product_data
  
  def scrape_category(self, category_url: str) -> None:
    """Main method to scrape an Gopal category"""
    try:
      if not self.init_driver():
        raise WebDriverException("Failed to initialize WebDriver")
      
      self.logger.info(f"Starting scraping for URL: {category_url}")
      print(f"Starting scraping for URL: {category_url}")
      product_urls = self.get_product_urls(category_url)
      # product_urls = ["https://www.gopalnamkeen.com/product/namkeen/shakarpara","https://www.gopalnamkeen.com/product/namkeen/cornigo-vanilla-balls"]
      
      if not product_urls:
        self.logger.error("No product URLs found")
        return
      self.logger.info(f"Found {len(product_urls)} product URLs to scrape")
      print(f"Found {len(product_urls)} product URLs to scrape")
      
      # Create a progress bar
      pbar = tqdm(total=len(product_urls), initial=0, desc="Gopal Scrapped Products", unit="products",
                  dynamic_ncols=True)
      for i, url in enumerate(product_urls, 1):
        product_data = self.get_product_details(url)
        if product_data:
          for data in product_data:
            # print(f"Scraped product {i}/{len(data)}: {data}")
            url = "http://10.0.101.153:10000/insert"
            response = requests.post(url, json=data)
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


if __name__ == "__main__":
  gopal_screpped = Gopal(headless=False)
  gopal_screpped.scrape_category(category_url="https://www.gopalnamkeen.com/categories/newly-launched")