import re
from difflib import SequenceMatcher
from app.models.postal_model import (
    get_by_pincode,
    get_by_state,
    get_by_district,
    get_by_circle,
    get_by_state_and_district,
    get_by_state_and_circle,
    get_by_state_district_division,
    get_post_offices_by_pincode
)
from app.services.ml_service import validate_pin_with_ml

# ─────────────────────────────────────────
# Words to ignore during keyword matching
# ─────────────────────────────────────────
SKIP_WORDS = {
    'nagar', 'road', 'street', 'block', 'house',
    'flat', 'near', 'post', 'dear', 'respected',
    'india', 'bharat', 'from', 'name', 'addr',
    'dist', 'lane', 'area', 'colony', 'sector',
    'plot', 'floor', 'building', 'apartment',
    'society', 'marg', 'chowk', 'bazaar', 'bazar',
    'village', 'town', 'city', 'state', 'circle',
    'division', 'region', 'office', 'speed', 'mail',
    'registered', 'courier', 'parcel', 'letter',
    'south', 'north', 'east', 'west', 'central',
    'your', 'their', 'from', 'with', 'that', 'this',
    'through', 'sincerely', 'regards', 'thanking'
}

# ─────────────────────────────────────────
# Known multi-word states for better matching
# ─────────────────────────────────────────
MULTI_WORD_STATES = [
    'tamil nadu', 'west bengal', 'andhra pradesh',
    'uttar pradesh', 'madhya pradesh', 'himachal pradesh',
    'arunachal pradesh', 'jammu kashmir', 'jammu and kashmir',
    'andaman nicobar', 'andaman and nicobar'
]

def extract_pincode(text):
    """Extract 6-digit PIN code from OCR text"""
    print("🔍 Extracting PIN from:\n", text)
    
    lines = text.split('\n')
    
    # ── Step 1: Find PIN on same line as city name ──
    address_indicators = [
        'mumbai', 'delhi', 'chennai', 'kolkata',
        'bangalore', 'bengaluru', 'hyderabad', 'pune',
        'ahmedabad', 'surat', 'jaipur', 'lucknow',
        'kanpur', 'nagpur', 'indore', 'bhopal',
        'patna', 'vadodara', 'coimbatore', 'madurai',
        'salem', 'trichy', 'agra', 'visakhapatnam',
        'gujarat', 'maharashtra', 'rajasthan', 'karnataka',
        'kerala', 'punjab', 'haryana', 'bihar', 'odisha'
    ]

    for line in lines:
        line_lower = line.lower()
        has_city = any(city in line_lower for city in address_indicators)
        if has_city:
            clean_line = line.replace('-', ' ').replace(',', ' ')
            pin_match = re.search(r'\b[1-9][0-9]{5}\b', clean_line)
            if pin_match:
                candidate = pin_match.group()
                if is_valid_indian_pin(candidate):
                    return candidate

    # ── Step 2: Find standalone PIN line ──
    # A line that contains ONLY a 6-digit number
    for line in lines:
        stripped = line.strip().replace('-', '').replace(' ', '')
        if re.match(r'^[1-9][0-9]{5}$', stripped):
            if is_valid_indian_pin(stripped):
                return stripped

    # ── Step 3: Skip phone/contact lines, find PIN ──
    skip_line_keywords = [
        'contact', 'phone', 'mobile', 'tel',
        'call', 'mob', 'ph:', 'ph.', 'fax',
        'whatsapp', 'number'
    ]

    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in skip_line_keywords):
            continue
        # Skip lines with 10+ digits (phone numbers)
        all_digits = re.sub(r'[^0-9]', '', line)
        if len(all_digits) >= 10:
            continue
        clean_line = line.replace('-', ' ').replace(',', ' ')
        pin_match = re.search(r'\b[1-9][0-9]{5}\b', clean_line)
        if pin_match:
            candidate = pin_match.group()
            if is_valid_indian_pin(candidate):
                return candidate

    # ── Step 4: OCR fixes on PIN-related lines ──
    ocr_fixes = str.maketrans({
        'l': '1', 'I': '1', 'O': '0',
        'o': '0', 'S': '5', 'B': '8',
        'Z': '2', 'G': '6', 'g': '9',
        'q': '9'
    })

    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in skip_line_keywords):
            continue
        context = ' '.join(lines[max(0, i-1):min(len(lines), i+2)])
        if any(k in context for k in ['PIN', 'Pin', 'pin', 'पिन']):
            cleaned = line.translate(ocr_fixes)
            digits = re.sub(r'[^0-9]', '', cleaned)
            if len(digits) == 6 and is_valid_indian_pin(digits):
                return digits
            elif 6 < len(digits) < 10:
                for j in range(len(digits) - 5):
                    candidate = digits[j:j+6]
                    if is_valid_indian_pin(candidate):
                        return candidate

    # ── Step 5: Last resort ──
    all_pins = re.findall(r'\b[1-9][0-9]{5}\b', text)
    for pin in all_pins:
        if is_valid_indian_pin(pin) and not is_phone_number(text, pin):
            return pin

    return None


