# CLAUDE.md — SERC Wildlife Intake

## Project Overview

A web application for volunteers at **Southeastern Reptile Conservation (SERC)**, a licensed wildlife rehabilitation organization based in Virginia focused on native reptiles and amphibians — primarily turtles, snakes, and salamanders. Volunteers photograph a paper intake sheet with patient and rescuer information, upload the photo through the UI, and the back-end extracts the data and appends it to a Google Sheet in the WRMD export format.

- **Organization:** Southeastern Reptile Conservation (SERC)
- **Website:** [southeastreptile.org](https://www.southeastreptile.org)
- **Mission:** "Protecting native species" through rehabilitation, habitat stewardship, and community education
- **Instagram:** @purringturtle

---

## Architecture

```
turtle-intake/
├── frontend/      # React + Material UI (JavaScript)
│   └── src/
│       └── assets/
│           └── logo.png   # SERC circular turtle logo
└── backend/       # Python (FastAPI recommended)
```

### Front-End
- **Language:** JavaScript (React.js)
- **Styling:** Material UI (MUI)
- **Key responsibilities:**
  - Camera / file-upload interface for the intake sheet photo
  - Display extracted data for volunteer review/correction before saving
  - Submit confirmed data to the back-end

### Back-End
- **Language:** Python
- **Key responsibilities:**
  - Receive uploaded image
  - Call Google Cloud Vision API to extract structured data from the intake sheet
  - Validate and normalize extracted fields
  - Append a new row to the configured Google Sheet via the Google Sheets API
  - Return structured results (and any errors) to the front-end

---

## Tech Stack

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Front-end    | React.js (JavaScript), Material UI  |
| Back-end     | Python (FastAPI)                    |
| OCR / AI     | Google Cloud Vision API             |
| Spreadsheet  | Google Sheets API                   |
| Auth (Sheets)| Google Service Account credentials  |

---

## Branding & Design

### Organization Identity
- **Full name:** Southeastern Reptile Conservation (SERC)
- **Tagline:** "Protecting native species"
- **Focus:** Licensed wildlife rehabilitators in Virginia; experts in native reptiles and amphibians
- **Tone:** Professional yet approachable — direct and purpose-driven without jargon; credentials paired with warmth and community accessibility
- **Key language patterns to echo in UI copy:**
  - Use "native species" / "native wildlife" when referring to animals
  - Action-oriented: *rehabilitate*, *conserve*, *protect*
  - Community-focused and welcoming — volunteers are partners, not just data-entry workers

### Logo
- **File:** `frontend/src/assets/logo.png`
- **Description:** Circular badge on a black background featuring an illustrated Eastern Box Turtle walking over a bed of green and tan leaves, with the acronym **SERC** lettered below in spaced caps
- Display the logo prominently in the app header/navbar
- The logo has a black background — place it on dark surfaces or use a transparent PNG variant if one becomes available

### Color Palette
Light mode, nature-inspired earth-tone palette drawn from the logo illustration and southeastreptile.org:

| Role              | Color                        | Hex       |
|-------------------|------------------------------|-----------|
| Primary           | Deep olive / dark moss green | `#4A5E35` |
| Primary light     | Sage green                   | `#7A8C5E` |
| Primary dark      | Forest shadow                | `#2E3B1F` |
| Secondary         | Warm carapace gold           | `#B8924A` |
| Secondary light   | Soft gold                    | `#D4AF6E` |
| Secondary dark    | Earthy brown                 | `#6B4F2A` |
| Background        | Warm parchment               | `#F5F0E6` |
| Surface / Paper   | Soft cream                   | `#FDFAF4` |
| Text primary      | Warm near-black              | `#2C2C1E` |
| Text secondary    | Warm muted brown             | `#6B6347` |
| Divider / Border  | Warm tan                     | `#DDD5C0` |

### MUI Theme Guidelines
- Use **light mode** as the base theme (`mode: 'light'`) to match southeastreptile.org's warm, accessible aesthetic
- Set `primary.main` to `#4A5E35` and `secondary.main` to `#B8924A`
- Use `Inter` or `Lato` as the body font (sans-serif, modern, accessible); slightly heavier weight for headings
- Rounded corners throughout: `shape.borderRadius: 12`
- Soft warm card shadows using `rgba(60,50,20,…)` — not pure grey or black
- Logo displayed prominently in a hero-style header (64–80px), not squeezed into a tiny navbar icon
- Step progress indicator between header and main content (Upload → Review → Confirm)

### UI Tone
- Clean, calm, and nature-inspired — this is a practical tool for volunteers, not a flashy consumer app
- Prioritize clarity and ease of use on **mobile** (volunteers may be photographing forms outdoors in the field)
- Generous whitespace, clear field labels, and large tap targets
- Success/confirmation states should feel rewarding — volunteers are doing meaningful conservation work

---

## Development Conventions

### General
- Keep front-end and back-end code strictly separated under `frontend/` and `backend/`.
- Use `.env` files for all secrets and API keys — never hard-code credentials.
- Add `.env` to `.gitignore` immediately; provide `.env.example` with placeholder values.

### Front-End (JavaScript / React)
- Use functional components and React hooks only (no class components).
- Co-locate component files: one folder per component with `index.jsx` + any sub-files.
- Use MUI's `sx` prop or `styled()` for custom styling — avoid plain inline styles.
- Prefer MUI components over raw HTML elements where an equivalent exists.
- State management: React `useState`/`useContext` is sufficient unless complexity grows.

### Back-End (Python)
- Use **FastAPI** as the web framework.
- Follow PEP 8; use type hints on all function signatures.
- Organize into modules: `routers/`, `services/`, `models/`, `utils/`.
- Use `pydantic` models for request/response validation.
- All Google Sheets interactions live in `services/sheets.py`.
- All OCR/AI interactions live in `services/ocr.py`.

### API Design
- Single primary endpoint: `POST /api/intake` — accepts multipart image upload, returns extracted + saved data.
- Return clear error responses with HTTP status codes and a `detail` message.

---

## Google Cloud Vision Integration

- Use the `google-cloud-vision` Python client library.
- Send the uploaded image to the Vision API using **DOCUMENT_TEXT_DETECTION** for best results on structured forms.
- Parse the raw OCR text in `services/ocr.py` to map recognized text to the expected intake fields.
- Authenticate via the same **Google Service Account** used for Sheets (grant it the `Cloud Vision API User` role in GCP).
- The service account JSON key path is shared: `GOOGLE_SERVICE_ACCOUNT_JSON` in `.env`.

### OCR Flow
1. Receive image bytes in `routers/intake.py`
2. Pass to `services/ocr.py` → `extract_intake_fields(image_bytes) -> IntakeRecord`
3. Vision API returns raw text blocks; parse with regex / string matching into pydantic fields
4. Return `IntakeRecord` to the router for review response and eventual Sheets append

### IntakeRecord Pydantic Model (fields extracted from form)
Defined in `backend/models/intake.py`:

```python
class IntakeRecord(BaseModel):
    common_name: str                  # REQUIRED — e.g. "Eastern Box Turtle"
    admitted_at: str                  # REQUIRED — date format YYYY-MM-DD (e.g. "2025-01-15")
    rescuer_first_name: str | None
    rescuer_last_name: str | None
    rescuer_phone: str | None
    rescuer_address: str | None
    rescuer_city: str | None
    rescuer_postal_code: str | None
    found_at: str | None             # date found, YYYY-MM-DD — only if different from admitted_at
    address_found: str | None        # street address where animal was found
    city_found: str | None
    reasons_for_admission: str | None  # one of: Injured, Orphaned, Displaced, Sick, Other
    notes_about_rescue: str | None
    care_by_rescuer: str | None
```

### Date Format
All date fields (`admitted_at`, `found_at`) must be formatted as **`YYYY-MM-DD`** (e.g. `2025-01-15`) for WRMD compatibility — convert from the MM/DD/YY format written on the paper intake form during parsing.

---

## Intake Form Fields

The paper intake sheet (photographed by volunteers) contains the following fields. These map to the WRMD export column schema documented in the Google Sheets section below.

| Intake Form Label                          | WRMD Column(s)                                      |
|--------------------------------------------|-----------------------------------------------------|
| Date                                       | `admitted_at`                                       |
| Species / Common Name                      | `common_name`                                       |
| Full Name (rescuer)                        | `rescuer_first_name`, `rescuer_last_name`           |
| Contact Number                             | `rescuer_phone`                                     |
| Address                                    | `rescuer_address`, `rescuer_city`, `rescuer_postal_code` |
| Location Found (if different)              | `found_at`, `city_found`, `address_found`           |
| Reason for Intake (checkbox)               | `reasons_for_admission`                             |
| Details about rescue / relevant info       | `notes_about_rescue`                                |
| Care given (food, water, meds, treatments) | `care_by_rescuer`                                   |

### Reason for Intake Checkboxes
The form has five options — map the checked value to `reasons_for_admission` as a string:
- `Injured`
- `Orphaned`
- `Displaced`
- `Sick`
- `Other` (include any specified text)

---

## Google Sheets Integration

- Authenticate via a **Google Service Account** (JSON key file).
- Store the key file path in `.env` as `GOOGLE_SERVICE_ACCOUNT_JSON`.
- Store the target spreadsheet ID in `.env` as `GOOGLE_SHEET_ID`.
- The sheet name (tab) is `daily-exams.csv`.
- Each intake record is appended as one new row.
- Column 1 is an empty index column — leave it blank on append.
- The sheet has **74 columns total**: 73 standard WRMD columns + 1 custom SERC column (`wrmd_processed`).
- All 74 columns must be present in every appended row; populate only the intake-relevant ones and leave the rest as empty strings.
- `wrmd_processed` (col 74) must always be set to `"0"` on a new intake append — staff update it to `"1"` manually in the sheet after entering the record into wrmd.org.
- **Never overwrite existing rows** — only ever append new rows.

### Full WRMD Column Order (73 columns)

Defined and enforced in `backend/services/sheets.py`. Columns populated at intake are marked ✅; others are left blank for later clinical entry. **REQUIRED** fields must never be empty strings on append.

| Col | Field                     | Type / Controlled Vocabulary                                                                                  | Intake ✅ |
|-----|---------------------------|---------------------------------------------------------------------------------------------------------------|-----------|
| 1   | _(index — empty)_         | —                                                                                                             |           |
| 2   | `common_name`             | **REQUIRED**, TEXT                                                                                            | ✅        |
| 3   | `admitted_at`             | **REQUIRED**, DATE (`YYYY-MM-DD`)                                                                             | ✅        |
| 4   | `admitted_by`             | TEXT                                                                                                          |           |
| 5   | `transported_by`          | TEXT                                                                                                          |           |
| 6   | `found_at`                | DATE (`YYYY-MM-DD`)                                                                                           | ✅        |
| 7   | `address_found`           | TEXT                                                                                                          | ✅        |
| 8   | `city_found`              | TEXT                                                                                                          | ✅        |
| 9   | `subdivision_found`       | TERMS: state/province/district for your country (e.g. `VA`)                                                   |           |
| 10  | `reasons_for_admission`   | TEXT                                                                                                          | ✅        |
| 11  | `care_by_rescuer`         | TEXT                                                                                                          | ✅        |
| 12  | `notes_about_rescue`      | TEXT                                                                                                          | ✅        |
| 13  | `diagnosis`               | TEXT                                                                                                          |           |
| 14  | `band`                    | TEXT                                                                                                          |           |
| 15  | `microchip_number`        | TEXT                                                                                                          |           |
| 16  | `reference_number`        | TEXT                                                                                                          |           |
| 17  | `name`                    | TEXT                                                                                                          |           |
| 18  | `keywords`                | TEXT                                                                                                          |           |
| 19  | `disposition`             | **REQUIRED**, TERMS: `Pending`, `Released`, `Transferred`, `Dead on arrival`, `Died +24hr`, `Died in 24hr`, `Euthanized +24hr`, `Euthanized in 24hr`, `Void` | |
| 20  | `transfer_type`           | TERMS: `Released`, `Continued care`, `Education or scientific research (individual)`, `Education or scientific research (institute)`, `Falconry or raptor propagation`, `Other` | |
| 21  | `release_type`            | TERMS: `Hard`, `Soft`, `Hack`, `Self`, `Returned to rescuer`, `Reunite with family`, `Fostered by animal`, `Adopted by human` | |
| 22  | `dispositioned_at`        | DATE (`YYYY-MM-DD`)                                                                                           |           |
| 23  | `disposition_location`    | TEXT                                                                                                          |           |
| 24  | `disposition_subdivision` | TERMS: state/province/district (e.g. `VA`)                                                                    |           |
| 25  | `reason_for_disposition`  | TEXT                                                                                                          |           |
| 26  | `dispositioned_by`        | TEXT                                                                                                          |           |
| 27  | `carcass_saved`           | TERMS: `1`, `0`                                                                                               |           |
| 28  | `criminal_activity`       | TERMS: `1`, `0`                                                                                               |           |
| 29  | `rescuer_organization`    | TEXT                                                                                                          |           |
| 30  | `rescuer_first_name`      | TEXT                                                                                                          | ✅        |
| 31  | `rescuer_last_name`       | TEXT                                                                                                          | ✅        |
| 32  | `rescuer_phone`           | TEXT                                                                                                          | ✅        |
| 33  | `rescuer_alt_phone`       | TEXT                                                                                                          |           |
| 34  | `rescuer_email`           | TEXT                                                                                                          |           |
| 35  | `rescuer_subdivision`     | TERMS: state/province/district (e.g. `VA`)                                                                    |           |
| 36  | `rescuer_city`            | TEXT                                                                                                          | ✅        |
| 37  | `rescuer_address`         | TEXT                                                                                                          | ✅        |
| 38  | `rescuer_postal_code`     | TEXT                                                                                                          | ✅        |
| 39  | `rescuer_notes`           | TEXT                                                                                                          |           |
| 40  | `examined_at`             | DATE (`YYYY-MM-DD`)                                                                                           |           |
| 41  | `sex`                     | TERMS: `Unknown`, `Male`, `Female`                                                                            |           |
| 42  | `weight`                  | NUMBER                                                                                                        |           |
| 43  | `weight_unit`             | TERMS: `g`, `kg`, `oz`, `lbs`                                                                                 |           |
| 44  | `bcs`                     | TERMS: `Emaciated`, `Thin`, `Reasonable`, `Good`, `Plump`                                                     |           |
| 45  | `age`                     | NUMBER                                                                                                        |           |
| 46  | `age_unit`                | TERMS: `Egg`, `Hatchling / Chick`, `Nestling`, `Fledgling`, `Juvenile`, `Adult`, `Sub-adult`, `Hatchling`, `Days`, `Weeks`, `Months`, `Years` | |
| 47  | `attitude`                | TERMS: `Alert`, `Quiet`, `Depressed`, `Obtunded`, `Stuporous`, `Non-responsive`                               |           |
| 48  | `dehydration`             | TERMS: `None`, `Mild`, `Moderate`, `Severe`                                                                   |           |
| 49  | `temperature`             | NUMBER                                                                                                        |           |
| 50  | `temperature_unit`        | TERMS: `F`, `C`                                                                                               |           |
| 51  | `mm_color`                | TERMS: `Pink`, `Pale`, `White`, `Blue`, `Yellow`, `Pigmented`, `Dark red`                                     |           |
| 52  | `mm_texture`              | TERMS: `Moist`, `Tacky`, `Oily`                                                                               |           |
| 53  | `head`                    | TEXT (notes)                                                                                                  |           |
| 54  | `head_finding`            | TERMS: `Not examined`, `No significant findings`, `Abnormal`                                                  |           |
| 55  | `cns`                     | TEXT (notes)                                                                                                  |           |
| 56  | `cns_finding`             | TERMS: `Not examined`, `No significant findings`, `Abnormal`                                                  |           |
| 57  | `cardiopulmonary`         | TEXT (notes)                                                                                                  |           |
| 58  | `cardiopulmonary_finding` | TERMS: `Not examined`, `No significant findings`, `Abnormal`                                                  |           |
| 59  | `gastrointestinal`        | TEXT (notes)                                                                                                  |           |
| 60  | `gastrointestinal_finding`| TERMS: `Not examined`, `No significant findings`, `Abnormal`                                                  |           |
| 61  | `musculoskeletal`         | TEXT (notes)                                                                                                  |           |
| 62  | `musculoskeletal_finding` | TERMS: `Not examined`, `No significant findings`, `Abnormal`                                                  |           |
| 63  | `integument`              | TEXT (notes)                                                                                                  |           |
| 64  | `integument_finding`      | TERMS: `Not examined`, `No significant findings`, `Abnormal`                                                  |           |
| 65  | `body`                    | TEXT (notes)                                                                                                  |           |
| 66  | `body_finding`            | TERMS: `Not examined`, `No significant findings`, `Abnormal`                                                  |           |
| 67  | `forelimb`                | TEXT (notes)                                                                                                  |           |
| 68  | `forelimb_finding`        | TERMS: `Not examined`, `No significant findings`, `Abnormal`                                                  |           |
| 69  | `hindlimb`                | TEXT (notes)                                                                                                  |           |
| 70  | `hindlimb_finding`        | TERMS: `Not examined`, `No significant findings`, `Abnormal`                                                  |           |
| 71  | `comments`                | TEXT                                                                                                          |           |
| 72  | `treatment`               | TEXT                                                                                                          |           |
| 73  | `examiner`                | TEXT                                                                                                          |           |
| 74  | `wrmd_processed`          | TERMS: `1`, `0` — **custom SERC column**, not part of WRMD spec                                               | ✅ (`0`)  |

> **Col 74 — `wrmd_processed`** is a custom column appended after all 73 WRMD columns. It tracks whether a row has been manually entered into [wrmd.org](https://wrmd.org). Set to `0` on every new intake append. Staff mark it `1` in the sheet after completing the WRMD entry. The back-end must never overwrite this column on existing rows.

---

## Environment Variables

### Back-End (`.env`)
```
GOOGLE_SERVICE_ACCOUNT_JSON=path/to/service-account.json
GOOGLE_SHEET_ID=1qQHxC6XYYvXPdGIAd6dgBwpPKtfraOwNkstFao4kIb8
GOOGLE_SHEET_TAB=daily-exams.csv
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
FRONTEND_ORIGIN=http://localhost:3000
```

### Front-End (`.env`)
```
REACT_APP_API_BASE_URL=http://localhost:8000
```

---

## Running Locally

### Back-End
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Front-End
```bash
cd frontend
npm install
npm start          # runs on http://localhost:3000
```

---

## Key Files (to be created)

```
backend/
  main.py                  # FastAPI app entry point
  routers/intake.py        # POST /api/intake route
  services/ocr.py          # Google Cloud Vision extraction + field parsing
  services/sheets.py       # Google Sheets append logic
  models/intake.py         # Pydantic models for intake data
  requirements.txt

frontend/
  src/
    assets/
      logo.png             # SERC circular turtle logo
    components/
      UploadForm/          # Photo capture / file upload
      ReviewForm/          # Display & edit extracted fields
      ConfirmDialog/       # Final confirmation before saving
    services/api.js        # Axios/fetch wrapper for back-end calls
    theme.js               # MUI dark theme config (colors, typography, shape)
    App.jsx
  package.json
```

---

## What NOT to Do
- Do not commit `.env` files or any credentials to version control.
- Do not store the Google Service Account JSON inside the `frontend/` directory.
- Do not skip the volunteer review step — always show extracted data before saving.
- Do not use class components or `componentDidMount` style patterns in React.
- Do not use `any` types or skip pydantic validation in Python routes.
