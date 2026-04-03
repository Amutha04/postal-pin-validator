import re
from app.models.postal_model import (
    get_by_pincode, 
    get_by_district, 
    get_by_state,
    get_post_offices_by_pincode
)
from app.services.ml_service import validate_pin_with_ml

def extract_pincode(text):
    """Extract 6-digit PIN code from OCR text"""
    pattern = r'\b[1-9][0-9]{5}\b'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None

def extract_address_keywords(text):
    """Extract keywords from OCR text"""
    clean_text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    words = [w.strip() for w in clean_text.split() 
             if len(w.strip()) > 3]
    return words

def validate_pin(pincode, address_keywords):
    """
    Full validation combining MongoDB + ML
    """
    # ── Step 1: Check PIN exists in MongoDB ──
    records = get_by_pincode(pincode)

    if not records:
        suggestion = suggest_correct_pin(address_keywords)
        return {
            "valid": False,
            "message": "PIN code does not exist ❌",
            "pincode": pincode,
            "suggestion": suggestion
        }

    # ── Step 2: Check address keywords match ──
    matched = False
    matched_record = None

    for record in records:
        district = record.get("district", "").lower()
        state = record.get("statename", "").lower()
        circle = record.get("circlename", "").lower()
        office = record.get("officename", "").lower()

        for keyword in address_keywords:
            kw = keyword.lower()
            if (kw in district or kw in state or 
                kw in office or kw in circle):
                matched = True
                matched_record = record
                break
        if matched:
            break

    # ── Step 3: ML Validation ──
    ml_result = {"ml_valid": None, "message": "ML skipped"}

    if records:
        first = records[0]
        district = first.get("district", "")
        state = first.get("statename", "")
        circle = first.get("circlename", "")

        if district and state and circle:
            ml_result = validate_pin_with_ml(
                pincode, district, state, circle
            )

    # ── Step 4: Get post offices ──
    post_offices = get_post_offices_by_pincode(pincode)

    # ── Step 5: Build response ──
    if matched:
        return {
            "valid": True,
            "message": "PIN code matches the address ✅",
            "pincode": pincode,
            "district": records[0].get("district"),
            "state": records[0].get("statename"),
            "circle": records[0].get("circlename"),
            "region": records[0].get("regionname"),
            "division": records[0].get("divisionname"),
            "latitude": records[0].get("latitude"),
            "longitude": records[0].get("longitude"),
            "post_offices": post_offices[:10],  # Top 10
            "ml_validation": ml_result
        }
    else:
        suggestion = suggest_correct_pin(address_keywords)
        return {
            "valid": False,
            "message": "PIN code does not match address ❌",
            "pincode": pincode,
            "actual_location": {
                "district": records[0].get("district"),
                "state": records[0].get("statename"),
            },
            "ml_validation": ml_result,
            "suggestion": suggestion
        }

def suggest_correct_pin(address_keywords):
    """Suggest correct PIN from address keywords"""
    for keyword in address_keywords:
        district_records = get_by_district(keyword)
        if district_records:
            return {
                "suggested_pin": district_records[0].get("pincode"),
                "district": district_records[0].get("district"),
                "state": district_records[0].get("statename"),
                "circle": district_records[0].get("circlename")
            }
        state_records = get_by_state(keyword)
        if state_records:
            return {
                "suggested_pin": state_records[0].get("pincode"),
                "district": state_records[0].get("district"),
                "state": state_records[0].get("statename"),
                "circle": state_records[0].get("circlename")
            }
    return None