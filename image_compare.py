import pandas as pd
import requests
from PIL import Image
import numpy as np
from io import BytesIO
import easyocr
from tqdm import tqdm
import os

reader = easyocr.Reader(['en'], gpu=False)


def get_text_score_from_url(image_url):
  try:
    response = requests.get(image_url, timeout=10)
    img = Image.open(BytesIO(response.content)).convert("RGB")
    img_np = np.array(img)
    result = reader.readtext(img_np)
    return len(result)
  except Exception as e:
    print(f"[!] Failed to process {image_url}: {e}")
    return -1


def find_front_back_images(urls):
  scores = []
  for url in urls:
    if isinstance(url, str) and url.strip():
      score = get_text_score_from_url(url)
      # print(f"Text count for {url}: {score}")
      if score >= 0:
        scores.append((url, score))
  if not scores:
    return {"front_url": None, "back_url": None}
  sorted_scores = sorted(scores, key=lambda x: x[1])
  return {
    "front_url": sorted_scores[0][0],
    "back_url": sorted_scores[-1][0]
  }


def add_front_back_columns(csv_path: str) -> None:
  try:
    df = pd.read_csv(csv_path)
    url_columns = [f'image_url_{i}' for i in range(1, 16)]
    
    # Add columns if not already present
    if 'front_url' not in df.columns:
      insert_pos = df.columns.get_loc('image_url_1') if 'image_url_1' in df.columns else 0
      df.insert(loc=insert_pos, column='front_url', value=[None] * len(df))
      df.insert(loc=insert_pos + 1, column='back_url', value=[None] * len(df))
    
    print(f"📦 Processing {len(df)} rows...")
    for i in tqdm(range(len(df)), desc="🔍 Finding front/back", unit="row", dynamic_ncols=True):
      row = df.iloc[i]
      
      # Skip already processed rows
      if pd.notna(row['front_url']) and pd.notna(row['back_url']):
        continue
      
      urls = [row[col] for col in url_columns if col in df.columns and pd.notna(row[col])]
      result = find_front_back_images(urls)
      
      # Only update if result is valid
      if result['front_url'] and result['back_url']:
        df.at[i, 'front_url'] = result['front_url']
        df.at[i, 'back_url'] = result['back_url']
        
        # Save immediately
        df.to_csv(csv_path, index=False)
    
    print(f"[✔] Done! Updated CSV saved to: {csv_path}")
  
  except Exception as e:
    print(f"[✖] Error processing CSV: {e}")


add_front_back_columns("amazon_biscuits.csv")
