# !pip install pandas opencv-python numpy pyzbar tqdm
# !apt-get install libzbar0
import pandas as pd
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from urllib.request import Request, urlopen
from typing import Optional, List, Tuple
import random
from tqdm import tqdm
import warnings
import os
import requests

# Suppress ZBar warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)


def get_random_user_agent() -> str:
  """Returns a random user agent from predefined list"""
  user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 10; SM-A505FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
  ]
  return random.choice(user_agents)


def process_image(image_url: str) -> Optional[str]:
  """Process image to extract barcode using multiple enhanced techniques"""
  try:
    req = Request(image_url, headers={'User-Agent': get_random_user_agent()})
    with urlopen(req, timeout=10) as response:
      img_array = np.asarray(bytearray(response.read()), dtype=np.uint8)
      img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
      
      if img is None:
        return None
      
      # Try different color channels
      for channel in [None, 0, 1, 2]:
        if channel is not None:
          gray = img[:, :, channel]
        else:
          gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # List of image processing techniques to try
        techniques: List[Tuple[str, np.ndarray]] = [
          ('original', gray),
          ('blurred', cv2.GaussianBlur(gray, (5, 5), 0)),
          ('median_blur', cv2.medianBlur(gray, 3)),
          ('bilateral_filter', cv2.bilateralFilter(gray, 9, 75, 75)),
          ('threshold', cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
          ('sharpened', cv2.addWeighted(gray, 1.5, cv2.GaussianBlur(gray, (5, 5), 0), -0.5, 1)),
          ('adaptive_thresh', cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                    cv2.THRESH_BINARY, 11, 2)),
          ('equalized', cv2.equalizeHist(gray)),
          ('clahe', cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)),
          ('morph_open', cv2.morphologyEx(gray, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))),
          ('morph_close', cv2.morphologyEx(gray, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))),
          ('inverted', cv2.bitwise_not(gray)),
          ('gamma_corrected', np.uint8(cv2.pow(gray / 255.0, 0.5) * 255))
        ]
        
        # Try different scales
        for scale in [0.8, 1.0, 1.5, 2.0]:
          scaled_gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
          techniques.append((f'scaled_{scale}x', scaled_gray))
        
        # Try decoding on each processed version
        for name, processed_img in techniques:
          try:
            barcodes = decode(processed_img)
            for barcode in barcodes:
              if barcode.type in ["EAN8", "EAN13", "UPC-A", "UPC-E", "CODE-128", "CODE-39"]:
                return barcode.data.decode('utf-8')
          except:
            continue
        
        # Try different rotation angles
        angles = [-15, -10, -5, 5, 10, 15]
        height, width = gray.shape
        center = (width // 2, height // 2)
        
        for angle in angles:
          M = cv2.getRotationMatrix2D(center, angle, 1.0)
          rotated = cv2.warpAffine(gray, M, (width, height))
          try:
            barcodes = decode(rotated)
            for barcode in barcodes:
              if barcode.type in ["EAN8", "EAN13", "UPC-A", "UPC-E", "CODE-128", "CODE-39"]:
                return barcode.data.decode('utf-8')
          except:
            continue
        
        # Try edge detection approach
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
          x, y, w, h = cv2.boundingRect(cnt)
          aspect_ratio = float(w) / h
          if aspect_ratio > 2 and w > 50 and h > 10:
            roi = gray[y:y + h, x:x + w]
            try:
              barcodes = decode(roi)
              for barcode in barcodes:
                if barcode.type in ["EAN8", "EAN13", "UPC-A", "UPC-E", "CODE-128", "CODE-39"]:
                  return barcode.data.decode('utf-8')
            except:
              continue
      
      return None
  
  except Exception as e:
    print(f"Error processing image: {e}")
    return None


def process_csv_for_barcodes(input_csv: str, output_csv: str) -> None:
  """Process CSV incrementally, saving results after each row"""
  try:
    print("\n[ℹ] Starting barcode extraction process...")
    
    # Check if output file exists to resume or start new
    if os.path.exists(output_csv):
      df = pd.read_csv(output_csv)
      processed_count = len(df)
      if 'barcode' not in df.columns:
        df['barcode'] = None
    else:
      df = pd.read_csv(input_csv)
      df['barcode'] = None
      processed_count = 0
    
    total_rows = len(df)
    success_count = df['barcode'].notna().sum()
    
    # Create progress bar starting from where we left off
    pbar = tqdm(total=total_rows, initial=processed_count, desc="Processing rows", unit="row", dynamic_ncols=True)
    
    # Process remaining rows
    for i in range(processed_count, total_rows):
      row = df.iloc[i]
      barcode = None
      
      # Skip rows with 'combo' or 'Combo' in the 'name' field
      name = str(row.get('unit_of_measure', '')).lower()
      if 'combo' in name:
        pbar.update(1)
        df.at[i, 'barcode'] = None
        df.to_csv(output_csv, index=False)
        pbar.set_postfix({'Success': f"{success_count}/{pbar.n}"})
        continue
      
      # Check each image URL in the row
      for j in range(1, 11):
        url = row.get(f'image_url_{j}')
        if pd.isna(url) or not isinstance(url, str):
          continue
        
        barcode = process_image(url)
        if barcode:
          success_count += 1
          break
      
      # Update the DataFrame with the result
      df.at[i, 'barcode'] = barcode
      
      # Save after each row
      df.to_csv(output_csv, index=False)
      
      # Update progress
      pbar.update(1)
      pbar.set_postfix({'Success': f"{success_count}/{pbar.n}"})
    
    pbar.close()
    
    # Print summary
    print("\n[✔] Processing completed!")
    print(f"  - Total rows processed: {total_rows}")
    print(f"  - Barcodes found: {success_count} ({success_count / total_rows * 100:.1f}%)")
    print(f"  - Barcodes not found: {total_rows - success_count}")
    print(f"\nResults saved to: {output_csv}")
  
  except Exception as e:
    print(f"\n[✖] Error processing CSV file: {str(e)}")
    raise


if __name__ == "__main__":
  input_csv = "zepto_data.csv"
  output_csv = "zepto_data_with_barcodes.csv"
  
  print("=== Barcode Extraction Tool ===")
  process_csv_for_barcodes(input_csv, output_csv)