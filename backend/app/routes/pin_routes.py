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
        # Check if image is uploaded
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        
        image_file = request.files['image']
        
        if image_file.filename == '':
            return jsonify({"error": "No image selected"}), 400
        
        # Read image bytes
        image_bytes = image_file.read()
        
        # Extract text using OCR
        extracted_text = extract_text(image_bytes)
        
        if isinstance(extracted_text, dict) and "error" in extracted_text:
            return jsonify(extracted_text), 500
        
        # Extract PIN and address keywords
        pincode = extract_pincode(extracted_text)
        keywords = extract_address_keywords(extracted_text)
        
        if not pincode:
            return jsonify({
                "error": "No PIN code found in image",
                "extracted_text": extracted_text
            }), 400
        
        # Validate PIN against address
        result = validate_pin(pincode, keywords)
        result["extracted_text"] = extracted_text
        result["extracted_pin"] = pincode
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500