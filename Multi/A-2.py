"""
Amazon Web Scraper Module
Author: Pravin Prajapati
A modular scraper for Amazon product data with:
- AJAX API data extraction
- Product page details scraping
"""

import os
import re
import csv
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


class Amazon:
  def __init__(self, headless: bool = True):
    """
    Initialize the Amazon scraper

    Args:
        headless (bool): Run browser in headless mode
    """
    self._setup_logging()
    self.headless = headless
    self.driver = None
    self._configure_constants()
  
  def _configure_constants(self):
    """Initialize scraper constants"""
    self.BASE_URL = "https://www.amazon.in/"
    self.USER_AGENTS = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edge/114.0.1823.67',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; AS; Desktop) like Gecko',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Brave/1.43.88',
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Vivaldi/5.8.2945.60'
    ]
    self.MAX_SCROLL_RETRIES = 10
    self.SCROLL_PAUSE_TIME = 4
    self.MAX_RETRIES = 3
    self.PAGE_LOAD_TIMEOUT = 20
    self.REQUEST_TIMEOUT = 30
  
  def _setup_logging(self):
    """Configure logging settings"""
    self.logger = setup_logger("AMAZON", "amazon_scraper.log")
  
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
  
  def get_breadcrumbs(self, soup: BeautifulSoup) -> List[str]:
    """
    Extracts breadcrumb navigation from an Amazon product/category page.
    Returns a list of breadcrumb text values.
    """
    breadcrumbs = []
    try:
      div = soup.find("div", id="wayfinding-breadcrumbs_feature_div")
      breadcrumb_ul = div.find("ul", class_="a-unordered-list")
      if breadcrumb_ul:
        breadcrumb_links = breadcrumb_ul.find_all("a", class_="a-link-normal a-color-tertiary")
        breadcrumbs = [link.get_text(strip=True) for link in breadcrumb_links]
        self.logger.info(f"Breadcrumbs extracted: {' > '.join(breadcrumbs)}")
      else:
        self.logger.warning("Breadcrumb section not found.")
    except Exception as e:
      self.logger.error(f"Error extracting breadcrumbs: {e}")
    
    return breadcrumbs
  
  def get_all_product_images(self, soup: BeautifulSoup) -> List[str]:
    """
    Extract all product image URLs from an Amazon product page.

    :param soup: The URL of the Amazon product.
    :return: List of image URLs.
    """
    image_urls = set()
    
    try:
      # 1. Main image
      main_img = soup.select_one("#landingImage")
      if main_img and main_img.has_attr('src'):
        image_urls.add(main_img['src'])
      
      # 2. Image thumbnails via data-a-dynamic-image (contains all image URLs as JSON-like string)
      image_data = soup.select_one("#imgTagWrapperId img")
      if image_data and image_data.has_attr("data-a-dynamic-image"):
        dynamic_image_json = image_data["data-a-dynamic-image"]
        urls = re.findall(r'"(https://[^"]+)"', dynamic_image_json)
        image_urls.update(urls)
      
      # 3. Gallery images from thumbnail container (optional fallback)
      thumbnails = soup.select("li.image.item img")
      for thumb in thumbnails:
        src = thumb.get("src")
        if src:
          high_res = re.sub(r"\._.*?_\.", ".", src)
          image_urls.add(high_res)
      
      self.logger.info(f"Found {len(image_urls)} image(s) for second method.")
      return list(image_urls)
    
    except Exception as e:
      self.logger.error(f"Error extracting images: {e}")
      return []
  
  def _get_images(self, soup: BeautifulSoup) -> List[str]:
    """
    Extract product image URLs from Amazon product page soup.
    First tries JavaScript 'colorImages' block, then falls back to direct HTML.
    """
    image_urls = []
    try:
      scripts = soup.find_all("script")
      for script in scripts:
        if script and "colorImages" in str(script):
          json_str = script.string or script.get_text()
          if json_str:
            json_str = json_str.replace("'", '"')  # Convert to valid JSON format
            matches_hd = re.findall(r'"hiRes"\s*:\s*"([^"]+)"', json_str)
            image_urls.extend(matches_hd)
            matches = re.findall(r'"large"\s*:\s*"([^"]+)"', json_str)
            image_urls.extend(matches)
            
            if matches:
              break
    except Exception as e:
      self.logger.error(f"Error extracting images from JS: {e}")
    
    if not image_urls:
      image_urls = self.get_all_product_images(soup)
    
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
      "return document.getElementById('navFooter').offsetHeight;")
    retries = 0
    
    while retries < self.MAX_SCROLL_RETRIES:
      try:
        wait = WebDriverWait(self.driver, 10)
        self.driver.execute_script(
          f"window.scrollTo(0, {last_height - footer_height - random.randint(600, 700)});")
        time.sleep(self.SCROLL_PAUSE_TIME + random.random())
        new_height = self.driver.execute_script("return document.body.scrollHeight")
        
        try:
          button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.Button__secondary__sMAVa")))
          button.click()
        except:
          pass
        
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
    """Scrape product URLs from an Amazon category page."""
    if not self._safe_get(url):
      return []
    
    self._load_all_products()
    product_urls = set()
    
    last_height = self.driver.execute_script("return document.body.scrollHeight")
    footer_height = self.driver.execute_script(
      "return document.getElementById('navFooter').offsetHeight;")
    
    while True:
      try:
        self.driver.execute_script(
          f"window.scrollTo(0, {last_height - footer_height - random.randint(600, 700)});")
        time.sleep(self.SCROLL_PAUSE_TIME + random.randint(1, 5))
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        product_elements = soup.find_all('a', class_=lambda x: x and (
            'ProductGridItem__overlay__IQ3Kw' in x or
            ('a-link-normal' in x and 's-no-outline' in x)
        ))
        product_link = soup.find_all('a', class_=re.compile(r'ProductShowcase__title__'))
        
        for product in product_link:
          href = product.get('href')
          if href and '/dp/' in href:
            product_urls.add('https://www.amazon.in' + href)
        
        for product in product_elements:
          href = product.get('href')
          if href and '/dp/' in href:
            product_urls.add('https://www.amazon.in' + href)
        
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
        
        time.sleep(self.SCROLL_PAUSE_TIME + random.randint(3, 6))
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        details = self._extract_product_details(soup)
        ingredients = self._extract_ingredients(soup) or details.get('ingredients')
        images = self._get_images(soup)
        
        def safe_find(by, value):
          try:
            return self._clean_text(self.driver.find_element(by, value).text)
          except:
            return None
        
        product_images = {}
        
        product = {
          "variant_id": None,
          "name": safe_find(By.ID, 'productTitle'),
          "product_url": url,
          "brand_name": details.get('brand'),
          "category": None,
          "sub_category": None,
          "diet": self.get_diet(details.get('ingredient_type')),
          "allergen_information": details.get('allergen_information'),
          "mass_measurement_unit": self.get_mass_measurement_unit(
            details.get('weight')) or self.get_mass_measurement_unit(details.get('net_quantity')),
          "net_weight": details.get('weight') or details.get('net_quantity'),
          "mrp": safe_find(By.CLASS_NAME, 'a-price-whole') or safe_find(By.CLASS_NAME, 'a-price'),
          "ingredients_main_ocr": ingredients,
          "nutrients_main_ocr": None,
          "images": self.extract_image_urls_text(images),
          "other_images": self.extract_image_urls_text(product_images.get("images")),
          "breadcrumbs": {"category": self.get_breadcrumbs(soup)},
          "front_img": None,
          "back_img": None,
          "nutrients_img": None,
          "ingredients_img": None,
          "source": "Amazon",
          "status": "raw",
          "addtional_detail": self.get_technical_details(soup),
          "addtional_info": self.get_additional_information(soup)
        }
        
        return product
      
      except Exception as e:
        self.logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
        if attempt == self.MAX_RETRIES - 1:
          return {}
        time.sleep(self.SCROLL_PAUSE_TIME * (attempt + 1))
    
    return {}
  
  def scrape_category(self, category_url: str) -> None:
    """Main method to scrape an Amazon category"""
    try:
      if not self.init_driver():
        raise WebDriverException("Failed to initialize WebDriver")
      
      self.logger.info(f"Starting scraping for URL: {category_url}")
      print(f"Starting scraping for URL: {category_url}")
      product_urls = self.get_product_urls(category_url)
      
      if not product_urls:
        self.logger.error("No product URLs found")
        return
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
          response = requests.post(url, json=product_data)
          if response.status_code == 200:
            self.logger.info(f"Inserted product with ID: {response.json().get('id')}")
          else:
            self.logger.error(f"Failed to insert product data: {response.status_code}")
          
          data = response.json()
          
          # inserted_id = self.db.insert_data("scrapped_data", product_data)
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
  url = input("Enter Amazon Scrap Category Url: ").strip()
  option = input("This is a Product url Y/n: ").strip().lower()
  amazon_screpped = Amazon(headless=False)
  if option == 'y':
    amazon_screpped.scrape_product(product_url=url)
  else:
    amazon_screpped.scrape_category(category_url=url)
