"""
Blinkit Web Scraper Module
Author: Pravin Prajapati
A modular scraper for Blinkit product data with:
- AJAX API data extraction
- Product page details scraping
"""

import re
import requests
import gzip
import brotli
import zstandard as zstd
import time
import json
import random

from logger_config import setup_logger
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from selenium.common.exceptions import (
  WebDriverException,
  TimeoutException,
)
from seleniumwire import webdriver


class Blinkit:
  def __init__(self, headless: bool = True, lat: str = "28.7030425", lon: str = "77.430373"):
    """
    Initialize the Blinkit scraper

    Args:
        headless (bool): Run browser in headless mode
    """
    self._setup_logging()
    self.headless = headless
    self.driver = None
    self.lat = lat.strip()
    self.lon = lon.strip()
    self._configure_constants()
  
  def _configure_constants(self):
    """Initialize scraper constants"""
    self.BASE_URL = "https://blinkit.com"
    self.USER_AGENTS = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edge/114.0.1823.67',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_2) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0.3 Safari/537.36',
    ]
    self.MAX_SCROLL_RETRIES = 15
    self.SCROLL_PAUSE_TIME = 4
    self.MAX_RETRIES = 3
    self.PAGE_LOAD_TIMEOUT = 20
    self.REQUEST_TIMEOUT = 30
  
  def _setup_logging(self):
    """Configure logging settings"""
    self.logger = setup_logger("BLINKIT", "blinkit_scraper.log")
  
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
      return self.driver
    except WebDriverException as e:
      self.logger.error(f"Driver initialization failed: {str(e)}")
      return False
  
  def _safe_get(self, url: str) -> bool:
    """Safely navigate to URL with retries and check for known page errors."""
    for attempt in range(self.MAX_RETRIES):
        try:
            self.logger.info(f"Attempt {attempt + 1} to load {url}")
            self.driver.get(url)

            # Delay to let content render (JS-heavy pages)
            time.sleep(2)

            # Error condition check (e.g., if body or table has 'page-error' class)
            if "page-error-page lang-en path-node page-node-type-page" in self.driver.page_source:
                self.logger.error(f"Page access denied detected in content of {url}")
                return False

            # Example: check for empty table with error class
            error_elements = self.driver.find_elements("css selector", "table.page-error, div.page-error-page, #page-error")
            if error_elements:
                self.logger.error(f"Error element detected in {url}")
                return False

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
  
  def decompress_response(self, body: bytes, encoding: str) -> str:
    try:
        encoding = encoding.lower()
        if 'gzip' in encoding:
            return gzip.decompress(body).decode('utf-8')
        elif 'br' in encoding:
            return brotli.decompress(body).decode('utf-8')
        elif 'zstd' in encoding:
            dctx = zstd.ZstdDecompressor()
            return dctx.decompress(body).decode('utf-8')
        else:
            return body.decode('utf-8')  # Try plain text
    except Exception as e:
        raise RuntimeError(f"Decompression failed ({encoding}): {e}")
    
  @staticmethod
  def _clean_text(text: str) -> str:
    """Clean text by removing special characters and extra whitespace"""
    if not text:
      return ""
    return re.sub(r'[\u200e\u200f]', '', text).strip()
  
  def _get_images(self, media_container: Dict) -> List[str]:
    """
    Extract product image URLs from Blinkit product page soup.
    First tries JavaScript 'colorImages' block, then falls back to direct HTML.
    """
    image_urls = []
    for item in media_container.get("items"):
      try:
        image = item.get("image", {})
        image_urls.append(image.get("url"))
      except Exception as e:
        self.logger.error(f"Error extracting images from JS: {e}")
    
    return list(image_urls)
  
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

  def get_mainpage_products(self, url: str) -> Dict[str, Any]:
    """Scrape product URLs from Blinkit category page."""
    if not self._safe_get(url):
        return {"data": None, "header": None}

    import time, random
    time.sleep(self.SCROLL_PAUSE_TIME + random.randint(5,10))

    target_url_part = '/v1/layout/listing_widgets'

    for request in self.driver.requests:
        if request.response and target_url_part in request.url:
            encoding = request.response.headers.get('Content-Encoding', '')
            body = request.response.body

            try:
                content = self.decompress_response(body, encoding)

                try:
                    data = json.loads(content)
                    return {"data": data, "header": dict(request.headers)}
                except json.JSONDecodeError as je:
                    self.logger.error(f"JSON decode error: {je}")
                    self.logger.debug(f"Partial content: {content[:500]}")

            except Exception as e:
                self.logger.error(f"Decompression failed: {e}")
                with open("failed_response.bin", "wb") as f:
                    f.write(body)
                self.logger.warning("Saved raw binary to failed_response.bin")

    return {"data": None, "header": None}
    
  
  def product_details_import(self, products_data: Dict):
    """Extract detailed product information from product page"""
    response = products_data.get("response")
    for snippet in response.get("snippets", []):
      try:
        data = snippet.get("data", {})
        images = self._get_images(data.get("media_container", {}))
        product = {
          "variant_id": None,
          "name": data.get("name",{}).get("text", None),
          "product_url": None,
          "brand_name": data.get("brand_name",{}).get("text", None),
          "diet": None,
          "mass_measurement_unit": self.get_mass_measurement_unit(data.get("variant",{}).get("text", None)),
          "net_weight": data.get("variant",{}).get("text", None),
          "mrp": data.get("normal_price",{}).get("text", None),
          "images": self.extract_image_urls_text(images),
          "source": "Blinkit",
          "status": "raw",
          "addtional_detail": snippet,
          }
        url = "http://10.0.101.153:10000/insert"
        response = requests.post(url, json=product)
        if response.status_code == 200:
          self.logger.info(f"Inserted product with ID: {response.json().get('id')}")
        else:
          self.logger.error(f"Failed to insert product data: {response.status_code}")
      
      except Exception as e:
        self.logger.error(f"Error: {str(e)}")
    
  def scrape_category(self, category_url: str) -> None:
    """Main method to scrape an Blinkit category"""
    try:
      if not self.init_driver():
        raise WebDriverException("Failed to initialize WebDriver")
      
      self.logger.info(f"Starting scraping for URL: {category_url}")
      print(f"Starting scraping for URL: {category_url}")
      products_data = self.get_mainpage_products(category_url)
      
      if not products_data.get("data"):
        self.logger.error("No product URLs found")
        return
      
      # self.logger.info(f"Found {len(product_urls)} product URLs to scrape")
      self.product_details_import(products_data.get("data"))
      # Create a progress bar
      # pbar = tqdm(total=len(product_urls), initial=0, desc="Blinkit Scrapped Products", unit="products",
      #             dynamic_ncols=True)
      # for i, url in enumerate(product_urls, 1):
      #   product_data = self.get_product_details(url)
      #   if product_data:
      #     print(f"Scraped product {i}/{len(product_urls)}: {product_data}")
          # url = "http://10.0.101.153:10000/insert"
          # response = requests.post(url, json=product_data)
          # if response.status_code == 200:
          #   self.logger.info(f"Inserted product with ID: {response.json().get('id')}")
          # else:
          #   self.logger.error(f"Failed to insert product data: {response.status_code}")
          #
          # data = response.json()

          # inserted_id = self.db.insert_data("scrapped_data", product_data)
          # pbar.set_postfix({"Inserted product with ID": data.get('id', None)})
      #   else:
      #     self.logger.error(f"Failed to scrape product {i}/{url}")
      #
      #   time.sleep(random.randint(2, 5))
      #   pbar.update(1)
      #
      # self.logger.info(f"Completed scraping. Results saved in DATABASE")
    
    except KeyboardInterrupt:
      self.logger.info("\nScraping stopped by user")
    except Exception as e:
      self.logger.error(f"Critical error: {e}", exc_info=True)
    finally:
      if self.driver:
        self.driver.quit()
        
if __name__ == "__main__":
  obj = Blinkit(headless=False)
  obj.scrape_category("https://blinkit.com/dc/?collection_filters=W3siYnJhbmRfaWQiOlsxMTcyNl19XQ%3D%3D&collection_name=Moi+Soi")
  