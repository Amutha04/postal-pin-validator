from flask import Blueprint, request, jsonify
from config import Config
from app.services.ocr_service import extract_text
from app.services.pin_service import extract_pincode, extract_address_keywords, validate_pin
from app.models.postal_model import get_by_pincode, get_post_offices_by_pincode, get_nearby_pincodes
from app.services.ml_service import validate_pin_with_ml

pin_bp = Blueprint('pin', __name__)

# Load Gemini service only if enabled
if Config.USE_GEMINI and Config.GEMINI_API_KEYS:
    from app.services.gemini_ocr_service import extract_with_gemini
    print("[OK] Gemini OCR enabled")
else:
    extract_with_gemini = None
    print("[INFO] Using EasyOCR (Gemini not configured)")


@pin_bp.route('/health', methods=['GET'])
def health():
    """Check if API is running"""
    ocr_engine = "Gemini 2.5 Flash" if extract_with_gemini else "EasyOCR"
    return jsonify({"status": "API is running", "ocr_engine": ocr_engine}), 200


@pin_bp.route('/lookup', methods=['POST'])
def lookup():
    """Manual PIN lookup — no image needed"""
    try:
        data = request.get_json()
        pincode = data.get('pincode', '').strip()

        if not pincode or len(pincode) != 6 or not pincode.isdigit():
            return jsonify({"error": "Please enter a valid 6-digit PIN code"}), 400

        records = get_by_pincode(pincode)

        if not records:
            return jsonify({
                "valid": False,
                "message": "PIN code does not exist in database",
                "pincode": pincode
            }), 200

        first = records[0]
        district = first.get("district", "")
        state = first.get("statename", "")
        circle = first.get("circlename", "")

        ml_result = {"ml_valid": None, "message": "ML skipped"}
        if district and state and circle:
            ml_result = validate_pin_with_ml(pincode, district, state, circle)

        post_offices = get_post_offices_by_pincode(pincode)

        return jsonify({
            "valid": True,
            "message": "PIN code found",
            "pincode": pincode,
            "district": district,
            "state": state,
            "circle": circle,
            "region": first.get("regionname"),
            "division": first.get("divisionname"),
            "latitude": first.get("latitude"),
            "longitude": first.get("longitude"),
            "post_offices": post_offices[:10],
            "ml_validation": ml_result,
            "lookup": True
        }), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500


@pin_bp.route('/nearby', methods=['POST'])
def nearby():
    """Find nearby PIN codes given lat/lng"""
    try:
        data = request.get_json()
        lat = float(data.get('lat', 0))
        lng = float(data.get('lng', 0))
        exclude_pin = data.get('exclude', '')

        results = get_nearby_pincodes(lat, lng)
        nearby = []
        for r in results:
            pin = str(r.get('pincode', ''))
            if pin == str(exclude_pin):
                continue
            rlat = r.get('latitude')
            rlng = r.get('longitude')
            if rlat and rlng and rlat != 'NA' and rlng != 'NA':
                nearby.append({
                    'pincode': pin,
                    'officename': r.get('officename', ''),
                    'district': r.get('district', ''),
                    'latitude': float(rlat),
                    'longitude': float(rlng),
                    'delivery': r.get('delivery', ''),
                })
        return jsonify(nearby), 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify([]), 200


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
                print("[ERROR] Gemini failed, falling back to EasyOCR...")
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
        if "error" in gemini_result or not gemini_result.get("text"):
            print("[INFO] Gemini returned no usable result, falling back to EasyOCR...")
            return _process_with_tesseract(image_bytes)

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500


def _process_with_tesseract(image_bytes):
    """EasyOCR-based processing"""
    print("[INFO] Starting EasyOCR...")
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
    result["ocr_engine"] = "EasyOCR"

    return jsonify(result), 200
