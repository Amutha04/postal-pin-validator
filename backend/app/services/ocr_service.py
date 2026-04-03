import pytesseract
import cv2
import numpy as np
from PIL import Image
import re
from config import Config

pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_PATH

def preprocess_image(img):
    """Standard preprocessing for OCR"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=30)
    _, thresh = cv2.threshold(
        denoised, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return thresh

def preprocess_image_sharp(img):
    """Sharper preprocessing for better digit recognition"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(
        gray, None, fx=2, fy=2,
        interpolation=cv2.INTER_CUBIC
    )
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    sharpened = cv2.filter2D(scaled, -1, kernel)
    _, thresh = cv2.threshold(
        sharpened, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return thresh

def extract_text(image_bytes):
    """Extract full text from image using Tesseract OCR"""
    try:
        np_array = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        results = []

        # ── Method 1: Standard preprocessing ──
        try:
            processed1 = preprocess_image(img)
            pil1 = Image.fromarray(processed1)
            text1 = pytesseract.image_to_string(
                pil1, config=r'--oem 3 --psm 6'
            )
            results.append(text1)
            print(f"✅ Method 1 digits: {len(re.sub(r'[^0-9]', '', text1))}")
        except Exception as e:
            print(f"⚠️ Method 1 failed: {e}")

        # ── Method 2: Sharp preprocessing ──
        try:
            processed2 = preprocess_image_sharp(img)
            pil2 = Image.fromarray(processed2)
            text2 = pytesseract.image_to_string(
                pil2, config=r'--oem 3 --psm 6'
            )
            results.append(text2)
            print(f"✅ Method 2 digits: {len(re.sub(r'[^0-9]', '', text2))}")
        except Exception as e:
            print(f"⚠️ Method 2 failed: {e}")

        # ── Method 3: Original image different PSM ──
        try:
            pil3 = Image.fromarray(
                cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            )
            text3 = pytesseract.image_to_string(
                pil3, config=r'--oem 3 --psm 4'
            )
            results.append(text3)
            print(f"✅ Method 3 digits: {len(re.sub(r'[^0-9]', '', text3))}")
        except Exception as e:
            print(f"⚠️ Method 3 failed: {e}")

        # ── Method 4: Scaled up original ──
        try:
            height, width = img.shape[:2]
            scaled_img = cv2.resize(
                img, (width*2, height*2),
                interpolation=cv2.INTER_CUBIC
            )
            gray_scaled = cv2.cvtColor(scaled_img, cv2.COLOR_BGR2GRAY)
            pil4 = Image.fromarray(gray_scaled)
            text4 = pytesseract.image_to_string(
                pil4, config=r'--oem 3 --psm 6'
            )
            results.append(text4)
            print(f"✅ Method 4 digits: {len(re.sub(r'[^0-9]', '', text4))}")
        except Exception as e:
            print(f"⚠️ Method 4 failed: {e}")

        if not results:
            return {"error": "All OCR methods failed"}

        # ── Pick result with most digits ──
        best_text = max(
            results,
            key=lambda t: len(re.sub(r'[^0-9]', '', t))
        )

        # ── Fix common OCR errors ──
        ocr_corrections = {
            'ouiarat': 'Gujarat', 'Ouiarat': 'Gujarat',
            'Gujerat': 'Gujarat', 'Gujrat': 'Gujarat',
            'Mumbat': 'Mumbai', 'Mumbay': 'Mumbai',
            'Deihi': 'Delhi', 'Delni': 'Delhi',
            'Chennal': 'Chennai', 'Channai': 'Chennai',
            'Kolkota': 'Kolkata', 'Calcuta': 'Kolkata',
            'Bangalor': 'Bangalore', 'Bengalur': 'Bangalore',
            'Hydrabad': 'Hyderabad',
        }
        for wrong, correct in ocr_corrections.items():
            best_text = best_text.replace(wrong, correct)

        print("✅ Best OCR result:\n", best_text)
        return best_text.strip()

    except Exception as e:
        print(f"❌ OCR failed: {e}")
        return {"error": str(e)}