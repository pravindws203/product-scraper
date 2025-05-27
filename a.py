"""
AmazonNow Web Scraper - Complete Version
Author: Pravin Prajapati
This script scrapes product data from AmazonNow website including:
1. AJAX API data (primary source)
2. Product page details (secondary source)
"""

import time
import json
import re
import csv
import os
import random
import gzip
import logging
import io
from typing import Any, Dict, List, Optional
from tqdm import tqdm
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException
)
from seleniumwire import webdriver

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/amazon_scraper.log'),
    ]
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.amazonnow.com"
API_DOMAIN = "api.amazonnow.com"
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
]
MAX_SCROLL_RETRIES = 15
SCROLL_PAUSE_TIME = 4
MAX_RETRIES = 3
PAGE_LOAD_TIMEOUT = 20
REQUEST_TIMEOUT = 30


def get_random_user_agent() -> str:
    """Return a random user agent from predefined list."""
    return random.choice(USER_AGENTS)


def init_driver() -> webdriver.Chrome:
    """Initialize and return a Chrome WebDriver with configured options."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f'user-agent={get_random_user_agent()}')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')

    wire_options = {
        'connection_timeout': REQUEST_TIMEOUT,
        'verify_ssl': False,
        'suppress_connection_errors': False
    }

    driver = webdriver.Chrome(options=options, seleniumwire_options=wire_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


def safe_get(driver: webdriver.Chrome, url: str) -> bool:
    """Safely navigate to URL with retries and proper waiting."""
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Attempt {attempt + 1} to load {url}")
            driver.get(url)

            # selector = "div[class*='grid grid-cols-2'], div[id='productHighlights'], div[id='productInformationL4']"
            # WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            #     ec.presence_of_element_located((By.CSS_SELECTOR, selector)))
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


def capture_ajax_data(driver: webdriver.Chrome, filename: str) -> None:
    """Capture and process AJAX API responses during scrolling."""
    handled_urls = set()
    last_height = driver.execute_script("return document.body.scrollHeight")
    footer_height = driver.execute_script("""
                const footer = document.querySelector('footer');
                return footer ? footer.offsetHeight : 0;
                """)
    same_count = 0
    print(f"Processing API requesting....")
    while same_count < MAX_SCROLL_RETRIES:
        driver.execute_script(f"window.scrollTo(0, {last_height - footer_height - random.randint(480, 600)});")
        time.sleep(SCROLL_PAUSE_TIME + random.randint(2,3))

        for request in driver.requests:
            if (request.response and
                'api.amazonnow.com/api/' in request.url and
                request.url not in handled_urls):

                handled_urls.add(request.url)
                logger.info(f"Processing API request: {request.url}")

                try:
                    pass
                    # content = (decompress_gzip_response(request.response.body)
                    #            if request.response.headers.get('Content-Encoding') == 'gzip'
                    #            else request.response.body.decode('utf-8'))
                    #
                    # if content and request.response.status_code == 200:
                    #     products = extract_product_data(content)
                    #     if products:
                    #         save_to_csv(products, filename)
                    #         logger.info(f"Added {len(products)} products from API")
                    #         print(f"Added {len(products)} products from API")
                except Exception as e:
                    logger.error(f"Error processing API response: {e}")

        new_height = driver.execute_script("return document.body.scrollHeight")
        same_count = same_count + 1 if new_height == last_height else 0
        last_height = new_height


def convert_to_dict(data: Dict[str, Any]) -> Dict[str, Optional[Any]]:
    """Convert scraped data to clean snake_case dictionary."""
    try:
        images = data.get('images', [])
        image_fields = {
            f'image_url_{i + 1}': images[i] if i < len(images) else ''
            for i in range(10)
        }

        details = data.get('details', {})
        return {
            'product_id': data.get('id'),
            'variant_id': data.get('variant_id'),
            'name': data.get('name'),
            'brand': details.get('brand'),
            'product_url': data.get('url'),
            'barcode': None,
            'ingredients': details.get('ingredients'),
            'allergen': details.get('allergen information'),
            'nutritional_info': details.get('nutrition information'),
            'price': data.get('price'),
            'dietary_preference': details.get('dietary preference', None),
            'unit_of_measure': details.get('unit'),
            'weight_in_gms': details.get('weight'),
            'packsize': details.get('serving size'),
            'primary_subcategory_name': details.get('product type'),
            'primary_category_name': None,
            **image_fields,
        }
    except Exception as e:
        logger.error("Failed to convert data: %s", e, exc_info=True)
        return {}


def clean_text(text):
    # Remove invisible unicode characters and extra whitespace
    return re.sub(r'[\u200e\u200f]', '', text).strip()

def extract_product_details(soup):
  details = {
    "weight": None,
    "brand": None,
    "additives": None,
    "net_quantity": None,
    "allergen_information": None,
    "ingredients": None,
    "ingredient_type	": None
  }
  
  rows = soup.select('#productDetails_techSpec_section_1 tr')
  
  for row in rows:
    key_el = row.find('th')
    value_el = row.find('td')
    if key_el and value_el:
      key = clean_text(key_el.get_text())
      value = clean_text(value_el.get_text())
      
      key_lower = key.lower()
      if key_lower == "weight":
        details["weight"] = value
      elif key_lower == "brand":
        details["brand"] = value
      elif key_lower == "additives":
        details["additives"] = value
      elif key_lower == "net quantity":
        details["net_quantity"] = value
      elif key_lower == "allergen information":
        details["allergen_information"] = value
      elif key_lower == "ingredient type":
        details["ingredient_type"] = value
      elif key_lower == "ingredients":
        if "Allergen Information:" in value:
          parts = value.split("Allergen Information:")
          details["ingredients"] = clean_text(parts[0])
          details["allergen_information"] = clean_text(parts[1])
        elif "Allergen information:" in value:
          parts = value.split("Allergen information:")
          details["ingredients"] = clean_text(parts[0])
          details["allergen_information"] = clean_text(parts[1])
        else:
          details["ingredients"] = value
  
  return details

def scrape_product_page(driver: webdriver.Chrome, url: str) -> Dict[str, Any]:
    """Scrape data from individual product page with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            if not safe_get(driver, url):
                continue
            time.sleep(SCROLL_PAUSE_TIME + random.random())

            variant_id = re.search(r'pvid/([a-f0-9-]+)', url).group(1) if re.search(r'pvid/([a-f0-9-]+)', url) else None

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            result = {
                'url': url,
                'variant_id': variant_id,
                "name": "N/A",
                "price": "N/A",
                "details": {},
                "images": []
            }

            # Product header
            product_header = soup.find('div', class_=re.compile(r'relative\s+flex\s+w-full'))
            if product_header:
                name_tag = product_header.find('h1', class_='text-xl')
                price_tag = product_header.find('span', class_=re.compile(r'text-[^/]\s+font-medium'))
                if name_tag:
                    result["name"] = name_tag.get_text(strip=True)
                if price_tag:
                    price_text = price_tag.get_text(strip=True).replace("₹", "").replace(",", "")
                    result["price"] = price_text

            # Product details
            for section in ['productHighlights', 'productInformationL4']:
                container = soup.find('div', id=section)
                if container:
                    for div in container.find_all("div", class_="flex items-start gap-3"):
                        key_tag = div.find("h3")
                        value_tag = div.find("p")
                        if key_tag and value_tag:
                            key = key_tag.get_text(strip=True).lower()
                            result["details"][key] = value_tag.get_text(strip=True)

            # Product images
            image_container = soup.find('div', class_='no-scrollbar relative flex max-h-full flex-col gap-4 overflow-y-scroll')
            if image_container:
                result["images"] = [
                    re.sub(r'/tr:[^/]+', '', img['src'])
                    for img in image_container.find_all('img')
                    if img.get('src')
                ]

            return convert_to_dict(result)

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                return {}
            time.sleep(SCROLL_PAUSE_TIME * (attempt + 1))

    return {}


