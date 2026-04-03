# 📮 Indian Postal PIN Validator

![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat-square&logo=flask)
![React](https://img.shields.io/badge/React-18.x-61DAFB?style=flat-square&logo=react)
![MongoDB](https://img.shields.io/badge/MongoDB-7.x-47A248?style=flat-square&logo=mongodb)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

> An OCR-powered web application that validates Indian Postal PIN codes against addresses using Machine Learning, helping postal workers and users ensure correct delivery.

---

## 📌 Problem Statement

Indian PIN codes are unique to each location. People often write incorrect or mismatched PIN codes on envelopes, causing delivery failures. This system solves that problem by:

- Scanning envelope images using **OCR (Tesseract)**
- Extracting the PIN code and address automatically
- Validating them against the **official India Post dataset**
- Suggesting the **correct PIN** if a mismatch is detected

---

## ✨ Features

- 📷 **Image Upload** — Upload printed or handwritten envelope images
- 🔍 **OCR Extraction** — Automatically extract PIN and address using Tesseract
- ✅ **PIN Validation** — Validate PIN against 165,000+ Indian postal records
- 🤖 **ML Validation** — Random Forest model validates PIN prefix accuracy
- 💡 **Smart Suggestion** — Hierarchical suggestion (State → District → Division)
- 📮 **Post Office Info** — Shows all post offices with delivery status
- 📍 **Location Details** — District, State, Circle, Region, Coordinates
- ✋ **Manual Override** — Enter PIN/address manually if OCR fails

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React.js, Axios, React Icons, React Toastify |
| Backend | Python, Flask, Flask-CORS |
| Database | MongoDB |
| OCR | Tesseract OCR + OpenCV |
| Machine Learning | Random Forest (scikit-learn) |
| Dataset | India Post Official PIN Directory (165,000+ records) |

---

## 🏗️ Project Structure

```
postal-pin-validator/
│
├── backend/                    ← Flask API
│   ├── app/
│   │   ├── routes/
│   │   │   └── pin_routes.py   ← API endpoints
│   │   ├── services/
│   │   │   ├── ocr_service.py  ← Tesseract OCR logic
│   │   │   ├── pin_service.py  ← PIN validation logic
│   │   │   └── ml_service.py   ← Random Forest logic
│   │   └── models/
│   │       └── postal_model.py ← MongoDB queries
│   ├── config.py
│   ├── run.py
│   └── requirements.txt
│
├── frontend/                   ← React.js UI
│   └── src/
│       ├── components/
│       │   ├── Header.js
│       │   ├── UploadSection.js
│       │   └── ResultSection.js
│       └── App.js
│
├── ml_model/                   ← ML Training
│   ├── train_model.py
│   ├── test_model.py
│   └── saved_models/
│
├── dataset/                    ← India Post CSV
│   └── india_postal.csv
│
└── docs/                       ← Documentation
```

---

## ⚙️ How It Works

```
📷 Upload Envelope Image
         ↓
🔍 Tesseract OCR + OpenCV
   (Extract text from image)
         ↓
🧠 PIN Extraction
   (Smart extraction ignoring phone numbers)
         ↓
🗄️ MongoDB Lookup
   (Check PIN against 165,000+ records)
         ↓
🤖 Random Forest ML Validation
   (Validate PIN prefix for the region)
         ↓
📊 Result
   ✅ Valid   → Show location + post offices
   ❌ Invalid → Suggest correct PIN
              (State → District → Division)
```

---

## 💡 PIN Suggestion Algorithm

When a PIN mismatch is detected, the system uses a **hierarchical search**:

```
Step 1: Match STATE from address keywords
Step 2: Match DISTRICT within that state
Step 3: Match DIVISION within that district
Step 4: Return most specific PIN found
```

This ensures suggestions are always geographically accurate.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+
- MongoDB 7.0+
- Tesseract OCR 5.x
- Git

### Installation

#### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/postal-pin-validator.git
cd postal-pin-validator
```

#### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

#### 3. Environment Variables
Create `.env` file in `backend/`:
```
MONGO_URI=mongodb://localhost:27017/
DB_NAME=postal_db
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
SECRET_KEY=your-secret-key
```

#### 4. Import Dataset
```bash
mongoimport --db postal_db --collection pincodes --type csv --headerline --file "dataset/india_postal.csv"
```

#### 5. Train ML Model
```bash
cd ml_model
python train_model.py
```

#### 6. Start Backend
```bash
cd backend
python run.py
```
Flask runs at `http://127.0.0.1:5000`

#### 7. Frontend Setup
```bash
cd frontend
npm install
npm start
```
React runs at `http://localhost:3000`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Check API status |
| POST | `/api/validate` | Validate envelope image |

### POST `/api/validate`
**Request:** `multipart/form-data`
| Field | Type | Required |
|---|---|---|
| image | File | Yes |
| manual_pin | String | No |
| manual_address | String | No |

**Response (Valid PIN):**
```json
{
  "valid": true,
  "message": "PIN code matches the address ✅",
  "pincode": "395007",
  "district": "SURAT",
  "state": "GUJARAT",
  "circle": "Gujarat Circle",
  "post_offices": [...],
  "ml_validation": {...}
}
```

**Response (Invalid PIN):**
```json
{
  "valid": false,
  "message": "PIN code does not match address ❌",
  "pincode": "395999",
  "suggestion": {
    "suggested_pin": "395007",
    "district": "SURAT",
    "state": "GUJARAT"
  }
}
```

---

## 🤖 ML Model Details

| Parameter | Value |
|---|---|
| Algorithm | Random Forest Classifier |
| Training Records | ~50,000 unique postal combinations |
| Features | District, State, Circle (encoded) |
| Target | PIN prefix (first 3 digits) |
| Accuracy | ~85%+ |
| Library | scikit-learn |

---

## 📸 Screenshots

> Add screenshots of your application here after deployment

---

## 🙏 Acknowledgements

- [India Post](https://www.indiapost.gov.in/) for the official PIN directory dataset
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text extraction
- [scikit-learn](https://scikit-learn.org/) for the Random Forest implementation

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

Made with ❤️ for improving India's postal delivery system.

