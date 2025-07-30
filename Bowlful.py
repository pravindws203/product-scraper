"""
Bowlful Web Scraper Module
Author: Pravin Prajapati
A modular scraper for Bowlful product data with:
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
from bs4 import BeautifulSoup, NavigableString
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


class Bowlful:
  def __init__(self, headless: bool = True):
    """
    Initialize the Bowlful scraper

    Args:
        headless (bool): Run browser in headless mode
    """
    self._setup_logging()
    self.headless = headless
    self.driver = None
    self._configure_constants()
  
  def _configure_constants(self):
    """Initialize scraper constants"""
    self.BASE_URL = "https://bowlfulstore.com"
    self.USER_AGENTS = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edge/114.0.1823.67',
      'Mozilla/5.0 (iPhone; CPU iPhone OS 15_6_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 OPR/90.0.4480.80',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_2) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0.3 Safari/537.36',
      'Mozilla/5.0 (Linux; Android 11; Pixel 4 XL Build/RQ3A.210805.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
      'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:114.0) Gecko/20100101 Firefox/114.0',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; AS; Desktop) like Gecko',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Brave/1.43.88',
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Vivaldi/5.8.2945.60'
    ]
    self.MAX_SCROLL_RETRIES = 15
    self.SCROLL_PAUSE_TIME = 4
    self.MAX_RETRIES = 3
    self.PAGE_LOAD_TIMEOUT = 30
    self.REQUEST_TIMEOUT = 30
  
  def _setup_logging(self):
    """Configure logging settings"""
    self.logger = setup_logger("Bowl_FUL", "bowlful_scraper.log")
  
  def _get_random_user_agent(self) -> str:
    """Return a random user agent from predefined list."""
    return random.choice(self.USER_AGENTS)
  
  def init_driver(self) -> webdriver.Chrome:
    """Initialize and return a Chrome WebDriver with configured options."""
    try:
      options = webdriver.ChromeOptions()
      
      if self.headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
      
      options.add_argument('--no-sandbox')
      options.add_argument('--disable-dev-shm-usage')
      options.add_argument(f'user-agent={self._get_random_user_agent()}')
      options.add_argument('--disable-blink-features=AutomationControlled')
      options.add_argument('--window-size=1920,1080')
      
      self.driver = webdriver.Chrome(options=options)
      self.driver.set_page_load_timeout(self.PAGE_LOAD_TIMEOUT)
      return self.driver
    except WebDriverException as e:
      self.logger.error(f"Driver initialization failed: {str(e)}")
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
    
    # Extract from technical details table
    product_section = soup.find('div', {'class': 'woocommerce-product-details__short-description'})
    details = {}
    
    # Parse key-value pairs from <p> tags
    for p in product_section.find_all('p'):
      strong_tags = p.find_all('strong')
      for strong_tag in strong_tags:
        if strong_tag:
          key = strong_tag.get_text(strip=True).rstrip(':').lower()
          next_value = ''
          for elem in strong_tag.next_siblings:
            if isinstance(elem, NavigableString) and elem.strip():
              next_value = elem.strip()
              break
              
          if p.find("span").get_text(strip=True) != "":
            next_value = p.find("span").get_text(strip=True)
          # value = p.get_text(strip=True)
          details[key] = next_value
    
    return details
  
  def _get_images(self, soup: BeautifulSoup) -> List[str]:
    """
    Extract product image URLs from Bowlful product page soup.
    """
    image_urls = []
    try:
      thumbnain_div = soup.find("div", class_="productView-thumbnail-wrapper")
      image_div = thumbnain_div.find("div", class_="slick-list draggable")
      image_tags = image_div.find_all("img")
      urls = [img.get("src") for img in image_tags if img.get("src")]
      for url in urls:
        if url.startswith("//"):
          url = "https:" + url
          url = url.replace("_large", "")
        image_urls.append(url)
    
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
    footer = self.driver.find_element("tag name", "footer")
    footer_height = footer.size['height']
    retries = 0
    
    while retries < self.MAX_SCROLL_RETRIES:
      try:
        self.driver.execute_script(
          f"window.scrollTo(0, {last_height - footer_height - random.randint(700, 800)});")
        new_height = self.driver.execute_script("return document.body.scrollHeight")
        
        time.sleep(self.SCROLL_PAUSE_TIME + random.randint(2, 4))
        button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-load-more='Show More']")))
        button.click()
        
        if new_height == last_height:
          retries += 1
        else:
          last_height = new_height
          retries = 0
      
      except Exception as e:
        self.logger.error(f"Error during scrolling: {e}")
        break
  
  def get_product_urls(self, url: str) -> List[str]:
    """Scrape product URLs from an Bowlful category page."""
    if not self._safe_get(url):
      return []
    
    self._load_all_products()
    product_urls = set()
    
    while True:
      try:
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        product_ul = soup.find('ul', id="main-collection-product-grid")
        anchor_tags = product_ul.find_all('a') if product_ul else []
        urls = [a['href'] for a in anchor_tags if a.has_attr('href')]
        
        for url in urls:
          product_urls.add(self.BASE_URL + url)
        
        self.logger.info(f"Collected {len(product_urls)} unique product URLs so far.")
        time.sleep(self.SCROLL_PAUSE_TIME + random.random())
        break
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
        images = self._get_images(soup)
        detail = self._extract_product_details(soup)
        
        def safe_find(by, value):
          try:
            product_view = self.driver.find_element(By.CLASS_NAME, "productView-product.clearfix")
            return self._clean_text(product_view.find_element(by, value).text)
          except:
            return None
        
        product = {
          "variant_id": None,
          "name": safe_find(By.CLASS_NAME, 'productView-title'),
          "product_url": url,
          "brand_name": "Bowlful",
          "diet": self.get_diet("veg"),
          "mass_measurement_unit": self.get_mass_measurement_unit(detail.get("net weight inside")),
          "net_weight": detail.get("net weight inside"),
          "ingredients_main_ocr": detail.get("ingredients"),
          "mrp": safe_find(By.CLASS_NAME, 'money'),
          "images": self.extract_image_urls_text(images),
          "source": "Bowlful site",
          "status": "raw",
        }
        return product
      
      except Exception as e:
        self.logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
        if attempt == self.MAX_RETRIES - 1:
          return {}
        time.sleep(self.SCROLL_PAUSE_TIME * (attempt + 1))
    
    return {}
  
  def scrape_category(self, category_url: str) -> None:
    """Main method to scrape an Bowlful category"""
    try:
      if not self.init_driver():
        raise WebDriverException("Failed to initialize WebDriver")
      
      self.logger.info(f"Starting scraping for URL: {category_url}")
      print(f"Starting scraping for URL: {category_url}")
      product_urls = self.get_product_urls(category_url)
      # product_urls = ['https://bowlfulstore.com/products/ready-to-eat-moong-dal-sheera' ]
      
      if not product_urls:
        self.logger.error("No product URLs found")
        return
      self.logger.info(f"Found {len(product_urls)} product URLs to scrape")
      print(f"Found {len(product_urls)} product URLs to scrape")
      
      # Create a progress bar
      pbar = tqdm(total=len(product_urls), initial=0, desc="Bowlful Scrapped Products", unit="products",
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


if __name__ == "__main__":
  obj = Bowlful(headless=True)
  obj.scrape_category(category_url="https://bowlfulstore.com/collections/all-product")