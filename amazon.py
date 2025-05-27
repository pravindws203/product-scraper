"""
Amazon Web Scraper - Complete Version
Author: Pravin Prajapati
This script scrapes product data from Amazon website including:
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
BASE_URL = "https://www.amazon.in/"
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

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


def safe_get(driver: webdriver.Chrome, url: str) -> bool:
    """Safely navigate to URL with retries and proper waiting."""
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Attempt {attempt + 1} to load {url}")
            driver.get(url)

            # selector = "div[class*='ProductGridItem__overlay__IQ3Kw'], div[id='important-information']"
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
      
      
def clean_text(text):
    # Remove invisible unicode characters and extra whitespace
    return re.sub(r'[\u200e\u200f]', '', text).strip()

def extract_product_details(soup):
    details = {
        "asin": None,
        "weight": None,
        "brand": None,
        "additives": None,
        "net_quantity": None,
        "allergen_information": None,
        "ingredients": None,
        "ingredient_type	": None,
        'generic_name': None
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
    
    additional_information = soup.select('#productDetails_detailBullets_sections1 tr')
    
    for row in additional_information:
        key_el = row.find('th')
        value_el = row.find('td')
        if key_el and value_el:
            key = clean_text(key_el.get_text())
            value = clean_text(value_el.get_text())

            key_lower = key.lower().strip()
            if key_lower == "asin":
                details["asin"] = value
            elif key_lower == "item weight":
                if not details["weight"]:
                    details["weight"] = value
            elif key_lower == "generic name":
                details["generic_name"] = value
            
    return details

def extract_ingredients(soup):
    ingredients = None
    sections = soup.select('#important-information .content')
    for section in sections:
        heading = section.find('h4')
        if heading and 'Ingredients' in heading.text:
            paragraphs = section.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    ingredients = text
                    break
    return ingredients
   
def get_images(soup):
    try:
        scripts = soup.find_all("script")
        image_data_script = None
        for script in scripts:
            if str(script) and "colorImages" in str(script):
                image_data_script = script.string
                break
        
        if image_data_script:
            # Try extracting the JSON array of images
            matches = re.findall(r'^.*colorImages.*$', image_data_script, re.MULTILINE)
            if matches:
                json_str = matches[0]
                json_str = json_str.replace("'", '"')
                return re.findall(r'"hiRes"\s*:\s*"([^"]+)"', json_str)
    except Exception as e:
        logger.error(f"Error extracting images: {e}")
        return []
    
def get_product_details(driver: webdriver.Chrome, url: str) -> Dict[str, Any]:
    """Extract product URLs from the current page."""
    for attempt in range(MAX_RETRIES):
        try:
            if not safe_get(driver, url):
                continue
            time.sleep(SCROLL_PAUSE_TIME + random.random())
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            details = extract_product_details(soup)
            
            def safe_find(by, value):
                try:
                    return driver.find_element(by, value).text.strip()
                except:
                    return None
            
            images = get_images(soup)
            image_fields = {
                f'image_url_{i + 1}': images[i] if i < len(images) else ''
                for i in range(15)
            }
            
            product = {
                "product_url": url,
                "asin": details.get('asin'),
                "name": safe_find(By.ID, 'productTitle'),
                "price": safe_find(By.CLASS_NAME, 'a-price-whole') or safe_find(By.CLASS_NAME, 'a-price'),
                "brand": details.get('brand'),
                "barcode": None,
                'generic_name': details.get('generic_name'),
                'ingredient_type': details.get('ingredient_type'),
                "ingredients": extract_ingredients(soup) or details.get('ingredients'),
                "allergen_info": details.get('allergen_information'),
                "weight": details.get('weight'),
                "additives": details.get('additives'),
                "unit_count": details.get('net_quantity'),
                **image_fields,
            }
            
            return product
        
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                return {}
            time.sleep(SCROLL_PAUSE_TIME * (attempt + 1))
    
    return {}


def load_all_prdoucts(driver: webdriver.Chrome) -> None:
    """Load all products on the page by scrolling."""
    time.sleep(SCROLL_PAUSE_TIME + random.random())
    last_height = driver.execute_script("return document.body.scrollHeight")
    footer_height = driver.execute_script("return document.getElementById('navFooter').offsetHeight;")
    retries = 0
    
    while retries < MAX_SCROLL_RETRIES:
        try:
            # Wait until the button is present and clickable (up to 10 seconds)
            wait = WebDriverWait(driver, 10)
            button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.Button__secondary__sMAVa")))
            button.click()
            driver.execute_script(f"window.scrollTo(0, {last_height - footer_height - random.randint(600, 700)});")
            time.sleep(SCROLL_PAUSE_TIME + random.random())
            new_height = driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                retries += 1
            else:
                last_height = new_height
                retries = 0

        except Exception as e:
            logger.error(f"Error during scrolling: {e}")
            break
def get_product_urls(driver: webdriver.Chrome) -> List[str]:
    """Scrape product URLs from an Amazon category page."""
    load_all_prdoucts(driver)
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
        
        # Wait for the page to load
        product_urls = get_product_urls(driver)
        # product_urls = ["https://www.amazon.in/Tang-Orange-Instant-Drink-Mix/dp/B078PLFYC5?ref_=ast_sto_dp&th=1",]
        logger.info(f"Found {len(product_urls)} initial product URLs")
        print(f"Found {len(product_urls)} initial product URLs")
        
        total_rows = len(product_urls)
        successful_scrapes = 0

        with tqdm(total=total_rows, initial=successful_scrapes,
                  desc="Processing Category Products", unit="product") as pbar:
            for i, product_url in enumerate(product_urls, 1):
                pbar.set_postfix({'Current': product_url})
                product_data = get_product_details(driver, product_url)
                if product_data:
                    save_to_csv([product_data], filename)
                    successful_scrapes += 1
                    logger.info(f"Scraped product {i}/{len(product_urls)}")
                else:
                    logger.error(f"Failed product {i}/{len(product_urls)}")
                  
                time.sleep(SCROLL_PAUSE_TIME + random.randint(2,6))
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
    category_url = input("Enter Amazon Category URL: ").strip()
    filename = input("Enter CSV filename: ").strip()
    # amazon_url = "https://www.amazon.in/stores/page/0499AE6D-F56B-4F69-977C-310CC92EAABE?ingress=2&visitId=48ef0498-80b0-4857-857b-9d67eaa81e07&ref_=ast_bln"  # replace with your product URL
    scrape_amazon_category(category_url,f"{filename}.csv")
