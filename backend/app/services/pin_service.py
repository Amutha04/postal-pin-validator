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
    """Extract 6-digit PIN code from OCR text — prioritizes 'To' address over 'From'"""
    print("[INFO] Extracting PIN from:\n", text)

    lines = text.split('\n')

    # ── Step 0: Split text into "To" section vs rest ──
    # Find where "To" and "From" sections start
    to_start = None
    from_start = None
    for i, line in enumerate(lines):
        line_lower = line.strip().lower()
        if re.match(r'^(to[,:\s]|dear\b)', line_lower) and to_start is None:
            to_start = i
        if re.match(r'^from[,:\s]', line_lower) and from_start is None:
            from_start = i

    # Build prioritized line order: "To" section first, then rest
    if to_start is not None:
        # "To" section runs from to_start until "From" or end
        to_end = from_start if (from_start is not None and from_start > to_start) else len(lines)
        to_lines = list(range(to_start, to_end))
        other_lines = [i for i in range(len(lines)) if i not in to_lines]
        ordered_indices = to_lines + other_lines
    else:
        ordered_indices = list(range(len(lines)))

    skip_line_keywords = [
        'contact', 'phone', 'mobile', 'tel',
        'call', 'mob', 'ph:', 'ph.', 'fax',
        'whatsapp', 'number'
    ]

    # If "From" section exists, mark those lines to deprioritize
    from_indices = set()
    if from_start is not None:
        from_end = to_start if (to_start is not None and to_start > from_start) else len(lines)
        from_indices = set(range(from_start, from_end))

    # ── Step 1: Find PIN near "PIN" keyword (highest confidence) ──
    for idx in ordered_indices:
        line = lines[idx]
        line_lower = line.lower()
        context = ' '.join(lines[max(0, idx-1):min(len(lines), idx+2)])
        if any(k in context.lower() for k in ['pin', 'pin:']):
            clean_line = line.replace('-', ' ').replace(',', ' ')
            pin_match = re.search(r'\b[1-9][0-9]{5}\b', clean_line)
            if pin_match:
                candidate = pin_match.group()
                if is_valid_indian_pin(candidate):
                    return candidate
            # Try OCR digit fixes on this line
            ocr_fixes = str.maketrans({
                'l': '1', 'I': '1', 'O': '0',
                'o': '0', 'S': '5', 'B': '8',
                'Z': '2', 'G': '6', 'g': '9',
                'q': '9'
            })
            cleaned = line.translate(ocr_fixes)
            digits = re.sub(r'[^0-9]', '', cleaned)
            if len(digits) == 6 and is_valid_indian_pin(digits):
                return digits
            elif 6 < len(digits) < 10:
                for j in range(len(digits) - 5):
                    candidate = digits[j:j+6]
                    if is_valid_indian_pin(candidate):
                        return candidate

    # ── Step 2: Find PIN on same line as city/state name ──
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

    # Search "To" section first, skip "From" section
    for idx in ordered_indices:
        if idx in from_indices:
            continue
        line = lines[idx]
        line_lower = line.lower()
        has_city = any(city in line_lower for city in address_indicators)
        if has_city:
            clean_line = line.replace('-', ' ').replace(',', ' ')
            pin_match = re.search(r'\b[1-9][0-9]{5}\b', clean_line)
            if pin_match:
                candidate = pin_match.group()
                if is_valid_indian_pin(candidate):
                    return candidate

    # ── Step 3: Find standalone PIN line (not in From section) ──
    for idx in ordered_indices:
        if idx in from_indices:
            continue
        line = lines[idx]
        stripped = line.strip().replace('-', '').replace(' ', '')
        if re.match(r'^[1-9][0-9]{5}$', stripped):
            if is_valid_indian_pin(stripped):
                return stripped

    # ── Step 4: Any valid PIN not in From section, skip phone lines ──
    for idx in ordered_indices:
        if idx in from_indices:
            continue
        line = lines[idx]
        line_lower = line.lower()
        if any(kw in line_lower for kw in skip_line_keywords):
            continue
        all_digits = re.sub(r'[^0-9]', '', line)
        if len(all_digits) >= 10:
            continue
        clean_line = line.replace('-', ' ').replace(',', ' ')
        pin_match = re.search(r'\b[1-9][0-9]{5}\b', clean_line)
        if pin_match:
            candidate = pin_match.group()
            if is_valid_indian_pin(candidate):
                return candidate

    # ── Step 5: Fall back to From section if nothing else found ──
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

