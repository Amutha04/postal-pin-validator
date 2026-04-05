import base64
import json
import re
from google import genai
from config import Config

client = genai.Client(api_key=Config.GEMINI_API_KEY)

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


def extract_with_gemini(image_bytes):
    """Extract text and structured data from envelope using Gemini Vision"""
    try:
        b64_image = base64.standard_b64encode(image_bytes).decode("utf-8")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
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
            ],
        )

        raw_text = response.text.strip()
        print(f"[OK] Gemini raw response:\n{raw_text}")

        # Strip markdown code blocks if present
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)

        parsed = json.loads(raw_text)

        # Build the full_text that the existing pipeline expects
        recipient = parsed.get("recipient", {})
        sender = parsed.get("sender", {})
        full_text = parsed.get("full_text", "")

        # If full_text is empty, build it from structured fields
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

        print(f"[OK] Gemini extracted PIN: {recipient.get('pincode')}")
        print(f"[OK] Gemini full text:\n{full_text}")

        return {
            "text": full_text,
            "structured": parsed,
            "pincode": recipient.get("pincode", ""),
        }

    except json.JSONDecodeError as e:
        print(f"[ERROR] Gemini JSON parse failed: {e}")
        print(f"[ERROR] Raw response was: {raw_text}")
        # Fall back to using raw text
        return {
            "text": raw_text,
            "structured": None,
            "pincode": None,
        }
    except Exception as e:
        print(f"[ERROR] Gemini API failed: {e}")
        return {"error": str(e)}
