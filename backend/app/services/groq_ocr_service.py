import base64
import json
import re
import time
from groq import Groq
from config import Config

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Per-key transient retries before declaring the key exhausted and rotating
TRANSIENT_RETRIES_PER_KEY = 2

EXTRACTION_PROMPT = """You are an expert at reading postal envelopes and postcards. Analyze this image and extract:

1. **Recipient (To)**: name, full address, city, district, state, PIN code
2. **Sender (From)**: name, full address, city, PIN code (if visible)
3. **Full text**: Everything written on the envelope/postcard

Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{
    "recipient": {
        "name": "",
        "address": "",
        "city": "",
        "district": "",
        "state": "",
        "pincode": ""
    },
    "sender": {
        "name": "",
        "address": "",
        "city": "",
        "pincode": ""
    },
    "full_text": ""
}

Rules:
- PIN code must be exactly 6 digits if found
- If a field is not readable, use empty string ""
- Read handwritten text carefully, especially digits
- Include the state name even if abbreviated (e.g., "H.P" means "Himachal Pradesh")
- The full_text should contain ALL readable text from the image"""


def _parse_response(raw_text):
    """Parse Groq raw response into structured result"""
    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)

    parsed = json.loads(raw_text)
    recipient = parsed.get("recipient", {})
    sender = parsed.get("sender", {})
    full_text = parsed.get("full_text", "")

    if not full_text:
        parts = []
        if sender.get("name"):
            parts.append(f"From: {sender['name']}")
            if sender.get("address"):
                parts.append(sender["address"])
        parts.append("To,")
        if recipient.get("name"):
            parts.append(recipient["name"])
        if recipient.get("address"):
            parts.append(recipient["address"])
        city_state = ", ".join(
            filter(None, [recipient.get("city"), recipient.get("state")])
        )
        if city_state:
            parts.append(city_state)
        if recipient.get("pincode"):
            parts.append(f"PIN: {recipient['pincode']}")
        full_text = "\n".join(parts)

    return {
        "text": full_text,
        "structured": parsed,
        "pincode": recipient.get("pincode", ""),
    }


def _try_call(client, messages):
    """Single Groq vision call. Returns parsed dict or raises."""
    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=2048,
    )
    raw_text = response.choices[0].message.content.strip()
    try:
        return _parse_response(raw_text)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Groq JSON parse failed: {e}")
        return {"text": raw_text, "structured": None, "pincode": None}


def extract_with_groq(image_bytes):
    """Extract text using Groq Llama 4 Scout vision with key rotation.
    Cycles through Config.GROQ_API_KEYS on rate-limit / auth / persistent errors.
    Returns {"error": "..."} if all keys fail so caller can fall back to EasyOCR.
    """
    keys = Config.GROQ_API_KEYS
    if not keys:
        print("[ERROR] No Groq API keys configured")
        return {"error": "No Groq API keys configured"}

    b64_image = base64.standard_b64encode(image_bytes).decode("utf-8")
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": EXTRACTION_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
        ],
    }]

    exhausted = set()
    last_error = None

    while True:
        available = [i for i in range(len(keys)) if i not in exhausted]
        if not available:
            print(f"[ERROR] All {len(keys)} Groq keys exhausted — falling back to EasyOCR")
            return {"error": f"All Groq keys exhausted: {str(last_error)[:200]}"}

        idx = available[0]
        key_num = idx + 1
        client = Groq(api_key=keys[idx])
        print(f"[INFO] Groq: trying key #{key_num} of {len(keys)} on {VISION_MODEL}...")

        # Per-key retry loop for transient 503/timeout
        for attempt in range(1, TRANSIENT_RETRIES_PER_KEY + 1):
            try:
                result = _try_call(client, messages)
                print(f"[OK] Key #{key_num} succeeded (attempt {attempt})")
                return result

            except Exception as e:
                last_error = e
                error_str = str(e)

                if "401" in error_str or "invalid_api_key" in error_str.lower() or "authentication" in error_str.lower():
                    print(f"[ERROR] Key #{key_num} invalid/unauthorized — rotating")
                    exhausted.add(idx)
                    break

                if "429" in error_str or "rate_limit" in error_str.lower() or "quota" in error_str.lower():
                    print(f"[WARN] Key #{key_num} rate-limited — rotating")
                    exhausted.add(idx)
                    break

                if "403" in error_str or "permission" in error_str.lower():
                    print(f"[ERROR] Key #{key_num} permission denied — rotating")
                    exhausted.add(idx)
                    break

                if "503" in error_str or "unavailable" in error_str.lower() or "timeout" in error_str.lower():
                    print(f"[WARN] Key #{key_num} transient (attempt {attempt}/{TRANSIENT_RETRIES_PER_KEY}): {error_str[:120]}")
                    if attempt < TRANSIENT_RETRIES_PER_KEY:
                        time.sleep(1.5 * attempt)
                        continue
                    print(f"[WARN] Key #{key_num} still transient after retries — rotating")
                    exhausted.add(idx)
                    break

                # Unknown error — rotate to be safe
                print(f"[ERROR] Key #{key_num} unexpected error: {error_str[:200]} — rotating")
                exhausted.add(idx)
                break
