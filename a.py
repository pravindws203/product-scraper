"""
Amazon Web Scraper Module
Author: Pravin Prajapati (Modified for Windows & enhanced robustness)

A modular scraper for Amazon product data with:
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
import warnings
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

warnings.filterwarnings("ignore", category=UserWarning, module=".*pkg_resources.*")

# ============================================================================
# MAIN AMAZON SCRAPER CLASS
# ============================================================================

class Amazon:
    """
    Comprehensive Amazon web scraper with anti-detection capabilities
    """

    def __init__(self, headless: bool = True, base_url: str = "https://www.amazon.in/"):
        """Initialize the Amazon scraper"""
        self._setup_logging()
        self.headless = headless
        self.driver = None
        self.BASE_URL = base_url
        self._configure_constants()

    # ========================================================================
    # CONFIGURATION AND SETUP METHODS
    # ========================================================================

    def _setup_logging(self):
        """Configure logging settings using logger_config"""
        self.logger = setup_logger("AMAZON", "amazon_scraper.log")

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
        self.MAX_SCROLL_RETRIES = 5
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
        """Handles modal overlays and Amazon 404 error redirects"""
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
        """Handle Amazon 404 page redirects"""
        try:
            page_source = self.driver.page_source.lower()
            if ('looking for something?' in page_source and
                'the web address you entered is not a functioning page' in page_source):
                try:
                    link = self.driver.find_element(By.CSS_SELECTOR, 'a[href="/ref=cs_404_link"]')
                    if link.is_displayed():
                        self._safe_click(link)
                        self.logger.warning("Detected 404 page. Redirecting to Amazon home page...")
                        time.sleep(2)
                        return True
                except NoSuchElementException:
                    pass
        except Exception as e:
            self.logger.error(f"Error checking Amazon 404 page: {e}")
        return False

    def _handle_homepage_popups(self) -> bool:
        """Handles various popups that may appear on Amazon homepage"""
        popup_handled = False

        try:
            time.sleep(2)
            popup_selectors = self._get_popup_selectors()
            wait = WebDriverWait(self.driver, 5)

            for popup_type in popup_selectors:
                popup_name = popup_type['name']
                self.logger.info(f"Checking for {popup_name} popup...")

                for selector in popup_type['selectors']:
                    try:
                        if selector.startswith('button:contains') or selector.startswith('span'):
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector.split(':')[0])
                            for element in elements:
                                if selector.split('"')[1] in element.text:
                                    self.logger.info(f"Found {popup_name} button: '{element.text}'")
                                    self._safe_click(element)
                                    popup_handled = True
                                    time.sleep(2)
                                    break
                        else:
                            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                            if element:
                                self.logger.info(f"Found {popup_name} button")
                                self._safe_click(element)
                                popup_handled = True
                                time.sleep(2)
                                break

                    except (TimeoutException, NoSuchElementException):
                        continue  # Try next selector
                    except Exception as e:
                        self.logger.debug(f"Error with selector {selector}: {e}")
                        continue

                if popup_handled:
                    self.logger.info(f"Successfully handled {popup_name}")
                    break

            if not popup_handled:
                self._handle_modal_overlays()

        except Exception as e:
            self.logger.error(f"Error while handling popups: {e}")

        return popup_handled

    def _get_popup_selectors(self) -> List[Dict]:
        """Streamlined popup selector configurations with most common ones first"""
        return [
            {
                'name': 'Continue Shopping',
                'selectors': [
                    'button.a-button-text',
                    'input[aria-label*="Continue shopping"]',
                    'button[aria-label*="Continue shopping"]',
                    'input[value*="Continue shopping"]',
                    'a[title*="Continue shopping"]',
                    '.a-button-input[aria-label*="Continue"]',
                    'input[name="continue-shopping"]'
                ]
            },
            {
                'name': 'Location Popup',
                'selectors': [
                    'button[aria-label*="Dismiss"]',
                    'button[data-action-type="DISMISS"]',
                    'span.a-button-text:contains("Not now")',
                    'input[aria-label*="Not now"]'
                ]
            },
            {
                'name': 'Cookie Consent',
                'selectors': [
                    'input[id*="accept-cookies"]',
                    'button[id*="accept-cookies"]',
                    'input[aria-label*="Accept cookies"]',
                    'button:contains("Accept")'
                ]
            },
            {
                'name': 'Generic Close',
                'selectors': [
                    'button[aria-label*="Close"]',
                    'button[title*="Close"]',
                    'span.a-icon-alt:contains("Close")',
                    'button.a-button-close'
                ]
            }
        ]

    def _handle_popup_selector(self, selector: str, popup_name: str, wait) -> bool:
        """Handle individual popup selector"""
        try:
            if selector.startswith('button:contains') or selector.startswith('span'):
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector.split(':')[0])
                for element in elements:
                    if selector.split('"')[1] in element.text:
                        self.logger.info(f"Found {popup_name} button: '{element.text}'")
                        self._safe_click(element)
                        time.sleep(2)
                        return True
            else:
                element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                if element:
                    self.logger.info(f"Found {popup_name} button")
                    self._safe_click(element)
                    time.sleep(2)
                    return True
        except Exception as e:
            self.logger.debug(f"Error with selector {selector}: {e}")
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

            # Amazon 404 error block
            if ('looking for something?' in page_source and
                'the web address you entered is not a functioning page' in page_source):
                self.logger.warning("Amazon 404 page detected.")
                return True

            # Check for popup elements
            return self._check_popup_elements()

        except Exception as e:
            self.logger.error(f"Error during block check: {e}")
            return False

    def _check_popup_elements(self) -> bool:
        """Fast popup element detection without timeouts"""
        priority_selectors = [
            'input[aria-label*="Continue shopping"]',
            'button[aria-label*="Continue shopping"]',
            'button[aria-label*="Dismiss"]',
            'iframe[title="reCAPTCHA"]',
            'div.g-recaptcha'
        ]

        try:
            for selector in priority_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed():
                        self.logger.debug(f"Blocking element detected: {selector}")
                        return True
            return False
        except Exception as e:
            self.logger.debug(f"Error in popup element check: {e}")
            return False

    def _perform_warmup_and_get(self, target_url: str) -> bool:
        """Performs safe navigation protocol with warmup"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("STARTING SAFE NAVIGATION PROTOCOL")
            self.logger.info("=" * 60)

            # Step 1: Navigate to homepage
            self.logger.info(f"Step 1/4: Navigating to Amazon homepage: {self.BASE_URL}")
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
        warmup_delay = random.uniform(5, 8)
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
            if "amazon" in current_url.lower():
                self.logger.info("Successfully navigated to target page.")
                self.logger.info("NAVIGATION PROTOCOL COMPLETED SUCCESSFULLY")
                return True
            else:
                self.logger.error("Navigation failed - not on Amazon domain")
                return False

        except Exception as e:
            self.logger.error(f"Failed to navigate to target: {e}")
            return False

    # ========================================================================
    # TEXT PROCESSING AND UTILITY METHODS
    # ========================================================================

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text by removing special characters and extra whitespace"""
        if not text:
            return ""
        return re.sub(r'[\u200e\u200f]', '', text).strip()

    def get_mass_measurement_unit(self, unit: str):
        """Extract and standardize mass or volume measurement unit"""
        if not unit:
            return None
        cleaned_unit = re.sub(r'[\d.]+', '', str(unit)).strip().lower()
        unit_mappings = {
            'GRAMS': ['gram', 'g', 'kg', 'kilogram'],
            'MILLILITRE': ['ml', 'millilitre', 'liter', 'l', 'litre']
        }
        for standard, variations in unit_mappings.items():
            if any(var in cleaned_unit for var in variations):
                return standard
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
    # PAGE INTERACTION AND SCROLLING
    # ========================================================================

    def _load_all_products(self) -> None:
        """Scrolls down the page to load all products"""
        time.sleep(self.SCROLL_PAUSE_TIME + random.random())
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        footer_height = self.driver.execute_script(
            "return document.getElementById('navFooter') ? document.getElementById('navFooter').offsetHeight : 0;")
        retries = 0

        while retries < self.MAX_SCROLL_RETRIES:
            try:
                wait = WebDriverWait(self.driver, 10)
                scroll_position = last_height - footer_height - random.randint(600, 700)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(self.SCROLL_PAUSE_TIME + random.randint(3, 6))

                new_height = self.driver.execute_script("return document.body.scrollHeight")

                # Try to click load more button if available
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
        details = {
            "asin": None, "weight": None, "brand": None, "additives": None,
            "net_quantity": None, "allergen_information": None, "ingredients": None,
            "ingredient_type": None, 'generic_name': None
        }

        # Extract from technical details table
        self._extract_technical_details(soup, details)

        # Extract from additional information section
        self._extract_additional_information(soup, details)

        return details

    def _extract_technical_details(self, soup: BeautifulSoup, details: Dict[str, str]):
        """Extract technical details from product page"""
        rows = soup.select('#productDetails_techSpec_section_1 tr')
        for row in rows:
            key_el = row.find('th')
            value_el = row.find('td')
            if key_el and value_el:
                key = self._clean_text(key_el.get_text()).lower()
                value = self._clean_text(value_el.get_text())
                self._process_detail_row(key, value, details)

    def _extract_additional_information(self, soup: BeautifulSoup, details: Dict[str, str]):
        """Extract additional information from product page"""
        additional_info = soup.select('#productDetails_detailBullets_sections1 tr')
        for row in additional_info:
            key_el = row.find('th')
            value_el = row.find('td')
            if key_el and value_el:
                key = self._clean_text(key_el.get_text()).lower().strip()
                value = self._clean_text(value_el.get_text())
                self._process_detail_row(key, value, details)

    def get_technical_details(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Get technical details as dictionary"""
        details = {}
        try:
            rows = soup.select('#productDetails_techSpec_section_1 tr')
            for row in rows:
                key_el = row.find('th')
                value_el = row.find('td')
                if key_el and value_el:
                    key = self._clean_text(key_el.get_text()).lower()
                    value = self._clean_text(value_el.get_text())
                    details[key] = value
            return details
        except Exception as e:
            self.logger.error(f"Error extracting technical details: {e}")
            return details

    def get_additional_information(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Get additional information as dictionary"""
        details = {}
        try:
            additional_info = soup.select('#productDetails_detailBullets_sections1 tr')
            for row in additional_info:
                key_el = row.find('th')
                value_el = row.find('td')
                if key_el and value_el:
                    key = self._clean_text(key_el.get_text()).lower()
                    value = self._clean_text(value_el.get_text())
                    details[key] = value
            return details
        except Exception as e:
            self.logger.error(f"Error extracting additional information: {e}")
            return details

    def _process_detail_row(self, key: str, value: str, details: Dict[str, str]):
        """Process individual detail row and map to appropriate fields"""
        mapping = {
            "weight": "weight", "item weight": "weight",
            "brand": "brand", "additives": "additives",
            "net quantity": "net_quantity", "allergen information": "allergen_information",
            "ingredient type": "ingredient_type", "ingredients": "ingredients",
            "asin": "asin", "generic name": "generic_name"
        }

        if key in mapping:
            field = mapping[key]
            if field == "ingredients":
                self._handle_ingredients_field(value, details)
            elif not details.get(field):
                details[field] = value

    def _handle_ingredients_field(self, value: str, details: Dict[str, str]):
        """Handle special case for ingredients field"""
        allergen_key = "allergen information:"
        if allergen_key in value.lower():
            parts = re.split(re.escape(allergen_key), value, flags=re.IGNORECASE)
            details["ingredients"] = self._clean_text(parts[0])
            details["allergen_information"] = self._clean_text(parts[1]) if len(parts) > 1 else None
        else:
            details["ingredients"] = value

    def _extract_ingredients(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract ingredients from important information section"""
        sections = soup.select('#important-information .content')
        for section in sections:
            heading = section.find('h4')
            if heading and 'ingredients' in heading.text.lower():
                text = section.get_text(separator=' ', strip=True)
                return self._clean_text(text.replace(heading.text, ''))
        return None

    def get_breadcrumbs(self, soup: BeautifulSoup) -> List[str]:
        """Extract breadcrumb navigation"""
        try:
            breadcrumb_ul = soup.select_one("#wayfinding-breadcrumbs_feature_div ul")
            if breadcrumb_ul:
                links = breadcrumb_ul.select("a.a-link-normal.a-color-tertiary")
                breadcrumbs = [self._clean_text(link.get_text()) for link in links]
                self.logger.info(f"Breadcrumbs extracted: {' > '.join(breadcrumbs)}")
                return breadcrumbs
            self.logger.warning("Breadcrumb section not found.")
        except Exception as e:
            self.logger.error(f"Error extracting breadcrumbs: {e}")
        return []

    def get_all_product_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract all product images"""
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
        """Get product images"""
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

    def get_product_urls(self, url: str) -> List[str]:
        """Scrapes product URLs from category pages"""
        if not self._safe_get(url):
            self.logger.error(f"Failed to load product page {url}. Skipping.")
            return []

        product_urls = set()
        page_count = 1

        while True:
            self.logger.info(f"--- Scraping product URLs from page {page_count} ---")
            self._load_all_products()
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            page_urls = self._extract_product_urls_from_page(soup)

            if not page_urls:
                self.logger.warning(f"No product URLs found on page {page_count}. Check selectors.")

            self.logger.info(f"Found {len(page_urls)} new URLs on this page.")
            product_urls.update(page_urls)
            self.logger.info(f"Total unique URLs collected so far: {len(product_urls)}")

            if not self.click_next_button():
                break
            page_count += 1
            time.sleep(random.uniform(2, 4))

        self.logger.info(f"Total unique product URLs collected from all pages: {len(product_urls)}")
        return list(product_urls)

    def _extract_product_urls_from_page(self, soup: BeautifulSoup) -> set:
        """Extract product URLs from current page"""
        page_urls = set()

        # Multiple selectors for different page layouts
        selectors = [
            ('a', lambda x: x and ('ProductGridItem__overlay__IQ3Kw' in x or
                                  ('a-link-normal' in x and 's-no-outline' in x))),
            ('a', re.compile(r'ProductShowcase__title__')),
            ('a.a-link-normal.s-no-outline[href*="/dp/"]', None)
        ]

        for selector, class_filter in selectors:
            if class_filter and callable(class_filter):
                elements = soup.find_all(selector, class_=class_filter)
            elif class_filter:
                elements = soup.find_all(selector, class_=class_filter)
            else:
                elements = soup.select(selector)

            for element in elements:
                href = element.get('href')
                if href and '/dp/' in href:
                    clean_href = href.split('/ref=')[0]
                    full_url = self.BASE_URL + clean_href
                    page_urls.add(full_url)

        # Handle special elements found via Selenium
        try:
            links = self.driver.find_elements(By.XPATH, '//div[@data-testid="small-editorial-tile"]//a')
            for link in links:
                href = link.get_attribute("href")
                if href and '/dp/' in href:
                    page_urls.add(href)
        except:
            pass

        return page_urls

    def get_product_details(self, url: str) -> Dict[str, Any]:
        """Extract detailed product information from a single product page"""
        if not self._safe_get(url):
            self.logger.error(f"Failed to load product page {url}. Skipping.")
            return {}

        try:
            parsed_url = urlparse(url)
            base_url = urlunparse(parsed_url._replace(query=""))

            WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "productTitle"))
            )
            time.sleep(self.SCROLL_PAUSE_TIME + random.randint(3, 6))
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            return self._parse_product_data(soup, base_url)

        except Exception as e:
            self.logger.error(f"CRITICAL: Failed to process product page {url}. Error: {e}", exc_info=True)
            return {}

    def _parse_product_data(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Parse product data from soup"""
        details = self._extract_product_details(soup)
        ingredients = self._extract_ingredients(soup) or details.get('ingredients')
        images = self._get_images(soup)
        def safe_find_text(soup, selector):
            try:
                return self._clean_text(soup.select_one(selector).text)
            except AttributeError:
                return None

        mrp = safe_find_text(soup, 'span.a-price.a-text-price span.a-offscreen')

        product = {
            "variant_id": None,
            "name": safe_find_text(soup, '#productTitle'),
            "product_url": base_url,
            "brand_name": details.get('brand'),
            "category": None,
            "sub_category": None,
            "diet": self.get_diet(details.get('ingredient_type')),
            "allergen_information": details.get('allergen_information'),
            "mass_measurement_unit": (self.get_mass_measurement_unit(details.get('weight')) or
                                    self.get_mass_measurement_unit(details.get('net_quantity'))),
            "net_weight": details.get('weight') or details.get('net_quantity'),
            "mrp": mrp,
            "ingredients_main_ocr": ingredients,
            "nutrients_main_ocr": None,
            "images": self.extract_image_urls_text(images),
            "other_images": None,
            "breadcrumbs": json.dumps({"category": self.get_breadcrumbs(soup)}),
            "front_img": None,
            "back_img": None,
            "nutrients_img": None,
            "ingredients_img": None,
            "source": "Amazon",
            "status": "raw",
            "addtional_detail": json.dumps(self.get_technical_details(soup)),
            "addtional_info": json.dumps(self.get_additional_information(soup))
        }
        return product

    # ========================================================================
    # API INTEGRATION METHODS
    # ========================================================================

    def _send_to_api(self, product_data: Dict[str, Any]) -> bool:
        """Send product data to API endpoint"""
        try:
            response = requests.post(
                self.API_ENDPOINT,
                json=product_data,
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
        """Main method to scrape an entire Amazon category"""
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
        """Main method to scrape a single Amazon product"""
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
        with tqdm(total=len(product_urls), desc="Amazon Category Scraping", unit="products") as pbar:
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
                time.sleep(random.uniform(4, 8))

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
    print("--- Amazon Scraper ---")
    url = input("Enter Amazon Category or Product URL: ").strip()

    if "/dp/" in url or "/gp/product/" in url:
        is_product = True
        print("Detected a Product URL.")
    else:
        is_product = False
        print("Detected a Category URL.")

    parsed = urlparse(url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"

    headless_choice = input("Run in headless mode (browser not visible)? (Y/n): ").strip().lower()
    run_headless = headless_choice != 'n'

    amazon_scraper = Amazon(headless=run_headless, base_url=base_domain)

    if is_product:
        amazon_scraper.scrape_product(product_url=url)
    else:
        amazon_scraper.scrape_category(category_url=url)
