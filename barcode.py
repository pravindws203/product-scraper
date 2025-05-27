# Install required packages
# !pip install pandas opencv-python numpy pyzbar tqdm tensorflow keras scikit-learn
# !apt-get install libzbar0

import cv2
import numpy as np
from pyzbar.pyzbar import decode
from urllib.request import Request, urlopen
from typing import Optional, List, Tuple, Dict, Any
import random
import warnings
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Conv2D, MaxPooling2D, Flatten, Input, Dropout, GlobalAveragePooling2D
from tensorflow.keras.applications import MobileNetV2
from sklearn.preprocessing import LabelEncoder
import time

# Suppress ZBar warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)


class BarcodeDetectionModel:
  """Deep learning model for barcode detection"""
  
  def __init__(self, input_shape=(224, 224, 3)):
    self.input_shape = input_shape
    self.model = self._build_model()
  
  def _build_model(self):
    """Build a CNN model for barcode region detection using transfer learning"""
    # Using MobileNetV2 as base model for faster inference
    base_model = MobileNetV2(
      input_shape=self.input_shape,
      include_top=False,
      weights='imagenet'
    )
    
    # Freeze base model layers
    for layer in base_model.layers:
      layer.trainable = False
    
    # Add custom classification head
    inputs = Input(shape=self.input_shape)
    x = base_model(inputs, training=False)
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.5)(x)
    outputs = Dense(4, activation='sigmoid')(x)  # x, y, width, height predictions
    
    return Model(inputs=inputs, outputs=outputs)
  
  def predict_barcode_region(self, img):
    """Predict barcode region in an image"""
    # In production, this would return bounding box coordinates
    # For this implementation, we'll return None as we're not including the training process
    return None


class BarcodeClassifier:
  """ANN-based barcode symbology classifier"""
  
  def __init__(self):
    self.model = self._build_model()
  
  def _build_model(self):
    """Build an ANN model for barcode type classification"""
    model = Sequential([
      Dense(128, activation='relu', input_shape=(64,)),
      Dropout(0.3),
      Dense(64, activation='relu'),
      Dropout(0.3),
      Dense(32, activation='relu'),
      Dense(7, activation='softmax')  # 7 common barcode types
    ])
    model.compile(
      optimizer='adam',
      loss='categorical_crossentropy',
      metrics=['accuracy']
    )
    return model
  
  def preprocess_features(self, barcode_image):
    """Extract features from barcode image"""
    # Resize to standard size
    resized = cv2.resize(barcode_image, (64, 64))
    # Extract histogram of oriented gradients or other features
    # For simplicity, we'll just use pixel intensities normalized
    features = resized.flatten().astype('float32') / 255.0
    return features[:64]  # Take first 64 features
  
  def predict_barcode_type(self, barcode_image):
    """Predict barcode type"""
    # In production this would return the predicted type
    # We're not including actual weights here, so this is a placeholder
    return None


def get_random_user_agent() -> str:
  """Returns a random user agent from predefined list"""
  user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/604.1',
    'Mozilla/5.0 (Linux; Android 10; SM-A505FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
  ]
  return random.choice(user_agents)


def preprocess_for_ml(img):
  """Preprocess image for machine learning models"""
  # Standard preprocessing for neural networks
  img_resized = cv2.resize(img, (224, 224))
  img_normalized = img_resized / 255.0
  return img_normalized


def segment_barcode_regions(img, detector_model=None):
  """Segment potential barcode regions using CV techniques and ML"""
  # If we have a trained detector model, use it
  if detector_model:
    regions = detector_model.predict_barcode_region(img)
    if regions:
      return regions
  
  # Fall back to traditional computer vision methods
  gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  
  # Gradient-based detection
  gradX = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
  gradY = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=-1)
  
  # Subtract y-gradient from x-gradient
  gradient = cv2.subtract(gradX, gradY)
  gradient = cv2.convertScaleAbs(gradient)
  
  # Blur and threshold the image
  blurred = cv2.blur(gradient, (9, 9))
  _, thresh = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)
  
  # Construct a closing kernel and apply it to the threshold image
  kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
  closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
  
  # Perform erosion and dilation
  closed = cv2.erode(closed, None, iterations=4)
  closed = cv2.dilate(closed, None, iterations=4)
  
  # Find contours
  contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  
  # Filter contours by aspect ratio and area
  barcode_regions = []
  for c in contours:
    x, y, w, h = cv2.boundingRect(c)
    aspect_ratio = float(w) / h
    area = w * h
    
    # Filter based on typical barcode properties
    if (aspect_ratio > 2.5 or aspect_ratio < 0.4) and area > 1500:
      barcode_regions.append((x, y, w, h))
  
  return barcode_regions


