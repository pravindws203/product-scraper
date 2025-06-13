"""
Zepto Web Scraper Module
Author: Pravin Prajapati
A modular scraper for Zepto product data with:
- Product page details scraping
"""

import re
import io
import gzip
import time
import json
import random
import requests
from logger_config import setup_logger
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
  WebDriverException,
  TimeoutException,
  NoSuchElementException
)
from tqdm import tqdm
from seleniumwire import webdriver


class Zepto:
  def __init__(self, headless: bool = True):
    """
    Initialize the Zepto scraper

    Args:
        headless (bool): Run browser in headless mode
    """
    self._setup_logging()
    self.headless = headless
    self.driver = None
    self._configure_constants()
  
  def _configure_constants(self):
    """Initialize scraper constants"""
    self.BASE_URL = "https://www.zeptonow.com"
    self.API_DOMAIN = "api.zeptonow.com/api/"
    self.USER_AGENTS = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edge/114.0.1823.67',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 OPR/90.0.4480.80',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_2) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0.3 Safari/537.36',
      'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:114.0) Gecko/20100101 Firefox/114.0',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Brave/1.43.88',
    ]
    self.MAX_SCROLL_RETRIES = 15
    self.SCROLL_PAUSE_TIME = 4
    self.MAX_RETRIES = 3
    self.PAGE_LOAD_TIMEOUT = 20
    self.REQUEST_TIMEOUT = 30

  def _setup_logging(self):
    """Configure logging settings"""
    self.logger = setup_logger("ZEPTO", "zeptonow_scrapped.log")
  
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
      return self.driver
  
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
      time.sleep(random.randint(2, 4))
    return False
  
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
  
  def extract_image_urls_text(self, image_urls: list) -> str:
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
  
  def safe_price_format(self, price: Any) -> str:
    """Format price by removing last 2 digits if possible."""
    try:
      if price and len(str(price)) > 2:
        return str(price)[:-2]
      return str(price)
    except Exception:
      return str(price)
    
  def filltered_scrapped_data(self, scraped_data):
    """
    Filter and clean the scraped data to remove unwanted fields.
    """
    filtered_data = {
      "barcode": None,
      "variant_id": None,
      "name": scraped_data.get('name', None),
      "product_url": scraped_data.get('product_url', None),
      "brand_name": scraped_data.get('brand_name', None),
      "category": None,
      "sub_category": None,
      "diet": scraped_data.get('food_type', None),
      "allergen_information": scraped_data.get('allergen_information', None),
      "mass_measurement_unit": scraped_data.get('mass_measurement_unit', None),
      "net_weight": scraped_data.get('net_quantity', None) or scraped_data.get('net_weight', None),
      "mrp": scraped_data.get('mrp', None),
      "ingredients_main_ocr": scraped_data.get('ingredients', None),
      "nutrients_main_ocr": scraped_data.get('nutrients', None),
      "images": scraped_data.get('images', None),
      "front_img": None,
      "back_img": None,
      "nutrients_img": None,
      "ingredients_img": None,
      "source": "Zepto",
      "status": "raw",
      "addtional_detail": scraped_data.get('details', None),
    }
    
    return filtered_data
  
  def generate_product_url(self, name: str, product_id: str) -> str:
    """Generate product URL from product name and ID."""
    if not product_id and not name:
      return ''
    product_name = re.sub(r'[^\w-]+', '-', name).strip('-').lower()
    return f"{self.BASE_URL}/pn/{product_name}/pvid/{product_id}"
  
  def extract_product_data(self, json_text: str) -> List[Dict[str, Any]]:
    """Extract product data from JSON API response."""
    try:
      data = json.loads(json_text)
      products = []
      
      for item in data.get('storeProducts', []):
        product_variant = item.get('productVariant', {})
        product = item.get('product', {})
        
        images = [
          'https://cdn.zeptonow.com/production/' + image.get('path')
          for image in product_variant.get('images', [])
          if image.get('path')
        ]
        
        products.append({
          'variant_id': product_variant.get('id'),
          'name': product.get('name'),
          'brand_name': product.get('brand'),
          'product_url': self.generate_product_url(
            product.get('name'),
            product_variant.get('id')
          ),
          'barcode': None,
          'ingredients_main_ocr': product.get('ingredients'),
          'allergen_information': product.get('allergen'),
          'images': self.extract_image_urls_text(images),
          'nutrients_main_ocr': product_variant.get('nutritionalInfo'),
          'mrp': self.safe_price_format(product_variant.get('mrp')),
          'diet': None,
          'mass_measurement_unit': self.get_mass_measurement_unit(product_variant.get('unitOfMeasure')),
          'net_weight': product_variant.get('weightInGms') or product_variant.get('packsize'),
          'sub_category': item.get('primarySubcategoryName'),
          'category': item.get('primaryCategoryName'),
          "status": "raw",
          "source": "Zepto",
        })
      return products
    except Exception as e:
      self.logger.error(f"JSON parse error: {e}")
      return []
  
  def decompress_gzip_response(self, response_body: bytes) -> Optional[str]:
    """Decompress gzip-encoded response body."""
    try:
      with gzip.GzipFile(fileobj=io.BytesIO(response_body)) as f:
        return f.read().decode('utf-8', errors='ignore')
    except Exception as e:
      self.logger.error(f"Decompression error: {e}")
      return None
    
  def _load_all_products(self) -> None:
    """Load all products on the page by scrolling and clicking 'Load More'"""
    time.sleep(self.SCROLL_PAUSE_TIME + random.random())
    last_height = self.driver.execute_script("return document.body.scrollHeight")
    footer_height = self.driver.execute_script("""
                    const footer = document.querySelector('footer');
                    return footer ? footer.offsetHeight : 0;
                    """)
    retries = 0
    handled_urls = set()
    while retries < self.MAX_SCROLL_RETRIES:
      try:
        self.driver.execute_script(f"window.scrollTo(0, {last_height - footer_height - random.randint(480, 550)});")
        time.sleep(self.SCROLL_PAUSE_TIME + random.randint(3, 6))
        new_height = self.driver.execute_script("return document.body.scrollHeight")

        # for request in self.driver.requests:
        #   if (request.response and self.API_DOMAIN in request.url and request.url not in handled_urls):
        #     handled_urls.add(request.url)
        #     self.logger.info(f"Processing API request: {request.url}")
        #
        #     try:
        #       content = (self.decompress_gzip_response(request.response.body)
        #                  if request.response.headers.get('Content-Encoding') == 'gzip'
        #                  else request.response.body.decode('utf-8'))
        #
        #       if content and request.response.status_code == 200:
        #         products = self.extract_product_data(content)
        #         print(products)
        #         for product in products:
        #           if product:
        #             url = "http://10.0.101.153:10000/insert"
        #             response = requests.post(url, json=self.filltered_scrapped_data(product))
        #             if response.status_code == 200:
        #               self.logger.info(f"Inserted product with ID: {response.json().get('id')}")
        #             else:
        #               self.logger.error(f"Failed to insert product data: {response.status_code}")
        #
        #           self.logger.info(f"Added {len(products)} products from API")
        #
        #     except Exception as e:
        #         self.logger.error(f"Error processing API response: {e}")
              
        if new_height == last_height:
          retries += 1
        else:
          last_height = new_height
          retries = 0
      
      except Exception as e:
        self.logger.error(f"Error during scrolling: {e}")
        break
  
  def   get_product_urls(self, url: str) -> List[str]:
    """Scrape product URLs from an Amazon category page."""
    if not self._safe_get(url):
      return []
    
    time.sleep(10)
    self._load_all_products()
    time.sleep(10)
    product_urls = set()
    
    try:
      soup = BeautifulSoup(self.driver.page_source, 'html.parser')
      main_section = soup.find('div', class_=re.compile(
        r'no-scrollbar grid grid-cols-2 content-start gap-y-4 gap-x-2 px-2.5 py-4 '
        r'md:grid-cols-3 md:gap-x-3 md:p-3 lg:grid-cols-5 xl:grid-cols-6'
      ))
      
      if not main_section:
        main_section = soup.find('div', class_=re.compile(
          r'grid w-full gap-x-3 gap-y-5 px-2 sm:gap-x-4 grid-cols-2 md:grid-cols-4 lg:grid-cols-6'
        ))
        
      if main_section:
        for a_tag in main_section.find_all('a', href=True):
          product_urls.add(self.BASE_URL + a_tag['href'])

      self.logger.info(f"Collected {len(product_urls)} unique product URLs so far.")

      time.sleep(self.SCROLL_PAUSE_TIME + random.random())

    except Exception as e:
      self.logger.error(f"Error while extracting product URLs: {e}")

    self.logger.info(f"Total product URLs collected: {len(product_urls)}")
    return list(product_urls)
  
  def _get_images(self, soup: BeautifulSoup) -> List[str]:
    """Extract product images from page"""
    try:
      images_urls = []
      if image_main_div := soup.find('div', class_='no-scrollbar relative flex max-h-full flex-col gap-4 overflow-y-scroll'):
        for img in image_main_div.find_all('img'):
          if raw_url := img.get('src'):
            cleaned_url = re.sub(r'/tr:[^/]+', '', raw_url)
            images_urls.append(cleaned_url)
      
      return images_urls
    except Exception as e:
      self.logger.error(f"Error extracting images: {e}")
    return []
  
  def _extract_product_details(self, soup: BeautifulSoup) -> Dict[str, str]:
    """Extract product details from the product page"""
    product_info = {}
    
    for table in ['productHighlights', 'productInformationL4']:
      try:
        if product_highlights := soup.find('div', id=table):
          for div in product_highlights.find_all("div", class_="flex items-start gap-3"):
            if key_tag := div.find("h3"):
              if value_tag := div.find("p"):
                key = key_tag.get_text(strip=True).lower()
                value = value_tag.get_text(strip=True)
                product_info[key] = value
            
      except Exception as e:
        self.logger.error(f"Error extracting product details: {e}")
        continue
    
    return product_info
  
  def get_product_details(self, url: str) -> Dict[str, Any]:
    """Extract detailed product information from product page"""
    for attempt in range(self.MAX_RETRIES):
      try:
        if not self._safe_get(url):
          continue
        
        time.sleep(random.randint(2, 5))
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # Extract product name and price
        product_full_name = None
        price = None
        product_header = soup.find('div', class_=re.compile(r'relative\s+flex\s+w-full'))
        if product_header:
          if name_tag := product_header.find('h1', class_='text-xl'):
            product_full_name = name_tag.get_text(strip=True)
          
          if price_tag := product_header.find('span', class_=re.compile(r'text-[^/]\s+font-medium')):
            price_text = price_tag.get_text(strip=True).replace("₹", "").replace(",", "")
            price = price_text
        
        # Extract product details
        images = self._get_images(soup)
        details = self._extract_product_details(soup)
        
        product = {
          "product_url": url,
          "name": product_full_name,
          "brand_name": "Kikibix" if details.get('brand', None) or details.get('brand', None) == 'BUNDLE' else details.get('brand', None),
          "mrp": price,
          "images": {"image_urls": images},
          "status": "raw",
          "source": "Zepto",
          "mass_measurement_unit": self.get_mass_measurement_unit(details.get('weight')) or self.get_mass_measurement_unit(details.get('net_weight')),
          "details" : details,
          **details
        }
        
        return product
      
      except Exception as e:
        self.logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
        if attempt == self.MAX_RETRIES - 1:
          return {}
        time.sleep(random.randint(2, 5))
    
    return {}
  
  def scrape_product(self, product_url: str) -> Dict[str, Any]:
    """Main method to scrape an Zepto product"""
    try:
      if not self.init_driver():
        return {}
      
      product_details = self.get_product_details(product_url)
      
      self.logger.info(f"Scraped product {product_url}")
      return product_details
    
    except KeyboardInterrupt:
      self.logger.info("\nScraping stopped by user")
      return {}
    except Exception as e:
      self.logger.error(f"Critical error: {e}", exc_info=True)
      return {}
    finally:
      if self.driver:
        self.driver.quit()
  
  def scrape_category(self, category_url: str) -> None:
    """Main method to scrape an Zepto category"""
    try:
      if not self.init_driver():
        raise WebDriverException("Failed to initialize WebDriver")
      
      self.logger.info(f"Starting scraping for URL: {category_url}")
      print(f"Starting scraping for URL: {category_url}")
      product_urls = self.get_product_urls(category_url)
      # product_urls = ["https://www.zeptonow.com/pn/kikibix-fruit-and-nut-digestive-cookies-healthy-tasty-fruit-biscuits-no-palm-oil-no-maida-130-g-combo/pvid/8150be4a-2281-4bd5-a9b7-e6779cacb236"]
      
      self.logger.info(f"Found {len(product_urls)} product URLs to scrape")
      print(f"Found {len(product_urls)} product URLs to scrape")
      
      # Create a progress bar
      pbar = tqdm(total=len(product_urls), initial=0, desc="Amazon Scrapped Products", unit="products",
                  dynamic_ncols=True)
      for i, url in enumerate(product_urls, 1):
        product_data = self.get_product_details(url)
        if product_data:
          # print(f"Scraped product {i}/{len(product_urls)}: {product_data}")
          url = "http://10.0.101.153:10000/insert"
          response = requests.post(url, json=self.filltered_scrapped_data(product_data))
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
  zepto_screpped = Zepto(headless=False)
  url = input("Enter Zepto Category url: ").strip()
  zepto_screpped.scrape_category(category_url=url)