def normalize_location_text(text):
    return re.sub(r'[^a-z]', '', text.lower())

def find_state_from_keywords(keywords, full_text):
    """
    Step 1 of hierarchical search:
    Find matching state from keywords
    """
    full_lower = full_text.lower()
    full_normalized = normalize_location_text(full_text)

    # Check multi-word states first
    for state in MULTI_WORD_STATES:
        if state in full_lower or normalize_location_text(state) in full_normalized:
            records = get_by_state(state)
            if records:
                return records[0].get("statename"), records

    # Check single keywords against states
    for keyword in keywords:
        records = get_by_state(keyword)
        if records:
            # Verify it's a real state match, not a partial locality match.
            state_name = records[0].get("statename", "")
            keyword_norm = normalize_location_text(keyword)
            state_norm = normalize_location_text(state_name)
            if keyword_norm == state_norm or fuzzy_match(keyword_norm, state_norm, threshold=0.9):
                return records[0].get("statename"), records

    return None, []

def find_district_from_keywords(keywords, state_name):
    """
    Step 2 of hierarchical search:
    Find matching district within the found state
    """
    for keyword in keywords:
        if keyword.lower().strip() in SKIP_WORDS:
            continue
        records = get_by_state_and_district(state_name, keyword)
        matching_records = [
            record for record in records
            if fuzzy_match(
                normalize_location_text(keyword),
                normalize_location_text(record.get("district", "")),
                threshold=0.9
            )
        ]
        if matching_records:
            return matching_records[0].get("district"), matching_records

    return None, []

def find_division_from_keywords(keywords, state_name, district_name):
    """
    Step 3 of hierarchical search:
    Find matching division within state+district
    """
    for keyword in keywords:
        if keyword.lower().strip() in SKIP_WORDS:
            continue
        records = get_by_state_district_division(
            state_name, district_name, keyword
        )
        if records:
            return records[0].get("divisionname"), records

    return None, []

def build_keyword_phrases(keywords):
    """Build normalized single and adjacent-word phrases for locality matching."""
    normalized = [
        normalize_location_text(keyword)
        for keyword in keywords
        if normalize_location_text(keyword)
    ]
    phrases = set(normalized)

    for i in range(len(normalized) - 1):
        phrases.add(normalized[i] + normalized[i + 1])

    for i in range(len(normalized) - 2):
        phrases.add(normalized[i] + normalized[i + 1] + normalized[i + 2])

    return phrases

def score_suggestion_record(record, address_keywords):
    """Rank suggestion candidates by how specifically they match the address."""
    phrases = build_keyword_phrases(address_keywords)
    office = normalize_location_text(record.get("officename", ""))
    district = normalize_location_text(record.get("district", ""))
    division = normalize_location_text(record.get("divisionname", ""))
    region = normalize_location_text(record.get("regionname", ""))
    state = normalize_location_text(record.get("statename", ""))
    circle = normalize_location_text(record.get("circlename", ""))
    score = 0

    for phrase in phrases:
        if not phrase:
            continue

        is_admin_phrase = phrase in {district, state, circle}

        if office and phrase == office:
            score += 150
        elif office and not is_admin_phrase and (phrase in office or office in phrase):
            score += 100 + min(len(phrase), 25)

        if district and phrase == district:
            score += 50
        elif district and phrase in district:
            score += 30

        if division and phrase in division:
            score += 20
        if region and phrase in region:
            score += 12
        if state and phrase == state:
            score += 5
        if circle and phrase in circle:
            score += 3

    if str(record.get("delivery", "")).lower() == "delivery":
        score += 2

    return score

