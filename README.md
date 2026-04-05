# Indian Postal PIN Validator

![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat-square&logo=flask)
![React](https://img.shields.io/badge/React-18.x-61DAFB?style=flat-square&logo=react)
![MongoDB](https://img.shields.io/badge/MongoDB-7.x-47A248?style=flat-square&logo=mongodb)
![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?style=flat-square&logo=google)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

> A web application that validates Indian Postal PIN codes against addresses by reading envelope images using AI-powered OCR and Machine Learning.

---

## Problem Statement

Indian PIN codes are unique to each location. People often write incorrect or mismatched PIN codes on envelopes, causing delivery failures. This system solves that by:

- Scanning envelope images using **Gemini 2.5 Flash Vision AI** (with EasyOCR as fallback)
- Extracting the PIN code, recipient name, address, city, district, and state
- Validating against **157,000+ official India Post records** in MongoDB
- Suggesting the **correct PIN** using hierarchical search if a mismatch is found
- Cross-validating with a **Random Forest ML model** for PIN prefix accuracy

---

## Features

- **Image Upload** - Drag & drop or click to upload printed/handwritten envelope images
- **AI-Powered OCR** - Gemini 2.5 Flash reads handwritten text, handles rotated images, colored envelopes
- **EasyOCR Fallback** - Works offline with EasyOCR + OpenCV preprocessing (CLAHE, adaptive threshold)
- **PIN Validation** - Validates PIN against 157,000+ Indian postal records in MongoDB
- **ML Validation** - Random Forest model validates PIN prefix matches the region
- **Smart Suggestion** - Hierarchical suggestion algorithm (State > District > Division)
- **Post Office Info** - Lists post offices for the PIN with delivery status
- **Location Details** - District, State, Circle, Region, Division, Coordinates

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Axios, React Icons, React Toastify |
| Backend | Python 3.13+, Flask, Flask-CORS |
| Database | MongoDB 7.0+ |
| OCR (Primary) | Google Gemini 2.5 Flash Vision API |
| OCR (Fallback) | EasyOCR 1.7 + OpenCV |
| Machine Learning | Random Forest Classifier (scikit-learn) |
| Dataset | India Post Official PIN Directory (157,000+ records) |

---

## Project Structure

```
postal-pin-validator/
|
|-- backend/                         <- Flask API
|   |-- app/
|   |   |-- routes/
|   |   |   +-- pin_routes.py        <- API endpoints (Gemini + Tesseract routing)
|   |   |-- services/
|   |   |   |-- gemini_ocr_service.py <- Gemini 2.5 Flash Vision integration
|   |   |   |-- ocr_service.py       <- EasyOCR with preprocessing pipeline
|   |   |   |-- pin_service.py       <- PIN extraction + validation logic
|   |   |   +-- ml_service.py        <- Random Forest ML validation
|   |   +-- models/
|   |       +-- postal_model.py      <- MongoDB queries
|   |-- config.py                    <- App configuration
|   |-- run.py                       <- Entry point
|   +-- requirements.txt
|
|-- frontend/                        <- React UI
|   +-- src/
|       |-- components/
|       |   |-- Header.js
|       |   |-- UploadSection.js     <- Image upload with drag & drop
|       |   +-- ResultSection.js     <- Validation results display
|       +-- App.js
|
|-- ml_model/                        <- ML Training
|   |-- train_model.py
|   |-- test_model.py
|   +-- saved_models/                <- Trained model + encoders (.pkl)
|
|-- scripts/
|   +-- import_data.py               <- Dataset download + MongoDB import
|
+-- dataset/                         <- India Post CSV (auto-downloaded)
```

---

## How It Works

```
Upload Envelope Image
         |
         v
Gemini 2.5 Flash Vision AI  (or EasyOCR fallback)
   - Reads handwritten/printed text
   - Extracts recipient, sender, PIN, address
   - Returns structured JSON
         |
         v
PIN Extraction
   - Prioritizes "To" address over "From"
   - Handles OCR digit errors
   - Skips phone numbers
         |
         v
MongoDB Lookup
   - Checks PIN against 157,000+ records
   - Fetches district, state, circle, region
         |
         v
Random Forest ML Validation
   - Predicts expected PIN prefix for the region
   - Cross-validates with extracted PIN
         |
         v
Result
   Valid   -> Show location details + post offices
   Invalid -> Suggest correct PIN (State > District > Division)
```

---

## Getting Started

### Prerequisites

- **Python 3.13+**
- **Node.js 18+**
- **MongoDB 7.0+** (Community Edition, running on localhost:27017)
- **Git**
- **Gemini API Key** (free) - get it from https://aistudio.google.com/apikey
- No extra system installs needed — EasyOCR is included in pip dependencies

### Step 1: Clone the repository

```bash
git clone https://github.com/Amutha04/postal-pin-validator.git
cd postal-pin-validator
```

### Step 2: Backend setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### Step 3: Create `.env` file

Create a file named `.env` inside the `backend/` folder:

```env
MONGO_URI=mongodb://localhost:27017/
DB_NAME=postal_db
GEMINI_API_KEY=your-gemini-api-key-here
USE_GEMINI=true
SECRET_KEY=your-secret-key
```

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes (if USE_GEMINI=true) | Free API key from Google AI Studio |
| `USE_GEMINI` | No | Set `true` for Gemini Vision, `false` for Tesseract. Default: `false` |
| `MONGO_URI` | No | MongoDB connection string. Default: `mongodb://localhost:27017/` |
| `DB_NAME` | No | Database name. Default: `postal_db` |

### Step 4: Import dataset into MongoDB

The script auto-downloads the dataset (157,000+ records) if not present:

```bash
cd ..
python scripts/import_data.py
```

This will:
- Download the India Post PIN directory CSV (if not in `dataset/`)
- Import all records into MongoDB `postal_db.pincodes`
- Create indexes for fast lookups

### Step 5: Start the backend

```bash
cd backend
python run.py
```

Flask API runs at **http://127.0.0.1:5000**

### Step 6: Frontend setup (new terminal)

```bash
cd frontend
npm install
npm start
```

React app runs at **http://localhost:3000**

### Step 7: Test it

1. Open http://localhost:3000 in your browser
2. Upload an envelope image (printed or handwritten)
3. Click "Validate PIN"
4. See the extracted text, PIN validation result, and suggestions

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Check API status and OCR engine |
| POST | `/api/validate` | Validate envelope image |

### POST `/api/validate`

**Request:** `multipart/form-data` with `image` field

**Response (Valid PIN):**
```json
{
  "valid": true,
  "message": "PIN code matches the address",
  "pincode": "175126",
  "district": "KULLU",
  "state": "HIMACHAL PRADESH",
  "circle": "Himachal Pradesh Circle",
  "post_offices": [...],
  "ml_validation": { "ml_valid": true, "predicted_prefix": "175" },
  "extracted_text": "Mrs. Jeevan Jyoti, SHAMSHI, Distt. Kullu (H.P), PIN 175126",
  "ocr_engine": "Gemini 2.5 Flash",
  "gemini_data": {
    "recipient": { "name": "Mrs. Jeevan Jyoti", "state": "Himachal Pradesh", "pincode": "175126" },
    "sender": { "name": "JAGANNATH MANI", "city": "Bangalore" }
  }
}
```

**Response (Invalid PIN):**
```json
{
  "valid": false,
  "message": "PIN code does not match address",
  "pincode": "682001",
  "suggestion": {
    "suggested_pin": "380001",
    "district": "AHMEDABAD",
    "state": "GUJARAT"
  }
}
```

---

## ML Model Details

| Parameter | Value |
|---|---|
| Algorithm | Random Forest Classifier |
| Features | District, State, Circle (label encoded) |
| Target | PIN prefix (first 3 digits) |
| Library | scikit-learn |

The ML model acts as a secondary validation layer. After MongoDB confirms the PIN exists, the model checks whether the PIN prefix is consistent with the district/state/circle combination.

---

## OCR Comparison

| Feature | Gemini 2.5 Flash | EasyOCR (fallback) |
|---|---|---|
| Handwritten text | Excellent | Good |
| Colored envelopes | Handles well | Needs preprocessing |
| Rotated images | Auto-handles | Auto-rotation built in |
| Hindi/regional text | Supported | Supported (80+ languages) |
| Speed | ~2-3 seconds | ~5-10 seconds |
| Offline support | No (needs internet) | Yes |
| Cost | Free tier available | Free |
| System install | None (API) | None (pip install) |

---

## Acknowledgements

- [India Post](https://www.indiapost.gov.in/) for the official PIN directory dataset
- [Google Gemini](https://ai.google.dev/) for Vision AI
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) for offline text extraction
- [scikit-learn](https://scikit-learn.org/) for the Random Forest implementation

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
