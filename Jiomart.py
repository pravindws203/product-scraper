"""
Jiomart Web Scraper Module
Author: Pravin Prajapati
A modular scraper for Jiomart product data with:
- Product page details scraping
"""

import re
import time
import random
import requests
from logger_config import setup_logger
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
  WebDriverException,
  TimeoutException,
  NoSuchElementException
)
from tqdm import tqdm
from seleniumwire import webdriver
from google_search import GoogleSearch


class Jiomart:
  def __init__(self, headless: bool = True):
    """
    Initialize the Jiomart scraper

    Args:
        headless (bool): Run browser in headless mode
    """
    self._setup_logging()
    self.headless = headless
    self.driver = None
    self._configure_constants()
  
  def _configure_constants(self):
    """Initialize scraper constants"""
    self.BASE_URL = "https://www.jiomart.com/"
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
    self.PAGE_LOAD_TIMEOUT = 20
    self.REQUEST_TIMEOUT = 30
  
  def _setup_logging(self):
    """Configure logging settings"""
    self.logger = setup_logger("JIOMART", "jiomart_scrapped.log")
  
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
        "source": "Jiomart",
        "status": "raw",
        "addtional_detail": scraped_data.get('details', None),
      }
    
    return filtered_data
  def _load_all_products(self) -> None:
    """Load all products on the page by scrolling and clicking 'Load More'"""
    time.sleep(self.SCROLL_PAUSE_TIME + random.random())
    last_height = self.driver.execute_script("return document.body.scrollHeight")
    footer = self.driver.find_element("tag name", "footer")
    footer_height = footer.size['height']
    retries = 0
    
    while retries < self.MAX_SCROLL_RETRIES:
      try:
        wait = WebDriverWait(self.driver, 10)
        # button = wait.until(EC.element_to_be_clickable(
        #   (By.CSS_SELECTOR, "button.Button__secondary__sMAVa")))
        # button.click()
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
  
  def click_out_of_stock(self):
    """Click the 'Out of Stock' checkbox to filter products"""
    try:
        time.sleep(self.SCROLL_PAUSE_TIME + random.random())
        # Wait for the label span containing the text
        # label = WebDriverWait(self.driver, 10).until(
        #     EC.element_to_be_clickable((By.XPATH, "//span[text()='Include Out of stock']"))
        # )
        #
        # # Scroll into view and click
        # self.driver.execute_script("arguments[0].scrollIntoView(true);", label)
        # label.click()
        checkbox = self.driver.find_element(By.ID, "in_stock_check")
        checkbox.click()

        self.logger.info("Clicked on 'Include Out of stock' label successfully.")

    except Exception as e:
        self.logger.error("Error clicking out-of-stock checkbox: %s", e)
      
  def get_product_urls(self, url: str) -> List[str]:
    """Scrape product URLs from an Amazon category page."""
    if not self._safe_get(url):
        return []
    
    time.sleep(5)
    # self.click_out_of_stock()
    # time.sleep(10)
    product_urls = set()

    try:
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        for a_tag in soup.select("ol.ais-InfiniteHits-list li a[href]"):
          href = a_tag["href"]
          full_url = f"https://www.jiomart.com{href}" if href.startswith("/") else href
          product_urls.add(full_url)

        self.logger.info(f"Collected {len(product_urls)} unique product URLs so far.")

        time.sleep(self.SCROLL_PAUSE_TIME + random.random())

    except Exception as e:
        self.logger.error(f"Error while extracting product URLs: {e}")

    self.logger.info(f"Total product URLs collected: {len(product_urls)}")
    return list(product_urls)
  
  def _get_images(self, soup: BeautifulSoup) -> List[str]:
    """Extract product images from page"""
    try:
      product_media = soup.find("div", class_ = "product-media")
      image_tags = product_media.find_all('img', class_='swiper-thumb-slides-img')
      cleaned_urls = []
      
      for img in image_tags:
        src = img.get('src')
        if src:
          parsed = urlparse(src)
          cleaned_url = urlunparse(parsed._replace(query=''))
          cleaned_urls.append(cleaned_url)
          
      return cleaned_urls
    except Exception as e:
      self.logger.error(f"Error extracting images: {e}")
    return []
  
  def _extract_product_details(self, soup: BeautifulSoup) -> Dict[str, str]:
    """Extract product details from the product page"""
    product_info = {}
    
    tables = soup.find_all('table', class_='product-specifications-table')
    
    for table in tables:
      rows = table.find_all('tr', class_='product-specifications-table-item')
      for row in rows:
        try:
          key_tag = row.find('th', class_='product-specifications-table-item-header')
          value_tag = row.find('td', class_='product-specifications-table-item-data')
          
          if key_tag and value_tag:
            key = key_tag.get_text(strip=True).lower().replace(' ', '_')
            
            # Handle image-based values (e.g., veg/non-veg icon)
            if value_tag.img:
              img_tag = value_tag.find('img')
              img_src = img_tag.get('src', '')
              if "icon-veg" in img_src:
                value = "Veg"
              elif "icon-nonveg" in img_src:
                value = "Non Veg"
              else:
                value = img_tag.get('alt', '').strip()
            else:
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
        product_full_name = soup.find('div', id='pdp_product_name').get_text(strip=True)
        price_span = soup.select_one("#price_section .product-price span.jm-heading-xs")
        price = price_span.get_text(strip=True) if price_span else None
        
        # Extract product details
        images = self._get_images(soup)
        details = self._extract_product_details(soup)
        
        product = {
          "product_url": url,
          "name": product_full_name.split('|')[0].strip(),
          "brand_name": details.get('brand', None),
          "mrp": price,
          "images": {"image_urls": images},
          "status": "raw",
          "source": "jiomart",
          "mass_measurement_unit": self.get_mass_measurement_unit(details.get('net_quantity')) or self.get_mass_measurement_unit(details.get('net_weight')),
          "details": details,
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
    """Main method to scrape an Jiomart product"""
    try:
      if not self.init_driver():
        raise WebDriverException("Failed to initialize WebDriver")
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
    """Main method to scrape an Jiomart category"""
    try:
      if not self.init_driver():
        raise WebDriverException("Failed to initialize WebDriver")
      
      self.logger.info(f"Starting scraping for URL: {category_url}")
      print(f"Starting scraping for URL: {category_url}")
      product_urls = self.get_product_urls(category_url)
      
      self.logger.info(f"Found {len(product_urls)} product URLs to scrape")
      print(f"Found {len(product_urls)} product URLs to scrape")
      # Create a progress bar
      pbar = tqdm(total=len(product_urls), initial=0, desc="Amazon Scrapped Products", unit="products",
                  dynamic_ncols=True)
      for i, url in enumerate(product_urls, 1):
        product_data = self.get_product_details(url)
        if product_data:
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
        
  def search_product(self, query: str) -> Dict[str, Any]:
    """Search for a product on Jiomart using Google Search"""
    try:
      google_search = GoogleSearch()
      search_url = google_search.search(query, 'jiomart.com')
      if search_url:
        self.logger.info(f"Found product URL: {search_url}")
        product_images = self.scrape_product(search_url)
        return product_images
      else:
        self.logger.warning("No product URL found")
        return None
    except Exception as e:
      self.logger.error(f"Error during Google search: {e}")
      return None