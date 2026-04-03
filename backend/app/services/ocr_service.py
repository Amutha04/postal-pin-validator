import pytesseract
import cv2
import numpy as np
from PIL import Image
import re
from config import Config

pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_PATH

def preprocess_image(img):
    """Preprocess image for better OCR"""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=30)
    # Thresholding
    _, thresh = cv2.threshold(
        denoised, 0, 255, 
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return thresh

def extract_pin_from_boxes(img):
    """
    Try to find and crop the PIN box area
    PIN boxes are usually in bottom-right of envelope
    """
    height, width = img.shape[:2]
    
    # Crop bottom-right area where PIN is usually written
    # PIN box is typically in bottom 40% and right 50%
    pin_region = img[
        int(height * 0.6):height,  # bottom 40%
        int(width * 0.5):width     # right 50%
    ]
    
    # Convert to grayscale
    gray = cv2.cvtColor(pin_region, cv2.COLOR_BGR2GRAY)
    
    # Scale up for better OCR
    scaled = cv2.resize(
        gray, None, fx=3, fy=3, 
        interpolation=cv2.INTER_CUBIC
    )
    
    # Apply threshold
    _, thresh = cv2.threshold(
        scaled, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    
    # Run OCR with digit-focused config
    pil_img = Image.fromarray(thresh)
    
    # Try digit-only config first
    digit_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
    text = pytesseract.image_to_string(pil_img, config=digit_config)
    
    digits = re.sub(r'[^0-9]', '', text)
    
    if len(digits) >= 6:
        # Find first valid 6-digit PIN
        for i in range(len(digits) - 5):
            candidate = digits[i:i+6]
            if candidate[0] != '0':
                return candidate
    
    return None

def extract_text(image_bytes):
    """Extract full text from image using Tesseract OCR"""
    try:
        # Convert bytes to numpy array
        np_array = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        
        # First try to extract PIN from box region specifically
        pin_from_box = extract_pin_from_boxes(img)
        
        # Preprocess full image for text extraction
        processed = preprocess_image(img)
        pil_img = Image.fromarray(processed)
        
        # Extract full text
        full_text = pytesseract.image_to_string(
            pil_img,
            config=r'--oem 3 --psm 6'
        )

        # Fix common printed text OCR errors
        ocr_corrections = {
            'ouiarat': 'Gujarat',
            'Ouiarat': 'Gujarat', 
            'Gujrat': 'Gujarat',
            'Maharastra': 'Maharashtra',
            'Rajasthan': 'Rajasthan',
            'Tamilnadu': 'Tamil Nadu',
            'Deihi': 'Delhi',
            'Chennal': 'Chennai',
            'Mumbei': 'Mumbai',
        }
        for wrong, correct in ocr_corrections.items():
            full_text = full_text.replace(wrong, correct)
        
        # If we found PIN from box, inject it into text
        if pin_from_box:
            full_text = full_text + f"\nPIN:{pin_from_box}"
        
        return full_text.strip()
        
    except Exception as e:
        return {"error": str(e)}