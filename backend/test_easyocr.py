# backend/test_easyocr.py
import sys
import os

# Make sure backend modules are accessible
sys.path.insert(0, os.path.dirname(__file__))

from app.services.ocr_service import extract_text

# Pass image path as argument, or hardcode one
image_path = sys.argv[1] if len(sys.argv) > 1 else None

if not image_path:
    print("Usage: python test_easyocr.py path/to/envelope_image.jpg")
    sys.exit(1)

if not os.path.exists(image_path):
    print(f"File not found: {image_path}")
    sys.exit(1)

print(f"\nTesting EasyOCR on: {image_path}\n")

with open(image_path, "rb") as f:
    image_bytes = f.read()

result = extract_text(image_bytes)

if isinstance(result, dict) and "error" in result:
    print(f"❌ EasyOCR failed: {result['error']}")
else:
    print("✅ EasyOCR result:\n")
    print(result)