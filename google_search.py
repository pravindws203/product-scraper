import time
import random

from logger_config import setup_logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (NoSuchElementException,
                                        WebDriverException,
                                        TimeoutException)


class GoogleSearch:
  def __init__(self, headless=True):
    """
        Initialize GoogleSearch with optional headless mode

        Args:
            headless (bool): Run browser in headless mode if True
        """
    self.driver = None
    self.max_retries = 5
    self.retry_delay = 5
    self.headless = headless
    self._setup_logging()
  
  def _setup_logging(self):
    """Configure logging settings"""
    self.logger = setup_logger("GOOGLW SEARCH", "google_searching.log")
  
  def get_random_user_agent(self) -> str:
    """Return a random user agent from predefined list."""
    user_agents = [
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
    return random.choice(user_agents)
  
  def initialize_driver(self):
    """Initialize Chrome WebDriver with options"""
    try:
      options = webdriver.ChromeOptions()
      
      if self.headless:
        options.add_argument('--headless')
      
      options.add_argument('--no-sandbox')
      options.add_argument('--disable-dev-shm-usage')
      options.add_argument('--start-maximized')
      options.add_argument('--disable-notifications')
      options.add_argument('--disable-dev-shm-usage')
      options.add_argument(f'user-agent={self.get_random_user_agent()}')
      options.add_argument('--disable-blink-features=AutomationControlled')
      options.add_argument('--window-size=1920,1080')
      
      self.driver = webdriver.Chrome(options=options)
      return True
    except WebDriverException as e:
      self.logger.error(f"Driver initialization failed: {str(e)}")
      return False
  
  def accept_cookies(self):
    """Handle cookie consent if present"""
    try:
      consent_button = self.driver.find_element(
        By.XPATH,
        "//button[contains(., 'I agree') or contains(., 'Accept') or contains(., 'Agree')]"
      )
      consent_button.click()
      self.logger.info("Cookie consent accepted")
      time.sleep(1)
      return True
    except NoSuchElementException:
      self.logger.info("No cookie consent found")
      return True
    except Exception as e:
      self.logger.warning(f"Failed to handle cookie consent: {str(e)}")
      return False
  
  def perform_search(self, query):
    """Perform Google search with the given query"""
    try:
      search_box = self.driver.find_element(By.NAME, "q")
      search_box.clear()
      search_box.send_keys(query)
      search_box.send_keys(Keys.RETURN)
      self.logger.info(f"Search performed for: {query}")
      time.sleep(3)
      return True
    except Exception as e:
      self.logger.error(f"Search failed: {str(e)}")
      return False
  
  def find_target_url(self, target_domain, timeout=10):
    """
        Find first URL containing target domain in search results

        Args:
            target_domain (str): Domain to search for in results
            timeout (int): Maximum time to search in seconds

        Returns:
            str: First matching URL or None if not found
        """
    end_time = time.time() + timeout
    while time.time() < end_time:
      try:
        # Wait for search results to load
        time.sleep(random.randint(2,5))
        
        # Find all result links
        results = self.driver.find_elements(By.XPATH, "//a[@href]")
        
        # Extract URLs and check for target domain
        for result in results:
          url = result.get_attribute("href")
          if target_domain.lower() in url.lower():
            self.logger.info(f"Found target URL: {url}")
            return url
        
        # If not found, try next page
        next_button = self.driver.find_element(
          By.CSS_SELECTOR,
          "#pnnext"
        )
        next_button.click()
        self.logger.info("Moving to next page of results")
      
      except NoSuchElementException:
        self.logger.warning("No more results or next button not found")
        break
      except Exception as e:
        self.logger.error(f"Error while searching for results: {str(e)}")
        break
    
    self.logger.warning(f"Target domain '{target_domain}' not found in results")
    return None
  
  def search(self, query, target_domain):
    """
        Main method with retry mechanism

        Args:
            query (str): Search term to query on Google
            target_domain (str): Domain to look for in search results

        Returns:
            str: First matching URL or None if not found
        """
    for attempt in range(1, self.max_retries + 1):
      self.logger.info(f"Attempt {attempt} of {self.max_retries}")
      
      try:
        # Initialize driver
        if not self.initialize_driver():
          raise WebDriverException("Driver initialization failed")
        
        # Open Google
        self.driver.get("https://google.com")
        time.sleep(random.randint(3,5))
        
        # Handle cookies
        if not self.accept_cookies():
          self.logger.warning("Cookie handling failed, continuing anyway")
        
        # Perform search
        if not self.perform_search(query):
          raise Exception("Search failed")
        
        self.logger.info(f"Searching for: {query}")
        # Find target URL
        url = self.find_target_url(target_domain)
        if url:
          return url
      
      except Exception as e:
        self.logger.error(f"Attempt {attempt} failed: {str(e)}")
        if attempt == self.max_retries:
          self.logger.error("Max retries reached")
        else:
          self.logger.info(f"Retrying in {self.retry_delay} seconds...")
          time.sleep(self.retry_delay)
      finally:
        if self.driver:
          self.driver.quit()
          self.driver = None
    
    return None