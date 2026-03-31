import re
from app.models.postal_model import get_by_pincode, get_by_district, get_by_state

def extract_pincode(text):
    """Extract 6-digit PIN code from OCR text"""
    # Indian PIN codes are always 6 digits
    pattern = r'\b[1-9][0-9]{5}\b'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None

def extract_address_keywords(text):
    """Extract possible district/state keywords from text"""
    # Clean text
    clean_text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    words = [w.strip() for w in clean_text.split() if len(w.strip()) > 3]
    return words

def validate_pin(pincode, address_keywords):
    """Validate if PIN code matches the address"""
    # Get records for this PIN
    records = get_by_pincode(pincode)
    
    if not records:
        return {
            "valid": False,
            "message": "PIN code does not exist in database",
            "records": []
        }
    
    # Check if any address keyword matches district or state
    matched = False
    for record in records:
        district = record.get("District", "").lower()
        state = record.get("StateName", "").lower()
        office = record.get("OfficeName", "").lower()
        
        for keyword in address_keywords:
            if keyword.lower() in district or keyword.lower() in state or keyword.lower() in office:
                matched = True
                break
    
    if matched:
        return {
            "valid": True,
            "message": "PIN code matches the address ✅",
            "records": records
        }
    else:
        return {
            "valid": False,
            "message": "PIN code does not match the address ❌",
            "records": records,
            "suggestion": suggest_correct_pin(address_keywords)
        }

def suggest_correct_pin(address_keywords):
    """Suggest correct PIN based on address keywords"""
    for keyword in address_keywords:
        # Try district match
        district_records = get_by_district(keyword)
        if district_records:
            return {
                "suggested_pin": district_records[0].get("Pincode"),
                "location": district_records[0].get("District"),
                "state": district_records[0].get("StateName")
            }
        
        # Try state match
        state_records = get_by_state(keyword)
        if state_records:
            return {
                "suggested_pin": state_records[0].get("Pincode"),
                "location": state_records[0].get("District"),
                "state": state_records[0].get("StateName")
            }
    
    return None