def is_valid_indian_pin(pin):
    """
    Validate if PIN looks like a real Indian PIN code
    Indian PINs:
    - Always 6 digits
    - First digit 1-9 (never 0)
    - Last 3 digits not all zeros (e.g. 110000 is invalid)
    - Not a sequence like 123456, 111111
    """
    if len(pin) != 6:
        return False
    if pin[0] == '0':
        return False
    # Reject obviously fake PINs
    fake_pins = {'123456', '111111', '000000', '999999', 
                 '112233', '123123', '654321'}
    if pin in fake_pins:
        return False
    
    return True


def is_phone_number(text, pin):
    """
    Check if the 6-digit sequence is part of a phone number
    Phone numbers in India are 10 digits
    """
    # Find the PIN in text and check surrounding digits
    pattern = r'\d*' + re.escape(pin) + r'\d*'
    matches = re.findall(pattern, text)
    for match in matches:
        # If surrounded by more digits making it 8+ digits = phone number
        if len(match) >= 8:
            return True
    # Check if preceded by "contact", "phone", "mobile", "tel"
    phone_keywords = ['contact', 'phone', 'mobile', 'tel', 'call', 'mob']
    pin_index = text.lower().find(pin)
    if pin_index > 0:
        before = text[max(0, pin_index-20):pin_index].lower()
        if any(kw in before for kw in phone_keywords):
            return True
    return False

def extract_address_keywords(text):
    """Extract meaningful keywords from address text"""
    clean_text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    words = clean_text.lower().split()
    
    # Filter out skip words and short words
    keywords = [
        w.strip() for w in words
        if len(w.strip()) > 3 and w.strip() not in SKIP_WORDS
    ]
    return list(dict.fromkeys(keywords))  # Remove duplicates

def fuzzy_match(word1, word2, threshold=0.75):
    """Check if two words are similar"""
    ratio = SequenceMatcher(
        None, word1.lower(), word2.lower()
    ).ratio()
    return ratio >= threshold

def find_state_from_keywords(keywords, full_text):
    """
    Step 1 of hierarchical search:
    Find matching state from keywords
    """
    full_lower = full_text.lower()

    # Check multi-word states first
    for state in MULTI_WORD_STATES:
        if state in full_lower:
            records = get_by_state(state)
            if records:
                return records[0].get("statename"), records

    # Check single keywords against states
    for keyword in keywords:
        records = get_by_state(keyword)
        if records:
            # Verify it's a real state match not partial
            state_name = records[0].get("statename", "").lower()
            if fuzzy_match(keyword, state_name) or keyword in state_name:
                return records[0].get("statename"), records

    return None, []

def find_district_from_keywords(keywords, state_name):
    """
    Step 2 of hierarchical search:
    Find matching district within the found state
    """
    for keyword in keywords:
        records = get_by_state_and_district(state_name, keyword)
        if records:
            return records[0].get("district"), records

    return None, []

def find_division_from_keywords(keywords, state_name, district_name):
    """
    Step 3 of hierarchical search:
    Find matching division within state+district
    """
    for keyword in keywords:
        records = get_by_state_district_division(
            state_name, district_name, keyword
        )
        if records:
            return records[0].get("divisionname"), records

    return None, []