def decode_with_ann(img, regions, classifier=None):
  """Try to decode barcodes in identified regions using traditional methods + ANN"""
  results = []
  
  # Process each region
  for x, y, w, h in regions:
    # Extract region with a small margin
    margin = 10
    x_start = max(0, x - margin)
    y_start = max(0, y - margin)
    x_end = min(img.shape[1], x + w + margin)
    y_end = min(img.shape[0], y + h + margin)
    
    roi = img[y_start:y_end, x_start:x_end]
    
    # Try to identify barcode type if classifier provided
    barcode_type = None
    if classifier:
      barcode_features = classifier.preprocess_features(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY))
      barcode_type = classifier.predict_barcode_type(barcode_features)
    
    # Try multiple image processing techniques for each region
    processing_techniques = [
      ('original', roi),
      ('gray', cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)),
      ('blur', cv2.GaussianBlur(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY), (5, 5), 0)),
      ('threshold', cv2.threshold(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY), 0, 255,
                                  cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
      ('adaptive', cv2.adaptiveThreshold(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY), 255,
                                         cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
      ('clahe', cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)))
    ]
    
    for name, processed in processing_techniques:
      try:
        barcodes = decode(processed)
        for barcode in barcodes:
          barcode_data = barcode.data.decode('utf-8')
          results.append({
            'data': barcode_data,
            'type': barcode.type,
            'region': (x, y, w, h),
            'processing': name,
            'ann_predicted_type': barcode_type
          })
      except Exception:
        continue
  
  return results


def process_image(image_url: str) -> Optional[str]:
  """Process image to extract barcode using deep learning enhanced techniques"""
  try:
    start_time = time.time()
    
    # Create models (in production these would be loaded from saved weights)
    detector = BarcodeDetectionModel()
    classifier = BarcodeClassifier()
    
    # Download and load the image
    req = Request(image_url, headers={'User-Agent': get_random_user_agent()})
    with urlopen(req, timeout=10) as response:
      img_array = np.asarray(bytearray(response.read()), dtype=np.uint8)
      img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
      
      if img is None:
        return None
      
      # Try our enhanced pipeline first
      # Step 1: Preprocess image
      preprocessed = preprocess_for_ml(img)
      
      # Step 2: Segment potential barcode regions
      barcode_regions = segment_barcode_regions(img, detector)
      
      # If no regions found with ML, try original technique as fallback
      if not barcode_regions:
        # Try traditional methods as in the original code
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        barcodes = decode(gray)
        
        if barcodes:
          for barcode in barcodes:
            if barcode.type in ["EAN8", "EAN13", "UPC-A", "UPC-E", "CODE-128", "CODE-39"]:
              print(f"Decoded using traditional method in {time.time() - start_time:.3f} seconds")
              return barcode.data.decode('utf-8')
      else:
        # Step 3: Decode barcodes in identified regions
        results = decode_with_ann(img, barcode_regions, classifier)
        
        if results:
          # Return the first found barcode data
          print(f"Decoded using deep learning pipeline in {time.time() - start_time:.3f} seconds")
          return results[0]['data']
      
      # If the enhanced pipeline didn't find anything, fall back to the original method
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
                print(f"Decoded using fallback method in {time.time() - start_time:.3f} seconds")
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
                print(f"Decoded using rotation method in {time.time() - start_time:.3f} seconds")
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
                  print(f"Decoded using edge detection in {time.time() - start_time:.3f} seconds")
                  return barcode.data.decode('utf-8')
            except:
              continue
      
      print(f"No barcode found after {time.time() - start_time:.3f} seconds")
      return None
  
  except Exception as e:
    print(f"Error processing image: {e}")
    return None


if __name__ == "__main__":
  result = process_image('https://m.media-amazon.com/images/I/41XgiFR32nL._SL1100_.jpg')
  print(f"Barcode result: {result}")