def save_to_csv(data: List[Dict[str, Any]], filename: str) -> None:
    """Save data to CSV file with error handling."""
    if not data:
        return

    try:
        file_exists = os.path.isfile(filename)
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            if not file_exists:
                writer.writeheader()
            writer.writerows(data)
        logger.info(f"Saved {len(data)} items to {filename}")
    except Exception as e:
        logger.error(f"Failed to save CSV: {e}")


def get_product_urls_from_categorypage(driver: webdriver.Chrome) -> List[str]:
    """Extract product URLs from the current page."""
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    main_section = soup.find('div', class_=re.compile(
        r'no-scrollbar grid grid-cols-2 content-start gap-y-4 gap-x-2 px-2.5 py-4 '
        r'md:grid-cols-3 md:gap-x-3 md:p-3 lg:grid-cols-5 xl:grid-cols-6'
    ))

    return [
        BASE_URL + a['href']
        for a in main_section.find_all('a', href=True)
    ] if main_section else []


def update_csv_with_product_data(driver: webdriver.Chrome, csv_path: str) -> None:
    """Update CSV file with product page data."""
    try:
        df = pd.read_csv(csv_path)
        processed_count = 0
        total_rows = len(df)

        with tqdm(total=total_rows, initial=processed_count,
                 desc="Processing API Products", unit="product") as pbar:
            for i in range(processed_count, total_rows):
                product_url = df.at[i, 'product_url'] if 'product_url' in df.columns else None
                if pd.notna(product_url):
                    product_data = scrape_product_page(driver, product_url)
                    if product_data:
                        for field in ['nutritional_info', 'allergen', 'ingredients','dietary_preference']:
                            df.at[i, field] = product_data.get(field)

                df.to_csv(csv_path, index=False)
                pbar.update(1)

    except Exception as e:
        logger.error(f"[✖] Error processing file: {str(e)}")
        raise


