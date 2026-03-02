# CLAUDE.md — SERC Wildlife Intake

## Project Overview

A web application for volunteers at **Southeastern Reptile Conservation (SERC)**, a licensed wildlife rehabilitation organization based in Virginia focused on native reptiles and amphibians — primarily turtles, snakes, and salamanders. Volunteers photograph a paper intake sheet with patient and rescuer information, upload the photo through the UI, and the back-end extracts the data and appends it to a Google Sheet in WRMD export format.

- **Organization:** Southeastern Reptile Conservation (SERC)
- **Website:** [southeastreptile.org](https://www.southeastreptile.org)
- **Mission:** "Protecting native species" through rehabilitation, habitat stewardship, and community education
- **Instagram:** @purringturtle
- **Frontend (live):** https://serc-turtle-intake.web.app
- **Backend (live):** https://serc-intake-api-4d3j3nugya-uk.a.run.app

---

## Architecture

```
turtle-intake/
├── cloudbuild.yaml            # CI/CD pipeline (Cloud Build)
├── firebase.json              # Firebase Hosting config
├── .firebaserc
├── frontend/                  # React + Material UI (JavaScript)
│   ├── .env.production        # REACT_APP_API_BASE_URL (production Cloud Run URL)
│   └── src/
│       ├── assets/logo.png    # SERC circular turtle logo
│       ├── components/
│       │   ├── UploadForm/    # Photo capture / file upload
│       │   ├── ReviewForm/    # Display & edit extracted fields
│       │   └── ConfirmDialog/ # Final confirmation before saving
│       ├── services/api.js    # axios wrapper for back-end calls
│       ├── theme.js           # MUI light theme (SERC earth tones)
│       ├── App.jsx
│       └── index.js
└── backend/                   # Python FastAPI
    ├── Dockerfile
    ├── .dockerignore
    ├── main.py                # FastAPI app entry, CORS, router registration
    ├── routers/
    │   └── intake.py          # POST /api/intake/extract, POST /api/intake/save, GET /api/taxa/search
    ├── services/
    │   ├── ocr.py             # Google Cloud Vision extraction + field parsing
    │   ├── sheets.py          # Google Sheets append logic
    │   └── wrmd.py            # WRMD taxa search (species name validation)
    ├── models/
    │   └── intake.py          # Pydantic models: IntakeRecord, IntakeResponse, TaxaCandidate
    ├── utils/
    │   └── dates.py           # Date parsing: MM/DD/YY → YYYY-MM-DD
    └── requirements.txt
```

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Front-end | React | 19 |
| Front-end UI | Material UI (MUI) | v7 |
| Front-end dates | `@mui/x-date-pickers` + `dayjs` | — |
| Front-end HTTP | axios | — |
| Back-end | Python + FastAPI | FastAPI 0.115.6 |
| Back-end server | uvicorn | 0.32.1 |
| Back-end models | pydantic | 2.10.4 |
| OCR | Google Cloud Vision API | `google-cloud-vision` 3.9.0 |
| Spreadsheet | Google Sheets via gspread | 6.1.4 |
| Auth | Google Service Account | `google-auth` 2.37.0 |
| WRMD taxa | WRMD internal API (Bearer auth) | — |
| Frontend hosting | Firebase Hosting | — |
| Backend hosting | Google Cloud Run | — |
| CI/CD | Google Cloud Build | — |

---

## Branding & Design

### Organization Identity
- **Full name:** Southeastern Reptile Conservation (SERC)
- **Tagline:** "Protecting native species"
- **Tone:** Professional yet approachable; direct and purpose-driven
- **Key language patterns:** Use "native species" / "native wildlife"; action-oriented (*rehabilitate*, *conserve*, *protect*); community-focused and welcoming

### Logo
- **File:** `frontend/src/assets/logo.png`
- Circular badge on black background: illustrated Eastern Box Turtle over leaves, acronym **SERC** in spaced caps
- Display prominently in app header (64–80px); black background — place on dark surfaces

### Color Palette

| Role | Color | Hex |
|---|---|---|
| Primary | Deep olive / dark moss green | `#4A5E35` |
| Primary light | Sage green | `#7A8C5E` |
| Primary dark | Forest shadow | `#2E3B1F` |
| Secondary | Warm carapace gold | `#B8924A` |
| Secondary light | Soft gold | `#D4AF6E` |
| Secondary dark | Earthy brown | `#6B4F2A` |
| Background | Warm parchment | `#F5F0E6` |
| Surface / Paper | Soft cream | `#FDFAF4` |
| Text primary | Warm near-black | `#2C2C1E` |
| Text secondary | Warm muted brown | `#6B6347` |
| Divider / Border | Warm tan | `#DDD5C0` |

### MUI Theme (`frontend/src/theme.js`)
- Light mode (`mode: 'light'`)
- Font: `"Inter", "Lato", "Roboto", sans-serif`
- `shape.borderRadius: 12`; buttons use `borderRadius: 10`
- Warm card shadows: `rgba(60,50,20,…)` — never pure grey or black
- Primary buttons: olive green gradient; success/warning/error colors override defaults to match palette

### UI Layout
- 3-step progress indicator: **Upload → Review → Confirm** (success view shown after save)
- `Container maxWidth="sm"` throughout
- Mobile-first: large tap targets, generous whitespace, clear field labels

---

## API Endpoints

All routes are under the prefix `/api` (registered in `routers/intake.py`, mounted in `main.py`).

### `POST /api/intake/extract`
Upload a photo of the intake form. Returns OCR-extracted fields for volunteer review.

**Request:** `multipart/form-data` — field name `image`, max 15 MB

**Response:**
```json
{
  "extracted": { "...IntakeRecord fields..." },
  "warnings": ["Species / Common Name could not be read — please fill it in."],
  "taxa_candidates": [{ "value": 123, "label": "Eastern Box Turtle" }]
}
```
- `warnings` is `[]` when all required fields were read successfully
- `taxa_candidates` are WRMD common-name matches for `common_name`; empty list if WRMD is unreachable or key is missing
- If an exact case-insensitive WRMD match is found for the OCR'd species name, `common_name` in `extracted` is automatically promoted to the canonical WRMD spelling

### `POST /api/intake/save`
Save the volunteer-reviewed record to Google Sheets. Called after confirmation.

**Request:** `application/json` — an `IntakeRecord` object

**Response:** `{ "success": true, "message": "Intake record saved successfully." }` (HTTP 201)

### `GET /api/taxa/search?q={query}`
Search WRMD common-names. Used by the `ReviewForm` Autocomplete for live species name lookup.

**Response:** `[{ "value": int, "label": str }]` — up to 20 results. Returns `[]` on any error (WRMD outage never blocks intake).

### `GET /health`
Health check. Returns `{ "status": "ok", "service": "SERC Wildlife Intake API" }`.

---

## Data Models (`backend/models/intake.py`)

```python
class TaxaCandidate(BaseModel):
    value: int    # WRMD internal ID
    label: str    # Canonical common name, e.g. "Eastern Box Turtle"

class IntakeRecord(BaseModel):
    common_name: str                    # REQUIRED
    admitted_at: str                    # REQUIRED — YYYY-MM-DD
    rescuer_first_name: str | None = None
    rescuer_last_name: str | None = None
    rescuer_phone: str | None = None
    rescuer_address: str | None = None
    rescuer_city: str | None = None
    rescuer_postal_code: str | None = None
    found_at: str | None = None         # YYYY-MM-DD
    address_found: str | None = None
    city_found: str | None = None
    reasons_for_admission: str | None = None  # Injured|Orphaned|Displaced|Sick|Other
    notes_about_rescue: str | None = None
    care_by_rescuer: str | None = None

class IntakeResponse(BaseModel):
    extracted: IntakeRecord
    warnings: list[str] = []
    taxa_candidates: list[TaxaCandidate] = []
```

---

## OCR Flow (`backend/services/ocr.py`)

Uses Google Cloud Vision **DOCUMENT_TEXT_DETECTION**. Credential resolution:
1. `GOOGLE_SERVICE_ACCOUNT_JSON` starts with `{` → parse as inline JSON (Cloud Run)
2. Otherwise treat as file path (local dev)
3. Fall back to Application Default Credentials

**Parsing strategy** — two helper functions:
- `_find_field(text, *labels)` — tries same-line `"Label: value"` first, then next-line
- `_find_field_after(text, label)` — more aggressive: finds first non-empty, non-label line within 3 lines after the label (used for `Species/Common Name` which is always on the next line)

**Address parsing** — `_parse_address(raw)` splits a raw address string into `(street, city, postal_code)` using ZIP regex and comma/whitespace heuristics.

**Name parsing** — `_parse_name(full_name)` splits "First Last" (handles middle names/initials, strips parenthetical nicknames).

**Reason parsing** — `_parse_reason(text)` detects checkmarks (`✓ √ x X *`) adjacent to reason keywords (`Injured`, `Orphaned`, `Displaced`, `Sick`, `Other`).

**Date parsing** (`backend/utils/dates.py`) — converts `MM/DD/YY` or `MM/DD/YYYY` from the form to `YYYY-MM-DD`. 2-digit year expansion: 00–29 → 2000s, 30–99 → 1900s.

---

## WRMD Taxa Integration (`backend/services/wrmd.py`)

**Endpoint:** `GET https://wrmd.org/internal-api/search/common-names/?search={query}`
**Auth:** `Authorization: Bearer {WRMD_API_KEY}`
**Response:** `[{"value": int, "label": str, "data": []}]` — up to 20 results

Key behaviors:
- `search_taxa(query)` — never raises; returns `[]` on any failure so WRMD outage never blocks intake
- `best_match_label(query, candidates)` — returns exact case-insensitive match label, or `None`
- The `/api/taxa/search` endpoint proxies this to the frontend for live Autocomplete use
- At extraction time: if an exact match is found, `common_name` is auto-promoted to canonical WRMD spelling before being returned to the volunteer

---

## Google Sheets Integration (`backend/services/sheets.py`)

- Sheet tab: `daily-exams.csv`
- **74 columns total**: 1 empty index + 73 WRMD columns + 1 custom `wrmd_processed`
- Appends using `gspread.append_row(..., insert_data_option="OVERWRITE")` — writes to the next empty row; never inserts rows that could shift the header
- **Never overwrites existing rows**

**Defaults applied on every new row:**

| Column | Field | Value |
|---|---|---|
| Col 4 | `admitted_by` | `"Linda Nichols"` (always) |
| Col 7 | `address_found` | `address_found` if set, otherwise falls back to `rescuer_address` |
| Col 19 | `disposition` | `"Pending"` (WRMD required field) |
| Col 74 | `wrmd_processed` | `"0"` (staff set to `"1"` after WRMD entry) |

---

## Frontend Components

### `UploadForm`
- Drag-and-drop zone + "Take Photo" (camera capture) + "Choose File" buttons
- Image validation: hard block >15 MB; soft warning Alert for 8–15 MB
- On submit: calls `extractIntakeData(file)` → receives `{extracted, warnings, taxa_candidates}` → calls `onExtracted(extracted, warnings, taxa_candidates)`

### `ReviewForm`
- Accepts `initialData`, `warnings`, `taxaCandidates`, `onSaveRequest` props
- **Species / Common Name** field: MUI `Autocomplete` (`freeSolo`, `fullWidth`)
  - Pre-populated with `taxaCandidates` from extraction
  - Debounced (350ms) live search via `GET /api/taxa/search` as volunteer types
  - Loading spinner during fetch; WRMD errors silently ignored
- All date fields use MUI `DatePicker` (dayjs); other fields are `TextField`
- Reason for Admission uses MUI `Select` with five controlled options
- Required fields (`common_name`, `admitted_at`) validated before `onSaveRequest`

### `ConfirmDialog`
- MUI `Dialog` showing a summary of all non-empty fields grouped by section
- "Save Record" calls `POST /api/intake/save`; shows error Alert on failure
- "Go Back" returns to ReviewForm without losing data

### `App.jsx`
- Manages top-level state: `step`, `extractedData`, `extractionWarnings`, `taxaCandidates`, `reviewedData`, `confirmOpen`
- Step flow: `upload` → `review` → (ConfirmDialog overlay) → `success`

---

## Environment Variables

### Back-End (`backend/.env`)

| Variable | Description |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Local: path to service account JSON file. Cloud Run: raw JSON contents from Secret Manager. Needs Cloud Vision API User + Sheets Editor. |
| `GOOGLE_SHEET_ID` | `1qQHxC6XYYvXPdGIAd6dgBwpPKtfraOwNkstFao4kIb8` |
| `GOOGLE_SHEET_TAB` | `daily-exams.csv` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `FRONTEND_ORIGIN` | Comma-separated allowed CORS origins |
| `WRMD_API_KEY` | WRMD API token (wrmd.org → account settings → API tokens) |

### Front-End (`frontend/.env`)

| Variable | Description |
|---|---|
| `REACT_APP_API_BASE_URL` | `http://localhost:8000` for local dev |

`frontend/.env.production` has the live Cloud Run URL and is used automatically by `npm run build`.

---

## Deployment

**Backend:** Google Cloud Run (`us-east4`)
**Frontend:** Firebase Hosting (`serc-turtle-intake`)
**CI/CD:** `cloudbuild.yaml` — single pipeline deploys both

### Cloud Build pipeline steps
1. `docker build` — tags image with `$BUILD_ID` and `latest`
2. `docker push --all-tags`
3. `gcloud run deploy` from `:latest` image, with all 4 secrets mounted
4. `npm ci` (frontend deps)
5. `npm run build` with `REACT_APP_API_BASE_URL=$_API_URL` injected at build time
6. `firebase deploy --only=hosting` (uses `FIREBASE_TOKEN` secret)

**`$BUILD_ID` is used instead of `$COMMIT_SHA`** — `$BUILD_ID` is always set for both manual and triggered builds; `$COMMIT_SHA` is empty on `gcloud builds submit`.

### Secrets in Secret Manager (GCP project `turtle-intake`)
- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `GOOGLE_SHEET_ID`
- `FRONTEND_ORIGIN`
- `WRMD_API_KEY`
- `FIREBASE_TOKEN` (used by Cloud Build step 6 only)

### Manual deploy
```bash
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions=\
_REGION=us-east4,\
_SERVICE_NAME=serc-intake-api,\
_API_URL=https://serc-intake-api-4d3j3nugya-uk.a.run.app,\
_FIREBASE_PROJECT=serc-turtle-intake
```

---

## Development Conventions

### General
- Keep front-end and back-end strictly separated under `frontend/` and `backend/`
- `.env` files for all secrets — never hard-code credentials
- `.env` in `.gitignore`; `.env.example` with placeholders provided

### Front-End (JavaScript / React)
- Functional components and React hooks only (no class components)
- MUI `sx` prop or `styled()` for custom styling — no plain inline styles
- Prefer MUI components over raw HTML where an equivalent exists
- State management: `useState`/`useContext` — no external state library

### Back-End (Python)
- FastAPI with type hints on all function signatures
- Pydantic models for all request/response validation
- Modules: `routers/`, `services/`, `models/`, `utils/`
- All Sheets interactions in `services/sheets.py`
- All OCR interactions in `services/ocr.py`
- All WRMD interactions in `services/wrmd.py`
- Follow PEP 8

### Running Locally

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm start   # http://localhost:3000
```

---

## What NOT to Do

- Do not commit `.env` files or service account JSON keys to version control
- Do not store the service account JSON inside `frontend/`
- Do not skip the volunteer review step — always show extracted data before saving
- Do not use class components or `componentDidMount` patterns in React
- Do not use `any` types or skip pydantic validation in Python routes
- Do not use `insert_data_option="INSERT_ROWS"` in `append_row` — it inserts above the header. Use `"OVERWRITE"`
- Do not reference `$COMMIT_SHA` in `cloudbuild.yaml` for manually triggered builds — use `$BUILD_ID`
