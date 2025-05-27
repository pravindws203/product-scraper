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
        logging.FileHandler('logs/hyugalife_scraper.log'),
    ]
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://hyugalife.com"
API_DOMAIN = "api.hyugalifenow.com"
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
PAGES = 10


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

            selector = "div[class*='listing-container grid grid-cols-1'], div[class*='product-detail-container h-full bg-white'], div[id='productInformationL4']"
            WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, selector)))
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


def safe_price_format(price: Any) -> str:
    """Format price by removing last 2 digits if possible."""
    try:
        if price and len(str(price)) > 2:
            return str(price)[:-2]
        return str(price)
    except Exception:
        return str(price)

def extract_specific_product_info(product_information):
    result = {
        "allergen": None
    }

    for item in product_information:
        label = item.get("attribute_code", "").strip().lower()
        if label == "allergens":
            result["allergen"] = item.get("value")

    return result

def extract_product_data(json_data, product_url) -> List[Dict[str, Any]]:
    """Extract product data from JSON API response."""
    try:
        data = json_data.get('data').get('data')
        products = []


        images = [
            'https://assets.hyugalife.com/catalog/product' + image.get('file')
            for image in data.get('media_gallery', [])
            if image.get('file')
        ]

        image_fields = {
            f'image_url_{i + 1}': images[i] if i < len(images) else ''
            for i in range(10)
        }
        product_information = extract_specific_product_info(data.get('product_information'))
        products.append({
            'product_id': data.get('id', {}),
            'sku': data.get('sku', {}),
            'name': data.get('name'),
            'brand': data.get('brand').get('label'),
            'product_url': product_url,
            'barcode': None,
            'ingredients': data.get('ingredients'),
            'allergen': product_information.get('allergen'),
            'price': data.get('price'),
            'dietary_preference': data.get('dietary_preference'),
            'unit_of_measure': data.get('pack_size'),
            'weight_in_gms': data.get('item_weight'),
            'packsize': data.get('size'),
            **image_fields,
        })
        return products
    except Exception as e:
        logger.error(f"JSON parse error: {e}")
        return []


def generate_product_url(name: str, product_id: str) -> str:
    """Generate product URL from product name and ID."""
    if not product_id:
        return ''
    product_name = re.sub(r'[^\w-]+', '-', name).strip('-').lower()
    return f"{BASE_URL}/pn/{product_name}/pvid/{product_id}"

def fetch_api_data(product_key: str, product_url: str) -> Optional[Dict]:
    """Fetch data from Blinkit API with headers and retry logic"""
    url = f"https://hyuga-catalog-service.pratech.live/v1/catalog/product/slug/{product_key}"
    scraper = cloudscraper.create_scraper()

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate, br"
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = scraper.get(url, headers=headers)
            if response.status_code == 200:
                time.sleep(SCROLL_PAUSE_TIME + random.randint(2,3))
                return extract_product_data(response.json(), product_url)
            else:
                logger.warning(f"Non-200 response (status {response.status_code}), retrying...")
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
        time.sleep(2 ** attempt)

    logger.error(f"All {MAX_RETRIES} attempts failed for product_key: {product_key}")
    return None

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
        r'listing-container grid grid-cols-1'
    ))

    return [
        BASE_URL + a['href']
        for a in main_section.find_all('a', href=True)
    ] if main_section else []

def set_page_param(url, page_value):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params['page'] = [str(page_value)]
    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse(parsed_url._replace(query=new_query))
    return new_url

def product_key_get(url):
    product_key = urlparse(url).path.rstrip('/').split('/')[-1]
    return product_key

def scrape_hyugalife_category(url: str, filename: str) -> None:
    """Main function to scrape a Hyugalife category."""
    driver = None
    try:
        driver = init_driver()
        logger.info(f"Starting scraping for URL: {url}")
        print(f"Starting scraping for URL: {url}")

        
        product_urls = []
        for i in range(PAGES):
            if not safe_get(driver, str(set_page_param(url, i + 1))):
                logger.error("Failed to load category page")
                break

            time.sleep(SCROLL_PAUSE_TIME + random.random())

            logger.info(f"Processing page {i + 1} of {PAGES}")
            product_urls += get_product_urls_from_categorypage(driver)


        logger.info(f"Found {len(product_urls)} initial product URLs")
        
        total_rows = len(product_urls)
        successful_scrapes = 0

        with tqdm(total=total_rows, initial=successful_scrapes,
                  desc="Processing Category Products", unit="product") as pbar:
            for i, product_url in enumerate(product_urls, 1):
                product_data = fetch_api_data(product_key_get(product_url), product_url)
                if product_data:
                    save_to_csv(product_data, filename)
                    successful_scrapes += 1
                    logger.info(f"Scraped product {i}/{len(product_urls)}")
                else:
                    logger.error(f"Failed product {i}/{len(product_urls)}")
                
                pbar.set_postfix({
                    'Current': product_url
                })
                pbar.update(1)

        logger.info(f"Completed scraping. Saved {successful_scrapes} products")

    except KeyboardInterrupt:
        logger.info("\nScraping stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    category_url = input("Enter Hyugalife Category URL: ").strip()
    filename = input("Enter CSV filename: ").strip()
    scrape_hyugalife_category(category_url, f"{filename}.csv")