def get_product_urls(driver: webdriver.Chrome) -> List[str]:
  """Scrape product URLs from an Amazon category page."""
  product_urls = []
  try:
    # Get page source after scrolling
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Extract product URLs
    product_elements = soup.find_all('a', {'class': 'ProductGridItem__overlay__IQ3Kw'})
    for product in product_elements:
      href = product.get('href')
      if href and '/dp/' in href:  # Ensuring it's a product link
        product_urls.append('https://www.amazon.in' + href)
    
    logger.info(f"Found {len(product_urls)} product URLs.")
    return product_urls
  except Exception as e:
    logger.error(f"Error while extracting product URLs: {e}")
    return []

def scrape_amazon_category(url: str, filename: str) -> None:
    """Main function to scrape a Amazon category."""
    driver = None
    try:
        driver = init_driver()
        logger.info(f"Starting scraping for URL: {url}")
        print(f"Starting scraping for URL: {url}")

        if not safe_get(driver, url):
            logger.error("Failed to load category page")
            return
        
        product_urls = get_product_urls(driver)
        logger.info(f"Found {len(product_urls)} initial product URLs")

        # capture_ajax_data(driver, filename)
        # time.sleep(SCROLL_PAUSE_TIME + random.random())
        #
        # if os.path.isfile(filename):
        #     update_csv_with_product_data(driver, filename)

        # total_rows = len(product_urls)
        # successful_scrapes = 0
        # 
        # with tqdm(total=total_rows, initial=successful_scrapes,
        #           desc="Processing Category Products", unit="product") as pbar:
        #     for i, product_url in enumerate(product_urls, 1):
        #         product_data = scrape_product_page(driver, product_url)
        #         pbar.set_postfix({
        #             'Current': product_url
        #         })
        #         if product_data:
        #             save_to_csv([product_data], filename)
        #             successful_scrapes += 1
        #             logger.info(f"Scraped product {i}/{len(product_urls)}")
        #         else:
        #             logger.error(f"Failed product {i}/{len(product_urls)}")
        # 
        #         pbar.update(1)
        # 
        # logger.info(f"Completed scraping. Saved {successful_scrapes} products")

    except KeyboardInterrupt:
        logger.info("\nScraping stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    category_url = input("Enter Amazon Category URL: ").strip()
    filename = input("Enter CSV filename: ").strip()
    scrape_amazon_category(category_url, f"{filename}.csv")