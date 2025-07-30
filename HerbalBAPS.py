"""
HerbalBAPS Web Scraper Module
Author: Pravin Prajapati
A modular scraper for HerbalBAPS product data with:
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


class HerbalBAPS:
  def __init__(self, headless: bool = True):
    """
    Initialize the HerbalBAPS scraper

    Args:
        headless (bool): Run browser in headless mode
    """
    self._setup_logging()
    self.headless = headless
    self.driver = None
    self._configure_constants()
  
  def _configure_constants(self):
    """Initialize scraper constants"""
    self.BASE_URL = "https://herbal.baps.org"
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
    self.MAX_SCROLL_RETRIES = 10
    self.SCROLL_PAUSE_TIME = 5
    self.MAX_RETRIES = 3
    self.PAGE_LOAD_TIMEOUT = 60
    self.REQUEST_TIMEOUT = 30
  
  def _setup_logging(self):
    """Configure logging settings"""
    self.logger = setup_logger("HerbalBAPS", "herbal_baps_scraper.log")
  
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
    details = {
        "barcode": None,
        "product_name": None,
        "weight": None,
        "brand": None,
        "price": None,
        "net_quantity": None,
        "allergen_information": None,
        "ingredients": None,
        "ingredient_type": None,
        "generic_name": None
    }

    # Extract weight
    weight_div = soup.find("div", class_="product attribute packing_weight")
    if weight_div:
        try:
            details['weight'] = weight_div.find("div", class_="value").get_text(strip=True)
        except AttributeError:
            pass

    # Extract SKU / barcode
    sku_div = soup.find("div", class_="product attribute sku")
    if sku_div:
        value_div = sku_div.find("div", class_="value", itemprop="sku")
        if value_div:
            details['barcode'] = value_div.get_text(strip=True)

    # Extract ingredients
    desc_div = soup.find("div", class_="value", itemprop="description")
    if desc_div:
        for p in desc_div.find_all("p"):
            strong = p.find("strong")
            if strong and "INGREDIENTS" in strong.get_text(strip=True).upper():
                full_text = p.get_text(separator=" ", strip=True)
                ingredients = full_text.replace(strong.get_text(strip=True), '').strip(" :\xa0")
                details['ingredients'] = ingredients
                break
            b = p.find("b")
            if b and "INGREDIENTS" in b.get_text(strip=True).upper():
              full_text = p.get_text(separator=" ", strip=True)
              ingredients = full_text.replace(strong.get_text(strip=True), '').strip(" :\xa0")
              details['ingredients'] = ingredients
              break
          
    # Extract product name
    product_name_tag = soup.find("span", class_="base", itemprop="name")
    if product_name_tag:
        details['product_name'] = product_name_tag.get_text(strip=True)

    # Extract price
    price_meta = soup.find("meta", itemprop="price")
    details['price'] = price_meta['content'] if price_meta else None

    return details
  
  def _get_images(self, soup: BeautifulSoup) -> List[str]:
    """
    Extract product image URLs from HerbalBAPS product page soup.
    First tries JavaScript 'colorImages' block, then falls back to direct HTML.
    """
    image_urls = []
    try:
      wait = WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT)
      element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "fotorama__nav__shaft")))
      nav_shaft = soup.find("div", class_="fotorama__nav__shaft")
      image_tags = nav_shaft.find_all("img")
      image_urls = [img['src'] for img in image_tags if img.get('src')]
    except Exception as e:
      self.logger.error(f"Error extracting images: {e}")
    
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
    clean_urls = []
    for url in image_urls:
      clean_urls.append(re.sub(r'cache/[^/]+/', '', url))
    return json.dumps({"image_urls": clean_urls}, indent=2)
  
  def _load_all_products(self) -> None:
    """Load all products on the page by scrolling and clicking 'Load More'"""
    time.sleep(self.SCROLL_PAUSE_TIME + random.random())
    last_height = self.driver.execute_script("return document.body.scrollHeight")
    news_latter_height = self.driver.execute_script("return document.getElementById('newsLatter').offsetHeight;")
    footer_tag = self.driver.execute_script("""
                    const footer = document.querySelector('footer');
                    return footer ? footer.offsetHeight : 0;
                    """)
    footer_height = int(news_latter_height) + int(footer_tag)
    retries = 0
    
    while retries < self.MAX_SCROLL_RETRIES:
      try:
        wait = WebDriverWait(self.driver, 10)
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
    Clicks the 'Next' button on pagination if available.
    Returns True if clicked, False if no next page.
    """
    try:
        time.sleep(self.SCROLL_PAUSE_TIME + random.randint(4, 8))
        next_btn = self.driver.find_element(By.CSS_SELECTOR, 'li.pages-item-next a.action.next')

        # Check if the button is visible and enabled
        if next_btn.is_displayed() and next_btn.is_enabled():
            self.logger.info("Clicking Next button...")
            next_btn.click()
            return True
        else:
            self.logger.warning("Next button is not clickable or not visible.")
            return False

    except NoSuchElementException:
        self.logger.info("No Next button found. Reached last page.")
        return False
  
  def get_product_urls(self, url: str) -> List[str]:
    """Scrape product URLs from an HerbalBAPS category page."""
    if not self._safe_get(url):
      return []
    
    self._load_all_products()
    product_urls = set()
    
    while True:
      try:
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        div_grid = soup.find("div", class_=re.compile(r'\bproducts-grid\b'))
        urls = [a['href'] for a in div_grid.find_all('a', href=True)]
        
        for url in urls:
          product_urls.add(url)
        
        self.logger.info(f"Collected {len(product_urls)} unique product URLs so far.")
        
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
        
        time.sleep(self.SCROLL_PAUSE_TIME + random.randint(5, 7))
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        details = self._extract_product_details(soup)
        images = self._get_images(soup)
        product = {
          "variant_id": None,
          "name": details.get("product_name"),
          "barcode": details.get("barcode"),
          "product_url": url,
          "brand_name": "BAPS Amrut",
          "category": None,
          "sub_category": None,
          "diet": self.get_diet('veg'),
          "allergen_information": details.get('allergen_information'),
          "mass_measurement_unit": self.get_mass_measurement_unit(details.get("weight")),
          "net_weight": details.get("weight"),
          "mrp": details.get("price"),
          "ingredients_main_ocr": details.get("ingredients"),
          "nutrients_main_ocr": None,
          "images": self.extract_image_urls_text(images),
          "other_images": None,
          "breadcrumbs": None,
          "front_img": None,
          "back_img": None,
          "nutrients_img": None,
          "ingredients_img": None,
          "source": "HerbalBAPS",
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
    """Main method to scrape an HerbalBAPS category"""
    try:
      if not self.init_driver():
        raise WebDriverException("Failed to initialize WebDriver")
      
      self.logger.info(f"Starting scraping for URL: {category_url}")
      print(f"Starting scraping for URL: {category_url}")
      product_urls = self.get_product_urls(category_url)
      # product_urls = ['https://herbal.baps.org/rajwadi-milk-masala.html']

      if not product_urls:
        self.logger.error("No product URLs found")
        return
      
      self.logger.info(f"Found {len(product_urls)} product URLs to scrape")
      print(f"Found {len(product_urls)} product URLs to scrape")
      
      # Create a progress bar
      pbar = tqdm(total=len(product_urls), initial=0, desc="HerbalBAPS Scrapped Products", unit="products",
                  dynamic_ncols=True)
      for i, url in enumerate(product_urls, 1):
        product_data = self.get_product_details(url)
        if product_data.get("name"):
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
  obj = HerbalBAPS(headless=False)
  obj.scrape_category(category_url="https://herbal.baps.org/herbal-food-supplements.html")