import easyocr
import cv2
import numpy as np
import re

# Initialize EasyOCR reader once (loads model on first call)
reader = None


def get_reader():
    global reader
    if reader is None:
        print("[INFO] Loading EasyOCR model (first time may take a moment)...")
        reader = easyocr.Reader(['en'], gpu=False)
        print("[OK] EasyOCR model loaded")
    return reader


def preprocess_clahe(img, scale=2):
    """CLAHE contrast enhancement — good for handwritten text"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(gray, None, fx=scale, fy=scale,
                        interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    return clahe.apply(scaled)


def preprocess_adaptive(img):
    """Gentle denoise + adaptive threshold — works on uneven lighting"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    return cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )

def preprocess_otsu(img):
    """OTSU binarization — best for printed text on plain backgrounds"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Scale up for better character recognition
    scaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    # Remove noise before thresholding
    blurred = cv2.GaussianBlur(scaled, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def preprocess_sharpen(img):
    """Sharpening — helps when image is slightly blurry"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(scaled, -1, kernel)


def score_ocr_result(text):
    """Score OCR quality — PIN detection is the top priority"""
    pin_found = 1 if re.search(r'\b[1-9]\d{5}\b', text) else 0
    word_count = len(re.findall(r'[a-zA-Z]{3,}', text))
    digit_count = len(re.sub(r'[^0-9]', '', text))
    return (pin_found * 1000) + (word_count * 2) + digit_count


def run_easyocr(img):
    """Run EasyOCR on an image and return joined text"""
    r = get_reader()
    results = r.readtext(img, detail=0, paragraph=True)
    return "\n".join(results)


def extract_text(image_bytes):
    """Extract full text from image using EasyOCR"""
    try:
        np_array = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if img is None:
            return {"error": "Could not decode image"}

        # Try multiple preprocessing methods
        candidates = []

        # Method 1: Raw image (EasyOCR handles preprocessing internally)
        print("[INFO] EasyOCR: trying raw image...")
        text_raw = run_easyocr(img)
        candidates.append(text_raw)
        print(f"[OK] Raw: score={score_ocr_result(text_raw)}")

        # Method 2: CLAHE enhanced
        print("[INFO] EasyOCR: trying CLAHE enhanced...")
        clahe_img = preprocess_clahe(img)
        text_clahe = run_easyocr(clahe_img)
        candidates.append(text_clahe)
        print(f"[OK] CLAHE: score={score_ocr_result(text_clahe)}")

        # Method 3: Adaptive threshold
        print("[INFO] EasyOCR: trying adaptive threshold...")
        adaptive_img = preprocess_adaptive(img)
        text_adaptive = run_easyocr(adaptive_img)
        candidates.append(text_adaptive)
        print(f"[OK] Adaptive: score={score_ocr_result(text_adaptive)}")

        # Method 4: OTSU binarization (add after Method 3)
        print("[INFO] EasyOCR: trying OTSU binarization...")
        otsu_img = preprocess_otsu(img)
        text_otsu = run_easyocr(otsu_img)
        candidates.append(text_otsu)
        print(f"[OK] OTSU: score={score_ocr_result(text_otsu)}")

        # Method 5: Sharpening
        print("[INFO] EasyOCR: trying sharpening...")
        sharp_img = preprocess_sharpen(img)
        text_sharp = run_easyocr(sharp_img)
        candidates.append(text_sharp)
        print(f"[OK] Sharp: score={score_ocr_result(text_sharp)}")

        # If no PIN found in any, try 180-degree rotation
        best_so_far = max(candidates, key=score_ocr_result)
        if not re.search(r'\b[1-9]\d{5}\b', best_so_far):
            print("[INFO] No PIN found, trying 180-degree rotation...")
            h, w = img.shape[:2]
            center = (w // 2, h // 2)
            matrix = cv2.getRotationMatrix2D(center, 180, 1.0)
            rotated = cv2.warpAffine(img, matrix, (w, h),
                                     borderValue=(255, 255, 255))
            text_rotated = run_easyocr(rotated)
            candidates.append(text_rotated)
            print(f"[OK] Rotated: score={score_ocr_result(text_rotated)}")

        if not candidates:
            return {"error": "All OCR methods failed"}

        # Pick best result
        best_text = max(candidates, key=score_ocr_result)

        # Fix common OCR errors
        ocr_corrections = {
            'ouiarat': 'Gujarat', 'Ouiarat': 'Gujarat',
            'Gujerat': 'Gujarat', 'Gujrat': 'Gujarat',
            'Mumbat': 'Mumbai', 'Mumbay': 'Mumbai',
            'Deihi': 'Delhi', 'Delni': 'Delhi',
            'Chennal': 'Chennai', 'Channai': 'Chennai',
            'Kolkota': 'Kolkata', 'Calcuta': 'Kolkata',
            'Bangalor': 'Bangalore', 'Bengalur': 'Bangalore',
            'Hydrabad': 'Hyderabad',
            'Bangatore': 'Bangalore', 'Bangalure': 'Bangalore',
        }
        for wrong, correct in ocr_corrections.items():
            best_text = best_text.replace(wrong, correct)

        print("[OK] Best OCR result:\n", best_text)
        return best_text.strip()

    except Exception as e:
        print(f"[ERROR] OCR failed: {e}")
        return {"error": str(e)}
