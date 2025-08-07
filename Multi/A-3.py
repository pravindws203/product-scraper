"""
Amazon Web Scraper Module
Author: Pravin Prajapati (Modified for Windows & enhanced robustness)

A modular scraper for Amazon product data with:
- Warm-up navigation to avoid bot detection.
- AJAX API data extraction.
- Product page details scraping.
- Self-contained logging.
"""

import os
import re
import csv
import time
import json
import random
import sys
import locale
from logger_config import setup_logger
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from seleniumwire import webdriver
from tqdm import tqdm

# Fix encoding issues for Windows
if sys.platform.startswith('win'):
    # Set console encoding to UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Set locale for proper Unicode handling
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except locale.Error:
            pass  # Use system default


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
        self.API_ENDPOINT = "http://10.0.101.117:1001/insert"  # API URL configured here
        self.USER_AGENTS = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        ]
        self.MAX_SCROLL_RETRIES = 10
        self.SCROLL_PAUSE_TIME = 4
        self.MAX_RETRIES = 3
        self.PAGE_LOAD_TIMEOUT = 30  # Increased timeout
        self.REQUEST_TIMEOUT = 30
        self.ELEMENT_WAIT_TIMEOUT = 15

    def _setup_logging(self):
        """
        Configure logging settings using logger_config.
        """
        self.logger = setup_logger("AMAZON", "amazon_scraper.log")

    def _get_random_user_agent(self) -> str:
        """Return a random user agent from predefined list."""
        return random.choice(self.USER_AGENTS)

    def init_driver(self) -> bool:
        """
        Initialize and return a Chrome WebDriver.
        """
        try:
            options = webdriver.ChromeOptions()
            if self.headless:
                options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument(f'--user-agent={self._get_random_user_agent()}')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            # Keeping your other options
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-extensions')

            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(self.PAGE_LOAD_TIMEOUT)
            self.logger.info("WebDriver initialized successfully.")
            return True
        except WebDriverException as e:
            self.logger.error(f"FATAL: WebDriver initialization failed. Error: {e}")
            return False

    def _safe_click(self, element) -> bool:
        """
        Safely clicks an element using multiple strategies to avoid click interception.

        Args:
            element: WebElement to click

        Returns:
            bool: True if click was successful, False otherwise
        """
        try:
            element.click()
            return True
        except ElementClickInterceptedException:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    ActionChains(self.driver).move_to_element(element).click().perform()
                    return True
                except Exception as e:
                    self.logger.error(f"All click strategies failed: {e}")
                    return False

    def _handle_modal_overlays(self) -> bool:
        """
        Handles modal overlays and Amazon 404 error redirects that might block scraping.

        Returns:
            bool: True if an overlay or 404 redirect was handled, False otherwise
        """
        try:
            # === 1. Modal overlays ===
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
                                self.logger.info("✅ Closed modal overlay.")
                                time.sleep(1)
                                return True
                except (NoSuchElementException, StaleElementReferenceException):
                    continue

            try:
                page_source = self.driver.page_source.lower()
                if (
                        'looking for something?' in page_source and
                        'the web address you entered is not a functioning page' in page_source
                ):
                    try:
                        # Try to click "Click here to go back to the Amazon home page"
                        link = self.driver.find_element(By.CSS_SELECTOR, 'a[href="/ref=cs_404_link"]')
                        if link.is_displayed():
                            self._safe_click(link)
                            self.logger.warning("↩️ Detected 404 page. Redirecting to Amazon home page...")
                            time.sleep(2)
                            return True
                    except NoSuchElementException:
                        pass
            except Exception as e:
                self.logger.error(f"Error checking Amazon 404 page: {e}")

        except Exception as e:
            self.logger.error(f"Error handling modal overlays: {e}")

        return False

    def _check_for_blocks(self) -> bool:
        """
        Detects if the page is blocked by CAPTCHA, access denial, popups, or 404 errors on Amazon.in or Amazon.com.
        Returns True if a block or popup is found, else False.
        """
        try:
            page_source = self.driver.page_source.lower()

            # 1. Page source block indicators
            block_indicators = [
                'captcha',
                'access denied',
                'unusual traffic',
                'enter the characters',
                'i am not a robot',
                'recaptcha'
            ]
            if any(indicator in page_source for indicator in block_indicators):
                self.logger.warning("🛑 Page source contains block indicators.")
                return True

            # 2. Amazon 404 error block
            if (
                    'looking for something?' in page_source and
                    'the web address you entered is not a functioning page' in page_source
            ):
                self.logger.warning("🚫 Amazon 404 page detected.")
                return True

            # 3. Popup selectors
            popup_selectors = [
                # Continue Shopping
                'button.a-button-text',
                'input[aria-label*="Continue shopping"]',
                'button[aria-label*="Continue shopping"]',
                'input[value*="Continue shopping"]',
                'a[title*="Continue shopping"]',
                '.a-button-input[aria-label*="Continue"]',
                'input[name="continue-shopping"]',

                # Location popup or dismiss
                'button[aria-label*="Dismiss"]',
                'button[data-action-type="DISMISS"]',
                'input[aria-label*="Not now"]',

                # Cookie consent
                'input[id*="accept-cookies"]',
                'button[id*="accept-cookies"]',
                'input[aria-label*="Accept cookies"]',
                'button:contains("Accept")',

                # Generic close
                'button[aria-label*="Close"]',
                'button[title*="Close"]',
                'button.a-button-close',

                # reCAPTCHA iframe
                'iframe[title="reCAPTCHA"]',
                'div.g-recaptcha',
                'div[class*="recaptcha"]',
            ]

            for selector in popup_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        if el.is_displayed():
                            self.logger.warning(f"⚠️ Popup or blocking element visible: {selector}")
                            return True
                except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
                    continue

            return False

        except Exception as e:
            self.logger.error(f"❌ Error during block check: {e}")
            return False

    def _handle_homepage_popups(self) -> bool:
        """
        Handles various popups that may appear on Amazon homepage including:
        - Continue Shopping dialogs
        - Location selection popups
        - Cookie consent banners
        - Newsletter signup modals
        - Language selection dialogs

        Returns:
            bool: True if any popup was handled, False if no popups found

        Note:
            This method uses multiple fallback strategies to handle different popup types
            and variations across different Amazon regions.
        """
        popup_handled = False

        try:
            time.sleep(2)

            popup_selectors = [
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
                    break  # Exit after handling first popup

            if not popup_handled:
                self._handle_modal_overlays()

        except Exception as e:
            self.logger.error(f"Error while handling popups: {e}")

        return popup_handled

    def _perform_warmup_and_get(self, target_url: str) -> bool:
        """
        Performs a safe navigation protocol by first visiting Amazon homepage.
        """
        try:
            # FIXED: Removed all emojis from log messages to prevent encoding errors
            self.logger.info("=" * 60)
            self.logger.info("STARTING SAFE NAVIGATION PROTOCOL")
            self.logger.info("=" * 60)

            self.logger.info(f"Step 1/4: Navigating to Amazon homepage for warm-up: {self.BASE_URL}")
            self.driver.get(self.BASE_URL)
            WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self.logger.info("Homepage loaded successfully")

            # Step 2: Handle potential popups and dialogs
            self.logger.info("Step 2/4: Checking for popups and dialogs")
            popup_handled = self._handle_homepage_popups()
            if popup_handled:
                self.logger.info("Popup dialogs handled successfully")
            else:
                self.logger.info("No popups detected or already dismissed")

            warmup_delay = random.uniform(5, 8)
            self.logger.info(f"Step 3/4: Mimicking human behavior - waiting {warmup_delay:.2f} seconds")
            time.sleep(warmup_delay)

            self.logger.info(f"Step 4/4: Navigating to target URL: {target_url}")
            self.driver.get(target_url)
            WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Additional wait for dynamic content
            post_load_delay = random.uniform(2, 4)
            self.logger.info(f"Waiting {post_load_delay:.2f} seconds for dynamic content to load")
            time.sleep(post_load_delay)

            self.logger.info("Final check of navigation status.")
            current_url = self.driver.current_url
            if "amazon" in current_url.lower():
                self.logger.info("Successfully navigated to target page.")
                self.logger.info(f"Current URL: {current_url}")
                self.logger.info("NAVIGATION PROTOCOL COMPLETED SUCCESSFULLY")
                return True
            else:
                self.logger.error("Navigation failed - not on Amazon domain")
                return False

        except Exception as e:
            self.logger.error("An unexpected error occurred during navigation protocol.")
            self.logger.error(f"Details: {e}", exc_info=True)
            return False

    def _safe_get(self, url: str) -> bool:
        """
        Safely navigate to URL with warm-up protocol and retries.

        This method implements a comprehensive navigation strategy:
        1. Uses warm-up protocol for first navigation
        2. Handles popups and dialogs automatically
        3. Implements retry mechanism with exponential backoff
        4. Includes bot detection checks

        Args:
            url (str): Target URL to navigate to

        Returns:
            bool: True if navigation successful, False otherwise
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                # FIXED: Removed emoji from log message
                self.logger.info(f"Navigation attempt {attempt + 1}/{self.MAX_RETRIES}")

                WebDriverWait(self.driver, self.ELEMENT_WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                if self._check_for_blocks():
                    self.logger.warning("Detected CAPTCHA or access block")
                    self._handle_homepage_popups()
                    time.sleep(random.uniform(15, 25))

                # FIXED: Removed emoji from log message
                self.logger.info("Navigation completed successfully")
                return True

            except TimeoutException:
                # FIXED: Removed emoji from log message
                self.logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
            except WebDriverException as e:
                # FIXED: Removed emoji from log message
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")

            if attempt == self.MAX_RETRIES - 1:
                # FIXED: Removed emoji from log message
                self.logger.error(f"Failed to load {url} after {self.MAX_RETRIES} attempts")
                return False

            backoff_time = (2 ** attempt) + random.uniform(1, 3)
            # FIXED: Removed emoji from log message
            self.logger.info(f"Waiting {backoff_time:.2f} seconds before retry...")
            time.sleep(backoff_time)

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
            "asin": None, "weight": None, "brand": None, "additives": None,
            "net_quantity": None, "allergen_information": None, "ingredients": None,
            "ingredient_type": None, 'generic_name': None
        }

        # Extract from technical details table
        rows = soup.select('#productDetails_techSpec_section_1 tr')
        for row in rows:
            key_el = row.find('th')
            value_el = row.find('td')
            if key_el and value_el:
                key = self._clean_text(key_el.get_text()).lower()
                value = self._clean_text(value_el.get_text())
                self._process_detail_row(key, value, details)

        # Extract from additional information section
        additional_info = soup.select('#productDetails_detailBullets_sections1 tr')
        for row in additional_info:
            key_el = row.find('th')
            value_el = row.find('td')
            if key_el and value_el:
                key = self._clean_text(key_el.get_text()).lower().strip()
                value = self._clean_text(value_el.get_text())
                self._process_detail_row(key, value, details)

        return details

    def get_technical_details(self, soup: BeautifulSoup) -> Dict[str, str]:
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
                # Handle special case for ingredients and allergen info together
                allergen_key = "allergen information:"
                if allergen_key in value.lower():
                    parts = re.split(re.escape(allergen_key), value, flags=re.IGNORECASE)
                    details["ingredients"] = self._clean_text(parts[0])
                    details["allergen_information"] = self._clean_text(parts[1]) if len(parts) > 1 else None
                else:
                    details["ingredients"] = value
            elif not details.get(field):  # Only set if not already set (e.g., weight vs item weight)
                details[field] = value

    def _extract_ingredients(self, soup: BeautifulSoup) -> Optional[str]:
        sections = soup.select('#important-information .content')
        for section in sections:
            heading = section.find('h4')
            if heading and 'ingredients' in heading.text.lower():
                text = section.get_text(separator=' ', strip=True)
                # Remove heading text from the content
                return self._clean_text(text.replace(heading.text, ''))
        return None

    def get_breadcrumbs(self, soup: BeautifulSoup) -> List[str]:
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
        image_urls = set()
        try:
            image_data = soup.select_one("#imgTagWrapperId img")
            if image_data and image_data.has_attr("data-a-dynamic-image"):
                dynamic_image_json = image_data["data-a-dynamic-image"]
                # Use regex to find all URLs in the JSON-like string
                urls = re.findall(r'"(https://[^"]+)"', dynamic_image_json)
                # Filter for high-resolution images
                high_res_urls = {url for url in urls if '._' not in url.split('/')[-1] or '._AC_SL' in url}
                image_urls.update(high_res_urls or urls)

            if not image_urls:
                # Fallback for main image
                main_img = soup.select_one("#landingImage")
                if main_img and main_img.has_attr('src'):
                    image_urls.add(main_img['src'])

            self.logger.info(f"Found {len(image_urls)} unique image(s).")
            return list(image_urls)
        except Exception as e:
            self.logger.error(f"Error extracting images: {e}")
            return []

    def _get_images(self, soup: BeautifulSoup) -> List[str]:
        return self.get_all_product_images(soup)

    def get_mass_measurement_unit(self, unit: str):
        if not unit: return None
        cleaned_unit = re.sub(r'[\d\.]+', '', str(unit)).strip().lower()
        unit_mappings = {
            'GRAMS': ['gram', 'g', 'kg', 'kilogram'],
            'MILLILITRE': ['ml', 'millilitre', 'liter', 'l', 'litre']
        }
        for standard, variations in unit_mappings.items():
            if any(var in cleaned_unit for var in variations):
                return standard
        return None

    def get_diet(self, diet: str):
        if not diet: return None
        diet = diet.lower()
        if 'vegan' in diet: return "Vegan"
        if 'non veg' in diet: return 'Non Veg'
        if 'vegetarian' in diet or 'veg' in diet: return 'Veg'
        return None

    def extract_image_urls_text(self, image_urls) -> str:
        if not image_urls or not isinstance(image_urls, list):
            return ""
        valid_urls = [url for url in image_urls if isinstance(url, str) and url.startswith("http")]
        return json.dumps({"image_urls": valid_urls}, indent=2) if valid_urls else ""

    def _load_all_products(self) -> None:
        """Scrolls down the page to load all products."""
        time.sleep(self.SCROLL_PAUSE_TIME + random.random())
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        footer_height = self.driver.execute_script(
            "return document.getElementById('navFooter') ? document.getElementById('navFooter').offsetHeight : 0;")
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
        """Clicks the 'Next' button for pagination."""
        try:
            next_btn = self.driver.find_element(By.CSS_SELECTOR, 'a.s-pagination-item.s-pagination-next:not(.s-pagination-disabled)')
            self.logger.info("Clicking 'Next' page button...")
            next_btn.click()
            # Wait for the next page to load
            WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT).until(
                EC.staleness_of(next_btn)
            )
            return True
        except (NoSuchElementException, TimeoutException):
            self.logger.info("No more 'Next' pages or button not found. Ending pagination.")
            return False

    def get_product_urls(self) -> List[str]:
        """Scrapes product URLs from the current and subsequent category pages."""

        if not self._safe_get(url):
            self.logger.error(f"Failed to load product page {url}. Skipping.")
            return []

        product_urls = set()
        page_count = 1

        while True:
            self.logger.info(f"--- Scraping product URLs from page {page_count} ---")
            self._load_all_products()
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            product_elements = soup.find_all('a', class_=lambda x: x and (
                'ProductGridItem__overlay__IQ3Kw' in x or
                ('a-link-normal' in x and 's-no-outline' in x)
            ))
            product_link = soup.find_all('a', class_=re.compile(r'ProductShowcase__title__'))

            page_urls = set()

            for product in product_link:
                href = product.get('href')
                if href and '/dp/' in href:
                    product_urls.add('https://www.amazon.in' + href)

            for product in product_elements:
                href = product.get('href')
                if href and '/dp/' in href:
                    product_urls.add('https://www.amazon.in' + href)

            links = soup.select('a.a-link-normal.s-no-outline[href*="/dp/"]')
            for link in links:
                href = link.get('href')
                clean_href = href.split('/ref=')[0]
                if '/dp/' in clean_href:
                    full_url = "https://www.amazon.in" + clean_href
                    page_urls.add(full_url)

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

    def get_product_details(self, url: str) -> Dict[str, Any]:
        """Extract detailed product information from a single product page."""
        if not self._safe_get(url):
            self.logger.error(f"Failed to load product page {url}. Skipping.")
            return {}

        try:
            # Wait for a key element to ensure the page is loaded
            WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "productTitle"))
            )
            time.sleep(random.uniform(1, 3))  # Small random delay
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

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
                "product_url": url,
                "brand_name": details.get('brand'),
                "category": None, "sub_category": None,
                "diet": self.get_diet(details.get('ingredient_type')),
                "allergen_information": details.get('allergen_information'),
                "mass_measurement_unit": self.get_mass_measurement_unit(details.get('weight')) or self.get_mass_measurement_unit(details.get('net_quantity')),
                "net_weight": details.get('weight') or details.get('net_quantity'),
                "mrp": mrp,
                "ingredients_main_ocr": ingredients,
                "nutrients_main_ocr": None,
                "images": self.extract_image_urls_text(images),
                "other_images": None,
                "breadcrumbs": json.dumps({"category": self.get_breadcrumbs(soup)}),
                "front_img": images[0] if images else None, "back_img": None,
                "nutrients_img": None, "ingredients_img": None,
                "source": "Amazon", "status": "raw",
                "addtional_detail": json.dumps(self.get_technical_details(soup)),
                "addtional_info": json.dumps(self.get_additional_information(soup))
            }
            return product
        except Exception as e:
            self.logger.error(f"CRITICAL: Failed to process product page {url}. Error: {e}", exc_info=True)
            return {}

    def scrape_category(self, category_url: str) -> None:
        """Main method to scrape an entire Amazon category."""
        if not self.init_driver(): return

        try:
            # Warm-up and navigation
            if not self._perform_warmup_and_get(category_url):
                self.logger.error("Scraping aborted due to navigation failure.")
                return

            self.logger.info(f"Starting scraping for URL: {category_url}")
            product_urls = self.get_product_urls()

            if not product_urls:
                self.logger.error("No product URLs found. Exiting.")
                return

            self.logger.info(f"Found {len(product_urls)} total product URLs to scrape.")

            with tqdm(total=len(product_urls), desc="Amazon Category Scraping", unit="products") as pbar:
                for url in product_urls:
                    product_data = self.get_product_details(url)
                    if product_data:
                        try:
                            response = requests.post(self.API_ENDPOINT, json=product_data, timeout=self.REQUEST_TIMEOUT)
                            if response.status_code == 200:
                                inserted_id = response.json().get('id', 'N/A')
                                self.logger.info(f"Successfully inserted product. ID: {inserted_id}")
                                pbar.set_postfix({"Last Inserted ID": inserted_id})
                            else:
                                self.logger.error(f"API Error: Failed to insert product data. Status: {response.status_code}, Response: {response.text}")
                        except requests.exceptions.RequestException as e:
                            self.logger.error(f"Network Error: Could not connect to API endpoint {self.API_ENDPOINT}. Error: {e}")
                    else:
                        self.logger.warning(f"Failed to scrape details for product: {url}")

                    pbar.update(1)
                    time.sleep(random.uniform(2, 5))

            self.logger.info("Scraping finished.")

        except KeyboardInterrupt:
            self.logger.info("\nScraping stopped by user.")
        except Exception as e:
            self.logger.critical(f"A critical error occurred: {e}", exc_info=True)
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("WebDriver closed.")

    def scrape_product(self, product_url: str) -> None:
        """Main method to scrape a single Amazon product."""
        if not self.init_driver(): return

        try:
            if not self._perform_warmup_and_get(product_url):
                self.logger.error("Scraping aborted due to navigation failure.")
                return

            product_data = self.get_product_details(product_url)
            if product_data:
                self.logger.info(f"Scraped data: {json.dumps(product_data, indent=2, ensure_ascii=False)}")
                try:
                    response = requests.post(self.API_ENDPOINT, json=product_data, timeout=self.REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        self.logger.info(f"Successfully inserted product. ID: {response.json().get('id')}")
                    else:
                        self.logger.error(f"API Error: Failed to insert product data. Status: {response.status_code}, Response: {response.text}")
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Network Error: Could not connect to API endpoint {self.API_ENDPOINT}. Error: {e}")
            else:
                self.logger.error(f"Failed to scrape any details for product: {product_url}")

            self.logger.info("Single product scraping finished.")

        except KeyboardInterrupt:
            self.logger.info("\nScraping stopped by user.")
        except Exception as e:
            self.logger.critical(f"A critical error occurred: {e}", exc_info=True)
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("WebDriver closed.")


if __name__ == "__main__":
    print("--- Amazon Scraper ---")
    url = input("Enter Amazon Category or Product URL: ").strip()

    if "/dp/" in url or "/gp/product/" in url:
        is_product = True
        print("Detected a Product URL.")
    else:
        is_product = False
        print("Detected a Category URL.")

    headless_choice = input("Run in headless mode (browser not visible)? (Y/n): ").strip().lower()
    run_headless = headless_choice != 'n'

    amazon_scraper = Amazon(headless=run_headless)

    if is_product:
        amazon_scraper.scrape_product(product_url=url)
    else:
        amazon_scraper.scrape_category(category_url=url)