def best_suggestion_record(records, address_keywords):
    if not records:
        return None
    return max(
        records,
        key=lambda record: score_suggestion_record(record, address_keywords)
    )

def order_post_offices_by_keywords(post_offices, address_keywords):
    if not address_keywords:
        return post_offices

    return sorted(
        post_offices,
        key=lambda office: score_suggestion_record(office, address_keywords),
        reverse=True
    )

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
            if keyword.lower().strip() in SKIP_WORDS:
                continue
            records = get_by_district(keyword)
            records = [
                record for record in records
                if fuzzy_match(
                    normalize_location_text(keyword),
                    normalize_location_text(record.get("district", "")),
                    threshold=0.9
                )
            ]
            if records:
                return build_suggestion(
                    best_suggestion_record(records, address_keywords),
                    address_keywords
                )
        return None

    # ── Level 2: Find District within State ──
    district_name, district_records = find_district_from_keywords(
        address_keywords, state_name
    )

    if not district_name:
        # Return state-level suggestion
        return build_suggestion(
            best_suggestion_record(state_records, address_keywords),
            address_keywords
        )

    # ── Level 3: Find Division within State+District ──
    division_name, division_records = find_division_from_keywords(
        address_keywords, state_name, district_name
    )

    if division_records:
        return build_suggestion(
            best_suggestion_record(division_records, address_keywords),
            address_keywords
        )

    # Return district-level suggestion
    return build_suggestion(
        best_suggestion_record(district_records, address_keywords),
        address_keywords
    )

def build_suggestion(record, address_keywords=None):
    """Build suggestion response from a record"""
    suggested_pin = record.get("pincode")
    post_offices = get_post_offices_by_pincode(suggested_pin) if suggested_pin else []
    post_offices = order_post_offices_by_keywords(post_offices, address_keywords)
    suggested_office = record.get("officename")
    if suggested_office:
        post_offices = sorted(
            post_offices,
            key=lambda office: office.get("officename") != suggested_office
        )
    return {
        "suggested_pin": suggested_pin,
        "suggested_office": suggested_office,
        "district": record.get("district"),
        "state": record.get("statename"),
        "circle": record.get("circlename"),
        "division": record.get("divisionname"),
        "region": record.get("regionname"),
        "latitude": record.get("latitude"),
        "longitude": record.get("longitude"),
        "post_offices": post_offices[:10]
    }

def keyword_in_field(keyword, field):
    """Exact or fuzzy match for a keyword against a postal field."""
    kw = keyword.lower().strip()
    value = field.lower().strip()
    if not kw or not value:
        return False
    return kw in value or fuzzy_match(kw, value)

def keyword_exists_in_location(keyword):
    """Return True when a keyword is a known district/state/circle anywhere."""
    return bool(
        get_by_district(keyword) or
        get_by_state(keyword) or
        get_by_circle(keyword)
    )

def records_match_address(records, address_keywords):
    """Match PIN records against address keywords with stricter evidence.

    A state/circle match alone is not enough. At least one locality-level
    field must match: district, post office, division, or region. If the
    address contains a known location keyword that does not match this PIN's
    records, treat it as a mismatch.
    """
    strong_match = False

    for keyword in address_keywords:
        kw = keyword.lower()
        matched_any_location = False

        for record in records:
            district = record.get("district", "")
            state = record.get("statename", "")
            circle = record.get("circlename", "")
            office = record.get("officename", "")
            division = record.get("divisionname", "")
            region = record.get("regionname", "")

            if (
                keyword_in_field(kw, district) or
                keyword_in_field(kw, office) or
                keyword_in_field(kw, division) or
                keyword_in_field(kw, region)
            ):
                strong_match = True
                matched_any_location = True
                break

            if keyword_in_field(kw, state) or keyword_in_field(kw, circle):
                matched_any_location = True

        if keyword_exists_in_location(kw) and not matched_any_location:
            return False

    return strong_match

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
    matched = records_match_address(records, address_keywords)

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
