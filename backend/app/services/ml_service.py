import pickle
import pandas as pd
import os

# ─────────────────────────────────────────
# Load model and encoders
# ─────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "ml_model", "saved_models")

try:
    with open(f"{MODEL_PATH}/rf_model.pkl", "rb") as f:
        model = pickle.load(f)
    with open(f"{MODEL_PATH}/le_district.pkl", "rb") as f:
        le_district = pickle.load(f)
    with open(f"{MODEL_PATH}/le_state.pkl", "rb") as f:
        le_state = pickle.load(f)
    with open(f"{MODEL_PATH}/le_circle.pkl", "rb") as f:
        le_circle = pickle.load(f)
    print("[OK] ML model loaded successfully!")
except Exception as e:
    print(f"[ERROR] ML model loading failed: {e}")
    model = None

def validate_pin_with_ml(pincode, district, state, circle):
    """
    Validate PIN code using Random Forest model
    Returns validation result with prediction
    """
    if model is None:
        return {
            "ml_valid": None,
            "message": "ML model not available"
        }

    try:
        # Encode inputs
        district_enc = le_district.transform(
            [district.lower().strip()]
        )[0]
        state_enc = le_state.transform(
            [state.lower().strip()]
        )[0]
        circle_enc = le_circle.transform(
            [circle.lower().strip()]
        )[0]

        # Create feature dataframe
        features = pd.DataFrame(
            [[district_enc, state_enc, circle_enc]],
            columns=["district_encoded", "state_encoded", 
                     "circle_encoded"]
        )

        # Predict PIN prefix
        predicted_prefix = str(model.predict(features)[0])
        actual_prefix = str(pincode)[:3]

        if actual_prefix == predicted_prefix:
            return {
                "ml_valid": True,
                "message": f"ML confirms PIN prefix {actual_prefix} matches address ✅",
                "predicted_prefix": predicted_prefix,
                "actual_prefix": actual_prefix
            }
        else:
            return {
                "ml_valid": False,
                "message": f"ML detected PIN mismatch ❌",
                "predicted_prefix": predicted_prefix,
                "actual_prefix": actual_prefix,
                "hint": f"PIN should start with {predicted_prefix}"
            }

    except ValueError:
        # Unknown district/state/circle — skip ML validation
        return {
            "ml_valid": None,
            "message": "Address not recognized by ML model"
        }
    except Exception as e:
        return {
            "ml_valid": None,
            "message": f"ML error: {str(e)}"
        }