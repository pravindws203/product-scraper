"""
Jiomart Web Scraper Module
Author: Pravin Prajapati (Modified for Windows & enhanced robustness)

A modular scraper for Jiomart product data with:
- Warm-up navigation to avoid bot detection
- AJAX API data extraction
- Product page details scraping
- Self-contained logging
"""

# ============================================================================
# IMPORTS AND SYSTEM CONFIGURATION
# ============================================================================

import os
import re
import sys
import time
import json
import random
import locale
import requests
import platform
from tqdm import tqdm
from bs4 import BeautifulSoup
from logger_config import setup_logger
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urlunparse

from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)

# Fix encoding issues for Windows
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except locale.Error:
            pass


# ============================================================================
# MAIN JIOMART SCRAPER CLASS
# ============================================================================

class Jiomart:
    """
    Comprehensive Jiomart web scraper with anti-detection capabilities
    """

    def __init__(self, headless: bool = True, base_url: str = "https://www.jiomart.com", pincode: int = 380060):
        """Initialize the Jiomart scraper"""
        self._setup_logging()
        self.headless = headless
        self.driver = None
        self.pincode = pincode
        self.BASE_URL = base_url
        self._configure_constants()

    # ========================================================================
    # CONFIGURATION AND SETUP METHODS
    # ========================================================================

    def _setup_logging(self):
        """Configure logging settings using logger_config"""
        self.logger = setup_logger("JIOMART", "jiomart_scrapped.log")

    def _configure_constants(self):
        """Initialize scraper constants and configuration"""
        self.API_ENDPOINT = "http://10.0.101.117:1001/insert"

        self.USER_AGENTS = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edge/114.0.1823.67',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; AS; Desktop) like Gecko',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Brave/1.43.88',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Vivaldi/5.8.2945.60'
        ]

        # Timing and retry configuration
        self.MAX_SCROLL_RETRIES = 10
        self.SCROLL_PAUSE_TIME = 4
        self.MAX_RETRIES = 3
        self.PAGE_LOAD_TIMEOUT = 30
        self.REQUEST_TIMEOUT = 30
        self.ELEMENT_WAIT_TIMEOUT = 15

    def _get_random_user_agent(self) -> str:
        """Return a random user agent from predefined list"""
        return random.choice(self.USER_AGENTS)

    # ========================================================================
    # WEBDRIVER INITIALIZATION AND MANAGEMENT
    # ========================================================================

    def init_driver(self) -> bool:
        """Initialize and return a Chrome WebDriver"""
        try:
            chrome_driver_path_windows = r"C:\path\to\chromedriver.exe"
            chrome_driver_path_ubuntu = "/usr/local/bin/chromedriver"

            options = self._configure_chrome_options()
            service = self._get_chrome_service(chrome_driver_path_windows, chrome_driver_path_ubuntu)

            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(self.PAGE_LOAD_TIMEOUT)
            self.logger.info("WebDriver initialized successfully.")
            return True

        except WebDriverException as e:
            self.logger.error(f"FATAL: WebDriver initialization failed. Error: {e}")
            return False

    def _configure_chrome_options(self):
        """Configure Chrome options for the WebDriver"""
        options = webdriver.ChromeOptions()

        if self.headless:
            options.add_argument('--headless=new')

        # Basic options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--user-agent={self._get_random_user_agent()}')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')

        # Anti-detection options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Security and performance options
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-insecure-localhost')

        return options

    def _get_chrome_service(self, windows_path: str, ubuntu_path: str):
        """Get Chrome service based on operating system"""
        system_os = platform.system()

        if system_os == "Windows":
            if os.path.exists(windows_path):
                print("Using local ChromeDriver (Windows)")
                return Service(windows_path)
            else:
                print("Installing ChromeDriver (Windows)")
                return Service(ChromeDriverManager().install())

        elif system_os == "Linux":
            if os.path.exists(ubuntu_path):
                print("Using local ChromeDriver (Ubuntu/Linux)")
                return Service(ubuntu_path)
            else:
                print("Installing ChromeDriver (Ubuntu/Linux)")
                return Service(ChromeDriverManager().install())
        else:
            return Service(ChromeDriverManager().install())

    # ========================================================================
    # NAVIGATION AND INTERACTION UTILITIES
    # ========================================================================

    def _safe_click(self, element) -> bool:
        """Safely clicks an element using multiple strategies"""
        try:
            element.click()
            return True
        except ElementClickInterceptedException:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                try:
                    ActionChains(self.driver).move_to_element(element).click().perform()
                    return True
                except Exception as e:
                    self.logger.error(f"All click strategies failed: {e}")
                    return False

    def _safe_get(self, url: str) -> bool:
        """Safely navigate to URL with retries and bot detection handling"""
        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.info(f"Navigation attempt {attempt + 1}/{self.MAX_RETRIES}")
                self.driver.get(url)
                WebDriverWait(self.driver, self.ELEMENT_WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                if self._check_for_blocks():
                    self.logger.warning("Detected CAPTCHA or access block")
                    self._handle_homepage_popups()
                    time.sleep(random.uniform(15, 25))

                self.logger.info("Navigation completed successfully")
                return True

            except TimeoutException:
                self.logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
            except WebDriverException as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")

            if attempt == self.MAX_RETRIES - 1:
                self.logger.error(f"Failed to load {url} after {self.MAX_RETRIES} attempts")
                return False

            backoff_time = (2 ** attempt) + random.uniform(1, 3)
            self.logger.info(f"Waiting {backoff_time:.2f} seconds before retry...")
            time.sleep(backoff_time)

        return False

    # ========================================================================
    # POPUP AND MODAL HANDLING
    # ========================================================================

    def _handle_modal_overlays(self) -> bool:
        """Handles modal overlays and Jiomart 404 error redirects"""
        try:
            # Handle modal overlays
            overlay_selectors = [
                '.a-modal-scroller',
                '.a-popover-wrapper',
                '[data-action="a-modal-close"]',
                '.a-declarative[data-action="close"]'
            ]

            for selector in overlay_selectors:
                try:
                    overlay = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if overlay.is_displayed():
                        close_buttons = overlay.find_elements(By.CSS_SELECTOR,
                                                              'button[aria-label*="Close"], button[title*="Close"], .a-button-close')
                        for button in close_buttons:
                            if button.is_displayed():
                                self._safe_click(button)
                                self.logger.info("Closed modal overlay.")
                                time.sleep(1)
                                return True
                except (NoSuchElementException, StaleElementReferenceException):
                    continue

            # Handle 404 page redirects
            return self._handle_404_redirects()

        except Exception as e:
            self.logger.error(f"Error handling modal overlays: {e}")
        return False

    def _handle_404_redirects(self) -> bool:
        """Handle Jiomart 404 page redirects"""
        try:
            page_source = self.driver.page_source.lower()
            if ('looking for something?' in page_source and
                    'the web address you entered is not a functioning page' in page_source):
                try:
                    link = self.driver.find_element(By.CSS_SELECTOR, 'a[href="/ref=cs_404_link"]')
                    if link.is_displayed():
                        self._safe_click(link)
                        self.logger.warning("Detected 404 page. Redirecting to Jiomart home page...")
                        time.sleep(2)
                        return True
                except NoSuchElementException:
                    pass
        except Exception as e:
            self.logger.error(f"Error checking Jiomart 404 page: {e}")
        return False

    def _handle_homepage_popups(self) -> bool:
        """Handles popups on Jiomart homepage"""
        popup_handled = False
        wait = WebDriverWait(self.driver, 5)

        try:
            time.sleep(2)  # Let initial UI load

            # Handle Location Popup
            popup_handled |= self._handle_location_popup(wait)

            # Handle Delivery Popup & Enter Pincode
            popup_handled |= self._handle_delivery_popup(wait)

        except Exception as e:
            self.logger.error(f"Unexpected error while handling popups: {e}")

        return popup_handled

    def _handle_location_popup(self, wait) -> bool:
        """Handle location services popup"""
        try:
            popup = wait.until(EC.presence_of_element_located((By.ID, "location_popup")))
            style_attr = popup.get_attribute("style").strip().lower()

            if style_attr in ("", "display:block") or "display:block" in style_attr:
                self.logger.warning("Location popup visible. Closing...")
                close_btn = popup.find_element(By.ID, "btn_location_close_icon")
                close_btn.click()
                time.sleep(0.5)
                return True
            else:
                self.logger.info("Location popup not visible.")
        except TimeoutException:
            self.logger.info("No location popup found.")
        except Exception as e:
            self.logger.error(f"Error handling location popup: {e}")
        return False

    def _handle_delivery_popup(self, wait) -> bool:
        """Handle delivery popup and pincode entry"""
        try:
            delivery_popup = wait.until(EC.presence_of_element_located((By.ID, "delivery_popup")))
            self.logger.info("Delivery popup detected.")
            time.sleep(1)

            pin_input = wait.until(EC.presence_of_element_located((By.ID, "rel_pincode")))
            pin_input.clear()
            pin_input.send_keys(self.pincode)
            self.logger.info(f"Entered pincode: {self.pincode}")

            apply_btn = delivery_popup.find_element(By.ID, "btn_pincode_submit")
            time.sleep(random.uniform(1, 2))
            apply_btn.click()
            self.logger.info("Submitted pincode.")

            wait.until(EC.invisibility_of_element_located((By.ID, "delivery_popup")))
            self.logger.info("Delivery popup closed.")
            return True

        except TimeoutException:
            self.logger.info("No delivery popup found.")
        except Exception as e:
            self.logger.error(f"Error handling delivery popup: {e}")
        return False

    # ========================================================================
    # BOT DETECTION AND SECURITY
    # ========================================================================

    def _check_for_blocks(self) -> bool:
        """Detects if the page is blocked by CAPTCHA, access denial, or 404 errors"""
        try:
            page_source = self.driver.page_source.lower()

            # Page source block indicators
            block_indicators = [
                'captcha', 'access denied', 'unusual traffic',
                'enter the characters', 'i am not a robot', 'recaptcha'
            ]

            if any(indicator in page_source for indicator in block_indicators):
                self.logger.warning("Page source contains block indicators.")
                return True

            # Jiomart 404 error block
            if ('looking for something?' in page_source and
                    'the web address you entered is not a functioning page' in page_source):
                self.logger.warning("Jiomart 404 page detected.")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error during block check: {e}")
            return False

    def _perform_warmup_and_get(self, target_url: str) -> bool:
        """Performs safe navigation protocol with warmup"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("STARTING SAFE NAVIGATION PROTOCOL")
            self.logger.info("=" * 60)

            # Step 1: Navigate to homepage
            self.logger.info(f"Step 1/4: Navigating to Jiomart homepage: {self.BASE_URL}")
            if not self._navigate_to_homepage():
                return False

            # Step 2: Handle popups
            self.logger.info("Step 2/4: Checking for popups and dialogs")
            popup_handled = self._handle_homepage_popups()
            if popup_handled:
                self.logger.info("Popup dialogs handled successfully")

            # Step 3: Human behavior simulation
            self._simulate_human_behavior()

            # Step 4: Navigate to target
            self.logger.info(f"Step 4/4: Navigating to target URL: {target_url}")
            return self._navigate_to_target(target_url)

        except Exception as e:
            self.logger.error(f"Navigation protocol failed: {e}", exc_info=True)
            return False

    def _navigate_to_homepage(self) -> bool:
        """Navigate to homepage and verify load"""
        try:
            self.driver.get(self.BASE_URL)
            WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self.logger.info("Homepage loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load homepage: {e}")
            return False

    def _simulate_human_behavior(self):
        """Simulate human browsing behavior"""
        warmup_delay = random.randint(5, 8)
        self.logger.info(f"Step 3/4: Mimicking human behavior - waiting {warmup_delay:.2f} seconds")
        time.sleep(warmup_delay)

    def _navigate_to_target(self, target_url: str) -> bool:
        """Navigate to target URL and verify success"""
        try:
            self.driver.get(target_url)
            WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            post_load_delay = random.uniform(2, 4)
            self.logger.info(f"Waiting {post_load_delay:.2f} seconds for dynamic content")
            time.sleep(post_load_delay)

            current_url = self.driver.current_url
            if "jiomart" in current_url.lower():
                self.logger.info("Successfully navigated to target page.")
                self.logger.info("NAVIGATION PROTOCOL COMPLETED SUCCESSFULLY")
                return True
            else:
                self.logger.error("Navigation failed - not on Jiomart domain")
                return False

        except Exception as e:
            self.logger.error(f"Failed to navigate to target: {e}")
            return False

    # ========================================================================
    # PAGE INTERACTION AND SCROLLING
    # ========================================================================

    def click_out_of_stock(self):
        """Click the first div inside #in_stock_filter list item (Include Out of stock filter)"""
        try:
            container = WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "in_stock_filter"))
            )
            self.logger.debug("Found #in_stock_filter container.")

            time.sleep(self.SCROLL_PAUSE_TIME + random.random())

            first_div = WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#in_stock_filter ul li:first-child > div"))
            )

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_div)

            first_div.click()
            self.logger.info("✅ 'Include Out of stock' filter clicked via div.")

        except Exception as e:
            self.logger.error("Error clicking out-of-stock checkbox via div", exc_info=True)

    def _load_all_products(self) -> None:
        """Scrolls down the page to load all products"""
        time.sleep(self.SCROLL_PAUSE_TIME + random.random())
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        footer = self.driver.find_element("tag name", "footer")
        footer_height = footer.size['height']
        retries = 0

        while retries < self.MAX_SCROLL_RETRIES:
            try:
                scroll_position = last_height - footer_height - random.randint(600, 700)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(self.SCROLL_PAUSE_TIME + random.randint(3, 6))

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
        """Clicks the 'Next' button for pagination"""
        try:
            next_btn = self.driver.find_element(
                By.CSS_SELECTOR,
                'a.s-pagination-item.s-pagination-next:not(.s-pagination-disabled)'
            )
            self.logger.info("Clicking 'Next' page button...")
            next_btn.click()

            WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT).until(
                EC.staleness_of(next_btn)
            )
            return True

        except (NoSuchElementException, TimeoutException):
            self.logger.info("No more 'Next' pages or button not found. Ending pagination.")
            return False

    # ========================================================================
    # DATA EXTRACTION METHODS
    # ========================================================================

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
                        value = self._extract_value_from_tag(value_tag)
                        product_info[key] = value

                except Exception as e:
                    self.logger.error(f"Error extracting product details: {e}")
                    continue

        return product_info

    def _extract_value_from_tag(self, value_tag):
        """Extract value from a table cell, handling images"""
        if value_tag.img:
            img_tag = value_tag.find('img')
            img_src = img_tag.get('src', '')
            if "icon-veg" in img_src:
                return "Veg"
            elif "icon-nonveg" in img_src:
                return "Non Veg"
            else:
                return img_tag.get('alt', '').strip()
        else:
            return value_tag.get_text(strip=True)

    def _get_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract product images from page"""
        try:
            product_media = soup.find("div", class_="product-media")
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

    def get_product_urls(self, url: str) -> List[str]:
        """Scrapes product URLs from category pages"""
        if not self._safe_get(url):
            self.logger.error(f"Failed to load product page {url}. Skipping.")
            return []

        product_urls = set()
        page_count = 1

        while True:
            self.logger.info(f"--- Scraping product URLs from page {page_count} ---")
            self.click_out_of_stock()
            self._load_all_products()
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            for a_tag in soup.select("ol.ais-InfiniteHits-list li a[href]"):
                href = a_tag["href"]
                full_url = f"https://www.jiomart.com{href}" if href.startswith("/") else href
                product_urls.add(full_url)

            self.logger.info(f"Total unique URLs collected so far: {len(product_urls)}")

            if not self.click_next_button():
                break
            page_count += 1
            time.sleep(random.uniform(2, 4))

        self.logger.info(f"Total unique product URLs collected: {len(product_urls)}")
        return list(product_urls)

    def get_product_details(self, url: str) -> Dict[str, Any]:
        """Extract detailed product information from product page"""
        for attempt in range(self.MAX_RETRIES):
            try:
                if not self._safe_get(url):
                    continue

                time.sleep(random.randint(2, 5))
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')

                return self._parse_product_data(soup, url)

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == self.MAX_RETRIES - 1:
                    return {}
                time.sleep(random.randint(2, 5))

        return {}

    def _parse_product_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Parse product data from soup"""
        # Extract basic product information
        product_full_name = soup.find('div', id='pdp_product_name').get_text(strip=True)
        price_span = soup.select_one("#price_section .product-price span.jm-heading-xs")
        price = price_span.get_text(strip=True) if price_span else None

        # Extract additional details
        images = self._get_images(soup)
        details = self._extract_product_details(soup)

        # Build product data structure
        product = {
            "product_url": url,
            "name": product_full_name.split('|')[0].strip(),
            "brand_name": details.get('brand', None),
            "mrp": price,
            "images": {"image_urls": images},
            "status": "raw",
            "source": "jiomart",
            "mass_measurement_unit": (self.get_mass_measurement_unit(details.get('net_quantity')) or
                                      self.get_mass_measurement_unit(details.get('net_weight'))),
            "details": details,
            **details
        }

        return product

    # ========================================================================
    # DATA PROCESSING AND UTILITY METHODS
    # ========================================================================

    def filltered_scrapped_data(self, scraped_data):
        """Filter and clean the scraped data to remove unwanted fields"""
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

    def get_mass_measurement_unit(self, unit: str):
        """Extract and standardize mass or volume measurement unit"""
        if not unit:
            return None

        cleaned_unit = re.sub(r'\d+(\.\d+)?', '', str(unit)).strip().lower()

        unit_mappings = {
            'grams': ['gram', 'grams', 'kilogram', 'kilograms', 'kg', 'g'],
            'millilitre': ['ml', 'millilitre', 'millilitres', 'milliliter',
                           'milliliters', 'liter', 'litre', 'liters', 'litres', 'l']
        }

        for standard_unit, variations in unit_mappings.items():
            if any(var in cleaned_unit for var in variations):
                return standard_unit.upper()

        return None

    def get_diet(self, diet: str):
        """Standardize diet information"""
        if not diet:
            return None
        diet = diet.lower()
        if 'vegan' in diet:
            return "Vegan"
        if 'non veg' in diet:
            return 'Non Veg'
        if 'vegetarian' in diet or 'veg' in diet:
            return 'Veg'
        return None

    def extract_image_urls_text(self, image_urls) -> str:
        """Convert image URLs list to JSON string"""
        if not image_urls or not isinstance(image_urls, list):
            return ""
        valid_urls = [url for url in image_urls if isinstance(url, str) and url.startswith("http")]
        return json.dumps({"image_urls": valid_urls}, indent=2) if valid_urls else ""

    # ========================================================================
    # API INTEGRATION METHODS
    # ========================================================================

    def _send_to_api(self, product_data: Dict[str, Any]) -> bool:
        """Send product data to API endpoint"""
        try:
            response = requests.post(
                self.API_ENDPOINT,
                json=self.filltered_scrapped_data(product_data),
                timeout=self.REQUEST_TIMEOUT
            )
            if response.status_code == 200:
                inserted_id = response.json().get('id', 'N/A')
                self.logger.info(f"Successfully inserted product. ID: {inserted_id}")
                return True
            else:
                self.logger.error(f"API Error: Status {response.status_code}, Response: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network Error: Could not connect to API endpoint. Error: {e}")
            return False

    # ========================================================================
    # MAIN SCRAPING METHODS
    # ========================================================================

    def scrape_category(self, category_url: str) -> None:
        """Main method to scrape an entire Jiomart category"""
        if not self.init_driver():
            return

        try:
            if not self._perform_warmup_and_get(category_url):
                self.logger.error("Scraping aborted due to navigation failure.")
                return

            self.logger.info(f"Starting scraping for URL: {category_url}")
            product_urls = self.get_product_urls(category_url)

            if not product_urls:
                self.logger.error("No product URLs found. Exiting.")
                return

            self.logger.info(f"Found {len(product_urls)} total product URLs to scrape.")
            self._process_product_urls(product_urls)

        except KeyboardInterrupt:
            self.logger.info("\nScraping stopped by user.")
        except Exception as e:
            self.logger.critical(f"A critical error occurred: {e}", exc_info=True)
        finally:
            self._cleanup()

    def scrape_product(self, product_url: str) -> None:
        """Main method to scrape a single Jiomart product"""
        if not self.init_driver():
            return

        try:
            if not self._perform_warmup_and_get(product_url):
                self.logger.error("Scraping aborted due to navigation failure.")
                return

            product_data = self.get_product_details(product_url)
            if product_data:
                self.logger.info(f"Scraped data: {product_data}")
                self._send_to_api(product_data)
            else:
                self.logger.error(f"Failed to scrape any details for product: {product_url}")

            self.logger.info("Single product scraping finished.")

        except KeyboardInterrupt:
            self.logger.info("\nScraping stopped by user.")
        except Exception as e:
            self.logger.critical(f"A critical error occurred: {e}", exc_info=True)
        finally:
            self._cleanup()

    def _process_product_urls(self, product_urls: List[str]):
        """Process list of product URLs with progress tracking"""
        with tqdm(total=len(product_urls), desc="Jiomart Category Scraping", unit="products") as pbar:
            for url in product_urls:
                product_data = self.get_product_details(url)
                if product_data:
                    if self._send_to_api(product_data):
                        pbar.set_postfix({"Status": "Success"})
                    else:
                        pbar.set_postfix({"Status": "API Error"})
                else:
                    self.logger.warning(f"Failed to scrape details for product: {url}")
                    pbar.set_postfix({"Status": "Scrape Failed"})

                pbar.update(1)
                time.sleep(random.uniform(2, 5))

        self.logger.info("Scraping finished.")

    def _cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            self.logger.info("WebDriver closed.")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("--- Jiomart Scraper ---")
    url = input("Enter Jiomart Category or Product URL: ").strip()

    if "/p/groceries/" in url:
        is_product = True
        print("Detected a Product URL.")
    else:
        is_product = False
        print("Detected a Category URL.")

    parsed = urlparse(url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"

    headless_choice = input("Run in headless mode (browser not visible)? (Y/n): ").strip().lower()
    run_headless = headless_choice != 'n'

    pincode_input = 380060
    # Pincode validation loop
    while True:
        try:
            pincode_input = input("Enter Pincode (6 digits): ").strip()

            # Check if input contains only digits
            if not pincode_input.isdigit():
                print("❌ Error: Pincode should contain only numbers. Please try again.")
                continue

            # Check if exactly 6 digits
            if len(pincode_input) != 6:
                print(
                    f"❌ Error: Pincode should be exactly 6 digits. You entered {len(pincode_input)} digits. Please try again.")
                continue

            # Convert to integer after validation
            pincode = int(pincode_input)
            print(f"✅ Valid pincode entered: {pincode}")
            break

        except ValueError:
            print("❌ Error: Invalid input. Please enter a valid 6-digit pincode.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            exit()

    jiomart_scraper = Jiomart(headless=run_headless, base_url=base_domain, pincode=pincode_input)

    if is_product:
        jiomart_scraper.scrape_product(product_url=url)
    else:
        jiomart_scraper.scrape_category(category_url=url)
