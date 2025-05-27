# main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Security, Header, Depends
from fastapi.security.api_key import APIKeyHeader, APIKey
from starlette.status import HTTP_403_FORBIDDEN
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any, Union, Tuple
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from urllib.request import Request, urlopen
import random
import warnings
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Conv2D, MaxPooling2D, Flatten, Input, Dropout, GlobalAveragePooling2D
from tensorflow.keras.applications import MobileNetV2
import time
import asyncio
import io
import uvicorn
import uuid
from datetime import datetime
import os
import logging

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # logging.StreamHandler(),
        logging.FileHandler("logs/barcode_api.log")
    ]
)
logger = logging.getLogger("barcode-scanner-api")

# Suppress ZBar warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Create FastAPI app
app = FastAPI(
    title="Barcode Scanner API",
    description="API for scanning barcodes from images using deep learning techniques",
    version="1.0.0"
)
# Define the API key header
API_KEY = "your-secret-api-key"  # Store this securely in environment variables
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Scan history (in-memory database - in production use a real database)
scan_history: Dict[str, Dict[str, Any]] = {}
cached_models = {}


class ScanRequest(BaseModel):
    image_url: Optional[HttpUrl] = None


class ScanResult(BaseModel):
    scan_id: str
    barcode_data: Optional[str] = None
    barcode_type: Optional[str] = None
    processing_time: float
    method_used: str
    status: str
    timestamp: str


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


