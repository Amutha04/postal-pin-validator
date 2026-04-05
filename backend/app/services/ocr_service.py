import pytesseract
import cv2
import numpy as np
from PIL import Image
import re
from config import Config

pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_PATH


def preprocess_clahe_raw(img, clip=3.0, scale=2):
    """CLAHE contrast on grayscale, no thresholding — best for handwritten text"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(gray, None, fx=scale, fy=scale,
                        interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8))
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


def preprocess_clahe_thresh(img):
    """CLAHE + adaptive threshold — good for colored/brown envelopes"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    scaled = cv2.resize(enhanced, None, fx=2, fy=2,
                        interpolation=cv2.INTER_CUBIC)
    return cv2.adaptiveThreshold(
        scaled, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 21, 15
    )


def preprocess_sharp_scaled(img):
    """Scale 2x + unsharp mask + adaptive threshold"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(gray, None, fx=2, fy=2,
                        interpolation=cv2.INTER_CUBIC)
    blurred = cv2.GaussianBlur(scaled, (0, 0), 3)
    sharpened = cv2.addWeighted(scaled, 1.5, blurred, -0.5, 0)
    return cv2.adaptiveThreshold(
        sharpened, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )


def score_ocr_result(text):
    """Score OCR quality — PIN detection is the top priority"""
    pin_found = 1 if re.search(r'\b[1-9]\d{5}\b', text) else 0
    word_count = len(re.findall(r'[a-zA-Z]{3,}', text))
    digit_count = len(re.sub(r'[^0-9]', '', text))
    # PIN found is worth far more than word/digit count
    return (pin_found * 1000) + (word_count * 2) + digit_count


def run_ocr_on_image(img):
    """Run all preprocessing methods on a single image orientation, return results"""
    methods = [
        ("CLAHE raw psm11", lambda i: preprocess_clahe_raw(i, 3.0, 2), '--oem 3 --psm 11'),
        ("CLAHE raw psm6", lambda i: preprocess_clahe_raw(i, 3.0, 2), '--oem 3 --psm 6'),
        ("CLAHE raw psm3", lambda i: preprocess_clahe_raw(i, 3.0, 2), '--oem 3 --psm 3'),
        ("CLAHE+thresh psm6", lambda i: preprocess_clahe_thresh(i), '--oem 3 --psm 6'),
        ("CLAHE+thresh psm4", lambda i: preprocess_clahe_thresh(i), '--oem 3 --psm 4'),
        ("Adaptive psm6", lambda i: preprocess_adaptive(i), '--oem 3 --psm 6'),
        ("Sharp scaled psm6", lambda i: preprocess_sharp_scaled(i), '--oem 3 --psm 6'),
    ]

    results = []
    for name, preprocess_fn, psm_config in methods:
        try:
            processed = preprocess_fn(img)
            pil_img = Image.fromarray(processed)
            text = pytesseract.image_to_string(pil_img, config=psm_config)
            score = score_ocr_result(text)
            results.append(text)
            print(f"[OK] {name}: score={score}")
        except Exception as e:
            print(f"[WARN] {name} failed: {e}")

    return results


def extract_text(image_bytes):
    """Extract full text from image using Tesseract OCR"""
    try:
        np_array = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if img is None:
            return {"error": "Could not decode image"}

        # Try original orientation first
        print("[INFO] Trying original orientation...")
        results = run_ocr_on_image(img)

        # Check if we got a PIN from original
        best_original = max(results, key=score_ocr_result) if results else ""
        original_has_pin = bool(re.search(r'\b[1-9]\d{5}\b', best_original))

        # If no PIN found, try 180-degree rotation
        if not original_has_pin:
            print("[INFO] No PIN found, trying 180-degree rotation...")
            h, w = img.shape[:2]
            center = (w // 2, h // 2)
            matrix = cv2.getRotationMatrix2D(center, 180, 1.0)
            rotated = cv2.warpAffine(img, matrix, (w, h),
                                     borderValue=(255, 255, 255))
            rotated_results = run_ocr_on_image(rotated)
            results.extend(rotated_results)

        if not results:
            return {"error": "All OCR methods failed"}

        # Pick result with best quality score
        best_text = max(results, key=score_ocr_result)

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
