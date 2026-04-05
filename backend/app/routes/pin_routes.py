from flask import Blueprint, request, jsonify
from config import Config
from app.services.ocr_service import extract_text
from app.services.pin_service import extract_pincode, extract_address_keywords, validate_pin

pin_bp = Blueprint('pin', __name__)

# Load Gemini service only if enabled
if Config.USE_GEMINI and Config.GEMINI_API_KEY:
    from app.services.gemini_ocr_service import extract_with_gemini
    print("[OK] Gemini OCR enabled")
else:
    extract_with_gemini = None
    print("[INFO] Using Tesseract OCR (Gemini not configured)")


@pin_bp.route('/health', methods=['GET'])
def health():
    """Check if API is running"""
    ocr_engine = "Gemini 2.5 Flash" if extract_with_gemini else "Tesseract"
    return jsonify({"status": "API is running", "ocr_engine": ocr_engine}), 200


@pin_bp.route('/validate', methods=['POST'])
def validate():
    """Main endpoint - accepts image, returns validation result"""
    try:
        print("[INFO] Request received")

        if 'image' not in request.files:
            print("[ERROR] No image in request")
            return jsonify({"error": "No image uploaded"}), 400

        image_file = request.files['image']
        print("[INFO] File received:", image_file.filename)

        if image_file.filename == '':
            print("[ERROR] Empty filename")
            return jsonify({"error": "No image selected"}), 400

        image_bytes = image_file.read()
        print("[INFO] Image bytes length:", len(image_bytes))

        # ── Gemini Vision path ──
        if extract_with_gemini:
            print("[INFO] Using Gemini Vision...")
            gemini_result = extract_with_gemini(image_bytes)

            if "error" in gemini_result:
                print("[ERROR] Gemini failed, falling back to Tesseract...")
                return _process_with_tesseract(image_bytes)

            extracted_text = gemini_result["text"]
            pincode = gemini_result.get("pincode") or None

            # If Gemini didn't extract a PIN, try the regex extractor
            if not pincode:
                pincode = extract_pincode(extracted_text)

            keywords = extract_address_keywords(extracted_text)

            # Also add structured fields as keywords for better matching
            structured = gemini_result.get("structured")
            if structured:
                recipient = structured.get("recipient", {})
                for field in ["city", "district", "state"]:
                    val = recipient.get(field, "")
                    if val and len(val) > 2:
                        keywords.append(val.lower())

            if not pincode:
                return jsonify({
                    "error": "No PIN code found in image. Please make sure the PIN code is clearly visible.",
                    "extracted_text": extracted_text,
                    "tip": "Try uploading a clearer image with the PIN code visible"
                }), 400

            result = validate_pin(pincode, keywords, extracted_text)
            result["extracted_text"] = extracted_text
            result["extracted_pin"] = pincode
            result["ocr_engine"] = "Gemini 2.5 Flash"
            if structured:
                result["gemini_data"] = structured

            return jsonify(result), 200

        # ── Tesseract fallback path ──
        else:
            return _process_with_tesseract(image_bytes)

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500


def _process_with_tesseract(image_bytes):
    """Original Tesseract-based processing"""
    print("[INFO] Starting Tesseract OCR...")
    extracted_text = extract_text(image_bytes)

    if isinstance(extracted_text, dict) and "error" in extracted_text:
        print("[ERROR] OCR Error:", extracted_text)
        return jsonify(extracted_text), 500

    if not isinstance(extracted_text, str):
        return jsonify({"error": "OCR failed to extract text"}), 500

    pincode = extract_pincode(extracted_text)
    keywords = extract_address_keywords(extracted_text)

    if not pincode:
        return jsonify({
            "error": "No PIN code found in image. Please make sure the PIN code is clearly visible.",
            "extracted_text": extracted_text,
            "tip": "Try uploading a clearer image with the PIN code visible"
        }), 400

    result = validate_pin(pincode, keywords, extracted_text)
    result["extracted_text"] = extracted_text
    result["extracted_pin"] = pincode
    result["ocr_engine"] = "Tesseract"

    return jsonify(result), 200
