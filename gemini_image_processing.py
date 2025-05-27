import pandas as pd
import cloudscraper
import json
import time
import random
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(filename="logs/gemini_image_classifier.log", level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

GEMINI_API_KEY = 'AIzaSyChZ7yQ8NMlVTNJ4aWxnGkTMncJxcZq7Gc'
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
scraper = cloudscraper.create_scraper()


def get_random_user_agent() -> str:
  return random.choice([
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
  ])


def parse_gemini_output(text):
  entries = text.strip().split("URL: ")[1:]
  parsed = {}
  for entry in entries:
    lines = entry.strip().split("\n")
    url_line = lines[0].strip()
    classification_line = next((l for l in lines if l.startswith("Classification:")), "")
    url = url_line
    classification = classification_line.split(":", 1)[1].strip().lower() if classification_line else "other"
    if "front" in classification:
      parsed["front_url"] = url
    elif "back" in classification:
      parsed["back_url"] = url
    elif "ingredient" in classification:
      parsed["ingredients_url"] = url
    elif "nutrition" in classification:
      parsed["nutrition_url"] = url
  return parsed


def classify_images_with_gemini(image_urls: list, retries=3) -> dict:
  numbered_urls = [f"{i + 1}. image_url_{i + 1}: {url}" for i, url in enumerate(image_urls)]
  prompt = (
      "You will be provided with a JSON payload containing a list of image URLs associated with a product. "
      "Your task is to classify each image into one of the following categories: 'Front Image', 'Back Image', "
      "'Ingredients Image', 'Nutrition Image', or 'Other'. Classification is based solely on URL filename keywords.\n\n"
      "URLs:\n" + "\n".join(numbered_urls) + "\n\n"
                                             "Please return the result in the following format:\n"
                                             "URL: [actual url]\nClassification: [category]\nReasoning: [brief reason]\n\n"
  )
  
  payload = {
    "contents": [{"parts": [{"text": prompt}]}]
  }
  
  for attempt in range(retries):
    try:
      headers = {'user-agent': get_random_user_agent(), 'Content-Type': 'application/json'}
      response = scraper.post(GEMINI_ENDPOINT, headers=headers, json=payload, timeout=30)
      response.raise_for_status()
      print(response.json())
      result = response.json()
      text = result['candidates'][0]['content']['parts'][0]['text']
      return parse_gemini_output(text)
    
    except Exception as e:
      logging.warning(f"[!] Gemini API attempt {attempt + 1} failed: {e}")
      time.sleep(2 ** attempt)  # exponential backoff
  
  logging.error("[✖] Gemini API failed after all retries")
  return {
    "front_url": None,
    "back_url": None,
    "ingredients_url": None,
    "nutrition_url": None
  }


def add_classified_urls_with_gemini(csv_path: str, sleep_seconds: float = 2.0):
  try:
    df = pd.read_csv(csv_path)
    url_columns = [f'image_url_{i}' for i in range(1, 16)]
    
    # Add target columns if not present
    for col in ['front_url', 'back_url', 'ingredients_url', 'nutrition_url']:
      if col not in df.columns:
        insert_pos = df.columns.get_loc('image_url_1')
        df.insert(loc=insert_pos, column=col, value=[None] * len(df))
    
    for i in tqdm(range(len(df)), desc="🔍 Classifying with Gemini", unit="row", dynamic_ncols=True):
      row = df.iloc[i]
      
      if all(pd.notna(row[col]) for col in ['front_url', 'back_url', 'ingredients_url', 'nutrition_url']):
        continue
      
      urls = [row[col] for col in url_columns if col in df.columns and pd.notna(row[col])]
      if not urls:
        continue
      
      logging.info(f"[→] Classifying row {i + 1}/{len(df)} with {len(urls)} image URLs")
      result = classify_images_with_gemini(urls)
      break
      for col in ['front_url', 'back_url', 'ingredients_url', 'nutrition_url']:
        df.at[i, col] = result.get(col)
      
      df.to_csv(csv_path, index=False)
      time.sleep(sleep_seconds)
    
    logging.info(f"[✔] Finished updating CSV: {csv_path}")
  
  except Exception as e:
    logging.error(f"[✖] Error during processing: {e}")


# Example usage
if __name__ == "__main__":
  add_classified_urls_with_gemini("amazon_beverage_ai.csv", sleep_seconds=5)
