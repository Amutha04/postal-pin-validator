import pytesseract
import cv2
import numpy as np
from PIL import Image
from config import Config

# Set tesseract path
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_PATH

def preprocess_image(image_bytes):
    """Convert image bytes to OpenCV format and preprocess"""
    # Convert bytes to numpy array
    np_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Remove noise
    denoised = cv2.fastNlMeansDenoising(gray, h=30)
    
    # Apply thresholding
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

def extract_text(image_bytes):
    """Extract text from image using Tesseract OCR"""
    try:
        # Preprocess image
        processed_img = preprocess_image(image_bytes)
        
        # Convert back to PIL Image for pytesseract
        pil_img = Image.fromarray(processed_img)
        
        # Extract text
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(pil_img, config=custom_config)
        
        return text.strip()
    except Exception as e:
        return {"error": str(e)}