import re
from app.models.postal_model import get_by_pincode, get_by_district, get_by_state, get_post_offices_by_pincode

def extract_pincode(text):
    """Extract 6-digit PIN code from OCR text"""
    pattern = r'\b[1-9][0-9]{5}\b'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None

def extract_address_keywords(text):
    """Extract possible district/state keywords from text"""
    clean_text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    words = [w.strip() for w in clean_text.split() if len(w.strip()) > 3]
    return words

def validate_pin(pincode, address_keywords):
    """Validate if PIN code matches the address"""
    records = get_by_pincode(pincode)

    if not records:
        return {
            "valid": False,
            "message": "PIN code does not exist in database",
            "records": []
        }

    # Check if any keyword matches district, state or office
    matched = False
    for record in records:
        district = record.get("district", "").lower()
        state = record.get("statename", "").lower()
        office = record.get("officename", "").lower()
        division = record.get("divisionname", "").lower()
        circle = record.get("circlename", "").lower()

        for keyword in address_keywords:
            kw = keyword.lower()
            if kw in district or kw in state or kw in office or kw in division or kw in circle:
                matched = True
                break

    # Get post offices for this PIN
    post_offices = get_post_offices_by_pincode(pincode)

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
            "post_offices": post_offices
        }
    else:
        return {
            "valid": False,
            "message": "PIN code does not match the address ❌",
            "pincode": pincode,
            "records": records,
            "suggestion": suggest_correct_pin(address_keywords)
        }

def suggest_correct_pin(address_keywords):
    """Suggest correct PIN based on address keywords"""
    for keyword in address_keywords:
        # Try district match first
        district_records = get_by_district(keyword)
        if district_records:
            return {
                "suggested_pin": district_records[0].get("pincode"),
                "district": district_records[0].get("district"),
                "state": district_records[0].get("statename"),
                "circle": district_records[0].get("circlename")
            }

        # Try state match
        state_records = get_by_state(keyword)
        if state_records:
            return {
                "suggested_pin": state_records[0].get("pincode"),
                "district": state_records[0].get("district"),
                "state": state_records[0].get("statename"),
                "circle": state_records[0].get("circlename")
            }

    return None