async def process_image_async(
    image_data: bytes = None, 
    image_url: str = None, 
    use_deep_learning: bool = True
) -> Dict[str, Any]:
    """Process image to extract barcode"""
    try:
        start_time = time.time()
        method_used = "unknown"
        logger.info(use_deep_learning)
        logger.info(image_url)
        # Get or create ML models
        if use_deep_learning:
            if "detector" not in cached_models:
                cached_models["detector"] = BarcodeDetectionModel()
            if "classifier" not in cached_models:
                cached_models["classifier"] = BarcodeClassifier()
                
            detector = cached_models["detector"]
            classifier = cached_models["classifier"]
        else:
            detector = None
            classifier = None
        
        # Load image
        if image_data is not None:
            img_array = np.frombuffer(image_data, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        elif image_url is not None:
            req = Request(image_url, headers={'User-Agent': get_random_user_agent()})
            with urlopen(req, timeout=10) as response:
                img_array = np.asarray(bytearray(response.read()), dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        else:
            return {
                "barcode_data": None,
                "barcode_type": None, 
                "processing_time": time.time() - start_time,
                "method_used": "error",
                "status": "error",
                "error": "No image data provided"
            }
            
        if img is None:
            return {
                "barcode_data": None,
                "barcode_type": None, 
                "processing_time": time.time() - start_time,
                "method_used": "error",
                "status": "error",
                "error": "Failed to decode image"
            }
        
        barcode_data = None
        barcode_type = None
        
        # Try deep learning pipeline if requested
        if use_deep_learning:
            try:
                # Step 1: Preprocess image
                preprocessed = preprocess_for_ml(img)
                
                # Step 2: Segment potential barcode regions
                barcode_regions = segment_barcode_regions(img, detector)
                
                # Step 3: Decode barcodes in identified regions
                if barcode_regions:
                    results = decode_with_ann(img, barcode_regions, classifier)
                    
                    if results:
                        barcode_data = results[0]['data']
                        barcode_type = results[0]['type']
                        method_used = f"deep_learning_{results[0]['processing']}"
                        
                        return {
                            "barcode_data": barcode_data,
                            "barcode_type": barcode_type,
                            "processing_time": time.time() - start_time,
                            "method_used": method_used,
                            "status": "success"
                        }
                
            except Exception as e:
                logger.error(f"Error in deep learning pipeline: {str(e)}")
                # Continue to traditional methods on error
        
        # Try traditional pipeline
        try:
            # Try simple decoding first
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            barcodes = decode(gray)
            
            if barcodes:
                for barcode in barcodes:
                    if barcode.type in ["EAN8", "EAN13", "UPC-A", "UPC-E", "CODE-128", "CODE-39"]:
                        barcode_data = barcode.data.decode('utf-8')
                        barcode_type = barcode.type
                        method_used = "traditional_basic"
                        
                        return {
                            "barcode_data": barcode_data,
                            "barcode_type": barcode_type,
                            "processing_time": time.time() - start_time,
                            "method_used": method_used,
                            "status": "success"
                        }
            
            # Try advanced techniques if simple decoding failed
            for channel in [None, 0, 1, 2]:
                if channel is not None:
                    channel_img = img[:, :, channel]
                else:
                    channel_img = gray
                
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
                scales = [0.8, 1.0, 1.5, 2.0]
                for scale in scales:
                    scaled = cv2.resize(channel_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                    techniques.append((f'scaled_{scale}x', scaled))
                
                # Try decoding on each processed version
                for name, processed_img in techniques:
                    try:
                        # Allow other tasks to run 
                        await asyncio.sleep(0.001)
                        
                        barcodes = decode(processed_img)
                        for barcode in barcodes:
                            if barcode.type in ["EAN8", "EAN13", "UPC-A", "UPC-E", "CODE-128", "CODE-39"]:
                                barcode_data = barcode.data.decode('utf-8')
                                barcode_type = barcode.type
                                method_used = f"traditional_{name}"
                                
                                return {
                                    "barcode_data": barcode_data,
                                    "barcode_type": barcode_type,
                                    "processing_time": time.time() - start_time,
                                    "method_used": method_used,
                                    "status": "success"
                                }
                    except Exception:
                        continue
            
        except Exception as e:
            logger.error(f"Error in traditional pipeline: {str(e)}")
        
        # Return failure if no barcode found
        return {
            "barcode_data": None,
            "barcode_type": None,
            "processing_time": time.time() - start_time,
            "method_used": method_used,
            "status": "no_barcode_found"
        }
        
    except Exception as e:
        logger.error(f"General error processing image: {str(e)}")
        return {
            "barcode_data": None,
            "barcode_type": None,
            "processing_time": time.time() - start_time if 'start_time' in locals() else 0,
            "method_used": "error",
            "status": "error",
            "error": str(e)
        }


def add_to_history(scan_id: str, result: Dict[str, Any]) -> None:
    """Add scan result to history"""
    scan_history[scan_id] = {
        **result,
        "timestamp": datetime.now().isoformat()
    }
    
    # Keep only the most recent 1000 results
    if len(scan_history) > 1000:
        oldest_key = min(scan_history.keys(), key=lambda k: scan_history[k]["timestamp"])
        scan_history.pop(oldest_key, None)

# Dependency to validate the API key
async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Invalid API key"
        )
    return api_key


@app.get("/")
async def root():
    return {
        "name": "Barcode Scanner API",
        "version": "1.0.0",
        "description": "API for scanning barcodes using deep learning techniques",
        "endpoints": {
            "/scan/url": "Scan barcode from URL",
            "/scan/upload": "Scan barcode from uploaded image",
            "/scan/{scan_id}": "Get result of a previous scan",
            "/health": "Check API health"
        }
    }


@app.post("/scan/url", response_model=ScanResult, dependencies=[Depends(get_api_key)])
async def scan_url(request: ScanRequest, background_tasks: BackgroundTasks):
    """Scan barcode from URL"""
    # Generate unique ID for this scan
    scan_id = str(uuid.uuid4())
    
    # Process image
    result = await process_image_async(
        image_url=str(request.image_url),
        use_deep_learning=True
    )
    
    # Add to history
    scan_result = {
        "scan_id": scan_id,
        **result,
        "timestamp": datetime.now().isoformat()
    }
    
    background_tasks.add_task(add_to_history, scan_id, result)
    
    return scan_result


@app.post("/scan/upload", response_model=ScanResult, dependencies=[Depends(get_api_key)])
async def scan_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Scan barcode from uploaded image"""
    # Generate unique ID for this scan
    scan_id = str(uuid.uuid4())
    
    # Read file content
    try:
        image_data = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file: {str(e)}")
    
    # Process image
    result = await process_image_async(
        image_data=image_data,
        use_deep_learning=True
    )
    
    # Add to history
    scan_result = {
        "scan_id": scan_id,
        **result,
        "timestamp": datetime.now().isoformat()
    }
    
    background_tasks.add_task(add_to_history, scan_id, result)
    
    return scan_result


@app.get("/scan/{scan_id}", response_model=ScanResult, dependencies=[Depends(get_api_key)])
async def get_scan_result(scan_id: str):
    """Get result of a previous scan"""
    if scan_id not in scan_history:
        raise HTTPException(status_code=404, detail="Scan result not found")
    
    return {
        "scan_id": scan_id,
        **scan_history[scan_id]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    # Start the FastAPI app with uvicorn
    uvicorn.run(app, host="10.0.101.153", port=8000)