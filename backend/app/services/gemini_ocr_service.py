import base64
import json
import re
import time
from google import genai
from config import Config

# ── Key rotation setup ──
_api_keys = Config.GEMINI_API_KEYS


# Primary model, fallback model
PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.0-flash"


EXTRACTION_PROMPT = """You are an expert at reading postal envelopes. Analyze this envelope image and extract:

1. **Recipient (To)**: name, full address, city, district, state, PIN code
2. **Sender (From)**: name, full address, city, PIN code (if visible)
3. **Full text**: Everything written on the envelope

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
- The full_text should contain ALL readable text from the envelope"""


def _parse_response(raw_text):
    """Parse Gemini raw response into structured result"""
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


def _try_generate(client, model, contents):
    """Single generate_content call, returns raw_text or raises"""
    response = client.models.generate_content(
        model=model,
        contents=contents,
    )
    return response.text.strip()


def extract_with_gemini(image_bytes):
    """Extract text using Gemini Vision with key rotation + model fallback.
    Exhausted keys reset every request — all keys tried fresh each time.
    Returns {"error": "..."} if all keys fail — caller falls back to EasyOCR.
    """
    if not _api_keys:
        print("[ERROR] No Gemini API keys configured")
        return {"error": "No Gemini API keys configured"}

    # ── LOCAL — resets every request, so all keys are tried fresh ──
    exhausted_keys = set()

    b64_image = base64.standard_b64encode(image_bytes).decode("utf-8")

    contents = [
        {
            "role": "user",
            "parts": [
                {"text": EXTRACTION_PROMPT},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": b64_image,
                    }
                },
            ],
        }
    ]

    while True:
        # ── Pick next available key ──
        available = [i for i in range(len(_api_keys)) if i not in exhausted_keys]
        if not available:
            print("[ERROR] All Gemini API keys exhausted — handing off to EasyOCR")
            return {"error": "All Gemini API keys exhausted"}

        key_index = available[0]
        client = genai.Client(api_key=_api_keys[key_index])
        key_num = key_index + 1
        print(f"[INFO] Gemini: trying key #{key_num} of {len(_api_keys)}...")

        try:
            # ── Try primary model ──
            raw_text = _try_generate(client, PRIMARY_MODEL, contents)
            print(f"[OK] Key #{key_num} succeeded with {PRIMARY_MODEL}")

        except Exception as e:
            error_str = str(e)

            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"[WARN] Key #{key_num} quota exhausted — switching key...")
                exhausted_keys.add(key_index)
                continue

            elif "403" in error_str or "PERMISSION_DENIED" in error_str:
                print(f"[ERROR] Key #{key_num} — API not enabled for this project.")
                print(f"[ERROR] Fix: Go to console.cloud.google.com → Enable 'Generative Language API'")
                exhausted_keys.add(key_index)
                continue

            elif "503" in error_str or "unavailable" in error_str.lower():
                # Primary model overloaded — try fallback model on same key
                print(f"[WARN] Key #{key_num} got 503 on {PRIMARY_MODEL}, trying {FALLBACK_MODEL}...")
                try:
                    raw_text = _try_generate(client, FALLBACK_MODEL, contents)
                    print(f"[OK] Key #{key_num} succeeded with {FALLBACK_MODEL}")
                except Exception as fallback_err:
                    fallback_str = str(fallback_err)
                    if "429" in fallback_str or "RESOURCE_EXHAUSTED" in fallback_str:
                        print(f"[WARN] Key #{key_num} quota exhausted on fallback — switching key...")
                    else:
                        print(f"[WARN] Key #{key_num} failed on both models — switching key...")
                    exhausted_keys.add(key_index)
                    continue

            else:
                print(f"[ERROR] Key #{key_num} unexpected error: {error_str} — switching key...")
                exhausted_keys.add(key_index)
                continue

        # ── Parse the response ──
        try:
            return _parse_response(raw_text)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Gemini JSON parse failed: {e}")
            return {"text": raw_text, "structured": None, "pincode": None}