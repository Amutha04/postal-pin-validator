from flask import Blueprint, request, jsonify
from app.services.ocr_service import extract_text
from app.services.pin_service import extract_pincode, extract_address_keywords, validate_pin

pin_bp = Blueprint('pin', __name__)

@pin_bp.route('/health', methods=['GET'])
def health():
    """Check if API is running"""
    return jsonify({"status": "API is running ✅"}), 200

@pin_bp.route('/validate', methods=['POST'])
def validate():
    """Main endpoint - accepts image, returns validation result"""
    try:
        print("📩 Request received")
        print("Files:", request.files)
        
        # Check if image is uploaded
        if 'image' not in request.files:
            print("❌ No image in request")
            return jsonify({"error": "No image uploaded"}), 400
        
        image_file = request.files['image']
        print("📁 File received:", image_file.filename)
        
        if image_file.filename == '':
            print("❌ Empty filename")
            return jsonify({"error": "No image selected"}), 400
        
        # Read image bytes
        image_bytes = image_file.read()
        print("📦 Image bytes length:", len(image_bytes))
        
        # Extract text using OCR
        print("🔍 Starting OCR...")
        extracted_text = extract_text(image_bytes)
        print("📝 Extracted text:", extracted_text)
        
        # Extract PIN and address keywords
        pincode = extract_pincode(extracted_text)
        keywords = extract_address_keywords(extracted_text)
        
        if not pincode:
            return jsonify({
        "error": "No PIN code found in image. Please make sure the PIN code is clearly visible.",
        "extracted_text": extracted_text,
        "tip": "Try uploading a clearer image with the PIN code visible"
    }), 400
        
        # Validate PIN against address
        result = validate_pin(pincode, keywords, extracted_text)
        result["extracted_text"] = extracted_text
        result["extracted_pin"] = pincode
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500