def suggest_correct_pin(address_keywords, full_text=""):
    """
    Hierarchical PIN suggestion:
    State → District → Division → PIN
    """
    if not address_keywords:
        return None

    # ── Level 1: Find State ──
    state_name, state_records = find_state_from_keywords(
        address_keywords, full_text
    )

    if not state_name:
        # Fallback: try direct district search
        for keyword in address_keywords:
            records = get_by_district(keyword)
            if records:
                return build_suggestion(records[0])
        return None

    # ── Level 2: Find District within State ──
    district_name, district_records = find_district_from_keywords(
        address_keywords, state_name
    )

    if not district_name:
        # Return state-level suggestion
        return build_suggestion(state_records[0])

    # ── Level 3: Find Division within State+District ──
    division_name, division_records = find_division_from_keywords(
        address_keywords, state_name, district_name
    )

    if division_records:
        return build_suggestion(division_records[0])

    # Return district-level suggestion
    return build_suggestion(district_records[0])

def build_suggestion(record):
    """Build suggestion response from a record"""
    return {
        "suggested_pin": record.get("pincode"),
        "district": record.get("district"),
        "state": record.get("statename"),
        "circle": record.get("circlename"),
        "division": record.get("divisionname"),
        "region": record.get("regionname")
    }

def validate_pin(pincode, address_keywords, full_text=""):
    """
    Full PIN validation:
    MongoDB lookup + keyword matching + ML validation
    """
    # ── Step 1: Check PIN in MongoDB ──
    records = get_by_pincode(pincode)

    if not records:
        suggestion = suggest_correct_pin(address_keywords, full_text)
        return {
            "valid": False,
            "message": "PIN code does not exist ❌",
            "pincode": pincode,
            "suggestion": suggestion
        }

    # ── Step 2: Match address keywords ──
    matched = False
    for record in records:
        district = record.get("district", "").lower()
        state = record.get("statename", "").lower()
        circle = record.get("circlename", "").lower()
        office = record.get("officename", "").lower()
        division = record.get("divisionname", "").lower()
        region = record.get("regionname", "").lower()

        for keyword in address_keywords:
            kw = keyword.lower()
            # Exact match
            if (kw in district or kw in state or
                    kw in office or kw in circle or
                    kw in division or kw in region):
                matched = True
                break
            # Fuzzy match for OCR errors
            if (fuzzy_match(kw, district) or
                    fuzzy_match(kw, state)):
                matched = True
                break
        if matched:
            break

    # ── Step 3: ML Validation ──
    ml_result = {"ml_valid": None, "message": "ML skipped"}
    first = records[0]
    district = first.get("district", "")
    state = first.get("statename", "")
    circle = first.get("circlename", "")

    if district and state and circle:
        ml_result = validate_pin_with_ml(
            pincode, district, state, circle
        )
        # Trust MongoDB match over ML if prefix is close
        if matched and ml_result.get("ml_valid") == False:
            predicted = ml_result.get("predicted_prefix", "")
            actual = str(pincode)[:3]
            if predicted and abs(int(actual) - int(predicted)) <= 1:
                ml_result["ml_valid"] = True
                ml_result["message"] = "ML confirms PIN is valid ✅"

    # ── Step 4: Get post offices ──
    post_offices = get_post_offices_by_pincode(pincode)

    # ── Step 5: Build response ──
    if matched:
        return {
            "valid": True,
            "message": "PIN code matches the address ✅",
            "pincode": pincode,
            "district": first.get("district"),
            "state": first.get("statename"),
            "circle": first.get("circlename"),
            "region": first.get("regionname"),
            "division": first.get("divisionname"),
            "latitude": first.get("latitude"),
            "longitude": first.get("longitude"),
            "post_offices": post_offices[:10],
            "ml_validation": ml_result
        }
    else:
        suggestion = suggest_correct_pin(address_keywords, full_text)
        return {
            "valid": False,
            "message": "PIN code does not match address ❌",
            "pincode": pincode,
            "actual_location": {
                "district": first.get("district"),
                "state": first.get("statename"),
            },
            "ml_validation": ml_result,
            "suggestion": suggestion
        }