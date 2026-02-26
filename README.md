# 🐢 SERC Wildlife Intake

A web application for volunteers at **[Southeastern Reptile Conservation (SERC)](https://www.southeastreptile.org)** — a licensed wildlife rehabilitation organization in Virginia focused on native reptiles and amphibians.

Volunteers photograph a paper intake sheet, upload the photo through the app, and the back-end extracts patient and rescuer information using Google Cloud Vision OCR — then appends the record to a Google Sheet in WRMD export format for staff review.

---

## How It Works

```
📷 Volunteer photographs intake sheet
        ↓
🌐 Uploads photo via the web app
        ↓
🔍 Google Cloud Vision extracts text from the form
        ↓
✏️  Volunteer reviews and corrects extracted data
        ↓
💾 Record is appended to Google Sheets (WRMD format)
        ↓
👩‍⚕️ Staff enters the record into wrmd.org
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Front-end | React 19, Material UI v7 |
| Back-end | Python, FastAPI |
| OCR | Google Cloud Vision API |
| Data storage | Google Sheets API |
| Auth | Google Service Account |

---

## Project Structure

```
turtle-intake/
├── frontend/                  # React + Material UI app
│   ├── public/
│   └── src/
│       ├── assets/
│       │   └── logo.png       # SERC circular turtle logo
│       ├── components/
│       │   ├── UploadForm/    # Photo capture / file upload
│       │   ├── ReviewForm/    # Review & edit extracted fields
│       │   └── ConfirmDialog/ # Final confirmation before saving
│       ├── services/
│       │   └── api.js         # Axios wrapper for back-end calls
│       ├── App.jsx
│       ├── theme.js           # MUI light theme (SERC earth tones)
│       └── index.js
└── backend/                   # Python FastAPI app (in progress)
    ├── main.py
    ├── routers/
    │   └── intake.py          # POST /api/intake
    ├── services/
    │   ├── ocr.py             # Google Cloud Vision extraction
    │   └── sheets.py          # Google Sheets append logic
    ├── models/
    │   └── intake.py          # Pydantic IntakeRecord model
    └── requirements.txt
```

---

## Getting Started

### Prerequisites

- [Node.js 22+](https://nodejs.org/) (LTS)
- Python 3.11+
- A Google Cloud project with **Cloud Vision API** and **Google Sheets API** enabled
- A Google Service Account with access to both APIs and the target spreadsheet

---

### Front-End

```bash
cd frontend
npm install
```

Create a `.env` file (use `.env.example` as a template):

```env
REACT_APP_API_BASE_URL=http://localhost:8000
```

Start the dev server:

```bash
npm start
# App runs at http://localhost:3000
```

---

### Back-End

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (use `.env.example` as a template):

```env
GOOGLE_SERVICE_ACCOUNT_JSON=path/to/service-account.json
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_SHEET_TAB=daily-exams.csv
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
FRONTEND_ORIGIN=http://localhost:3000
```

Start the API server:

```bash
uvicorn main:app --reload --port 8000
```

---

## Environment Variables

### Front-End (`frontend/.env`)

| Variable | Description |
|---|---|
| `REACT_APP_API_BASE_URL` | Base URL for the FastAPI back-end |

### Back-End (`backend/.env`)

| Variable | Description |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Path to GCP service account JSON key file |
| `GOOGLE_SHEET_ID` | ID of the target Google Sheet |
| `GOOGLE_SHEET_TAB` | Sheet tab name (default: `daily-exams.csv`) |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `FRONTEND_ORIGIN` | Allowed CORS origin for the front-end |

> ⚠️ Never commit `.env` files or service account JSON keys to version control.

---

## API

### `POST /api/intake`

Accepts a multipart image upload of the paper intake form. Returns extracted fields for volunteer review, and appends the confirmed record to Google Sheets.

**Request:** `multipart/form-data` with an `image` file field
**Response:** JSON matching the `IntakeRecord` schema

#### IntakeRecord fields

| Field | Required | Description |
|---|---|---|
| `common_name` | ✅ | Species common name (e.g. "Eastern Box Turtle") |
| `admitted_at` | ✅ | Intake date (`YYYY-MM-DD`) |
| `rescuer_first_name` | | Rescuer first name |
| `rescuer_last_name` | | Rescuer last name |
| `rescuer_phone` | | Rescuer contact number |
| `rescuer_address` | | Rescuer street address |
| `rescuer_city` | | Rescuer city |
| `rescuer_postal_code` | | Rescuer ZIP code |
| `found_at` | | Date animal was found (`YYYY-MM-DD`) |
| `address_found` | | Street address where animal was found |
| `city_found` | | City where animal was found |
| `reasons_for_admission` | | `Injured`, `Orphaned`, `Displaced`, `Sick`, or `Other` |
| `notes_about_rescue` | | Free-text rescue details |
| `care_by_rescuer` | | Care provided before intake |

---

## Google Sheets Format

Records are appended to the configured sheet in **WRMD export format** — 73 standard columns plus one custom SERC column (`wrmd_processed`). Only intake-relevant columns are populated; the rest are left blank for clinical staff to complete later.

The `wrmd_processed` column (col 74) is set to `0` on every new append. Staff update it to `1` in the sheet after entering the record into [wrmd.org](https://wrmd.org).

---

## Deployment (Google Cloud)

| Component | Recommended Service |
|---|---|
| Front-end | Firebase Hosting or Cloud Run |
| Back-end (FastAPI) | Cloud Run |
| Service Account key | Secret Manager |

---

## About SERC

[Southeastern Reptile Conservation](https://www.southeastreptile.org) is a licensed wildlife rehabilitation organization based in Virginia, focused on the rehabilitation, conservation, and education of native reptile and amphibian species — primarily turtles, snakes, and salamanders.

SERC also supports the development of conservation technology and software tools that help streamline wildlife care, reduce administrative burden for volunteers, and improve data quality for research and reporting. This application is part of that effort.

> *Protecting native species.*

- 🌐 [southeastreptile.org](https://www.southeastreptile.org)
- 📸 [@purringturtle](https://www.instagram.com/purringturtle) on Instagram
