import pickle
import pandas as pd

with open("saved_models/rf_model.pkl", "rb") as f:
    model = pickle.load(f)
with open("saved_models/le_district.pkl", "rb") as f:
    le_district = pickle.load(f)
with open("saved_models/le_state.pkl", "rb") as f:
    le_state = pickle.load(f)
with open("saved_models/le_circle.pkl", "rb") as f:
    le_circle = pickle.load(f)

def validate_pin_with_ml(pincode, district, state, circle):
    try:
        district_enc = le_district.transform([district.lower().strip()])[0]
        state_enc = le_state.transform([state.lower().strip()])[0]
        circle_enc = le_circle.transform([circle.lower().strip()])[0]

        features = pd.DataFrame(
            [[district_enc, state_enc, circle_enc]],
            columns=["district_encoded", "state_encoded", "circle_encoded"]
        )
        predicted_prefix = str(model.predict(features)[0])
        actual_prefix = str(pincode)[:3]

        if actual_prefix == predicted_prefix:
            return {
                "valid": True,
                "message": f"PIN prefix {actual_prefix} matches address ✅"
            }
        else:
            return {
                "valid": False,
                "message": f"PIN prefix {actual_prefix} doesn't match ❌",
                "hint": f"PIN should start with {predicted_prefix}"
            }
    except ValueError as e:
        return {"valid": False, "reason": str(e)}

print("🧪 Testing...\n")
tests = [
    ("636001", "salem", "tamil nadu", "tamilnadu circle"),
    ("345001", "salem", "tamil nadu", "tamilnadu circle"),
    ("600001", "chennai", "tamil nadu", "tamilnadu circle"),
    ("110001", "new delhi", "delhi", "delhi circle"),
]

for pin, district, state, circle in tests:
    result = validate_pin_with_ml(pin, district, state, circle)
    print(f"📍 PIN {pin} | {district.title()}, {state.title()}")
    if "message" in result:
        print(f"   → {result['message']}")
    else:
        print(f"   → Unknown: {result['reason']}")
    print()