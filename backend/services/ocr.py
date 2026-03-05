"""
OCR service — Google Cloud Vision API integration.

Sends an intake form image to Vision API using DOCUMENT_TEXT_DETECTION,
then parses the raw text into an IntakeRecord using regex and keyword matching.

The SERC intake form layout has labels and values on adjacent lines, e.g.:
  Species/Common Name:
  Eastern Box Turtle

This parser handles both same-line and next-line value layouts.
"""

import json
import os
import re
import logging

from google.cloud import vision
from google.oauth2 import service_account

from models.intake import IntakeRecord
from utils.dates import parse_date

logger = logging.getLogger(__name__)

# ── Admission reason keywords (ordered — checked first) ──────────────────────
_REASON_KEYWORDS = [
    ("displaced", "Displaced"),
    ("injured", "Injured"),
    ("orphaned", "Orphaned"),
    ("sick", "Sick"),
    ("other", "Other"),
]


def _get_vision_client() -> vision.ImageAnnotatorClient:
    """
    Build a Vision API client.

    Credential resolution order:
      1. GOOGLE_SERVICE_ACCOUNT_JSON contains raw JSON (Cloud Run secret-as-env)
      2. GOOGLE_SERVICE_ACCOUNT_JSON is a file path (local dev)
      3. Application Default Credentials (Cloud Run with attached service account)
    """
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]

    if raw.startswith("{"):
        # Inline JSON string
        info = json.loads(raw)
        credentials = service_account.Credentials.from_service_account_info(info, scopes=scopes)
        return vision.ImageAnnotatorClient(credentials=credentials)

    if raw:
        # File path
        credentials = service_account.Credentials.from_service_account_file(raw, scopes=scopes)
        return vision.ImageAnnotatorClient(credentials=credentials)

    # Fall back to Application Default Credentials
    return vision.ImageAnnotatorClient()


def _extract_raw_text(image_bytes: bytes) -> str:
    """Send image bytes to Vision API and return the full raw text."""
    client = _get_vision_client()
    image = vision.Image(content=image_bytes)
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise RuntimeError(f"Vision API error: {response.error.message}")

    return response.full_text_annotation.text


def _is_label(text: str) -> bool:
    """Return True if text looks like a form label rather than a field value."""
    return bool(
        re.match(r"^[A-Za-z /\(\)]+:$", text)
        # Parenthetical label continuation, e.g. "(food, water, medications, treatments):"
        or re.match(r"^\([^)]+\):?$", text)
    )


def _find_field(text: str, *labels: str, next_line: bool = False) -> str | None:
    """
    Find the value following any of the given label strings in OCR text.

    Tries two strategies for each label:
      1. Same-line: "Label: value"
      2. Next-line: label on one line, value on the next (next_line=True)

    Returns the first non-empty match.
    """
    lines = text.splitlines()

    for label in labels:
        escaped = re.escape(label)

        # Strategy 1: same-line  "Label: value"
        pattern = rf"{escaped}\s*[:\-]?\s*(.+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Remove bleed-through from next label on same line
            value = re.split(r"\s{3,}|\n", value)[0].strip()
            if value and not _is_label(value):
                return value

        # Strategy 2: next-line — label alone on a line, value follows
        for i, line in enumerate(lines):
            if re.search(escaped, line, re.IGNORECASE) and i + 1 < len(lines):
                next = lines[i + 1].strip()
                if next and not _is_label(next):
                    return next

    return None


def _find_field_after(text: str, label: str, max_lines: int = 4) -> str | None:
    """
    More aggressive next-line search: find the first non-empty, non-label
    line that appears after the given label anywhere in the text.
    """
    lines = text.splitlines()
    escaped = re.escape(label)
    for i, line in enumerate(lines):
        if re.search(escaped, line, re.IGNORECASE):
            for j in range(i + 1, min(i + max_lines + 1, len(lines))):
                candidate = lines[j].strip()
                if candidate and not _is_label(candidate):
                    return candidate
    return None


def _parse_name(full_name: str | None) -> tuple[str | None, str | None]:
    """Split 'First Last' into (first, last). Handles middle names/initials."""
    if not full_name:
        return None, None
    # Remove parenthetical nicknames e.g. "Migdalia (micky) Blair"
    cleaned = re.sub(r"\(.*?\)", "", full_name).strip()
    parts = cleaned.split()
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[-1]


def _parse_address(raw: str | None) -> tuple[str | None, str | None, str | None]:
    """
    Attempt to split a raw address string into (street, city, postal_code).
    Handles formats like:
      "1238 water warwick drive UB 23453"
      "123 Main St, CityName 23456"
    Returns (street, city, postal_code) — any may be None.
    """
    if not raw:
        return None, None, None

    raw = raw.strip()

    # Extract ZIP (5-digit)
    zip_match = re.search(r"\b(\d{5})(?:-\d{4})?\b", raw)
    postal_code = zip_match.group(1) if zip_match else None

    # Remove ZIP and preceding 2-letter state abbrev
    cleaned = re.sub(r"\b[A-Z]{2}\b\s*\d{5}(?:-\d{4})?", "", raw).strip().rstrip(",").strip()
    cleaned = re.sub(r"\b\d{5}(?:-\d{4})?\b", "", cleaned).strip().rstrip(",").strip()

    # Split on comma: "street, city"
    if "," in cleaned:
        parts = [p.strip() for p in cleaned.split(",", 1)]
        return parts[0] or None, parts[1] or None, postal_code

    # Heuristic: street is everything with a leading number
    street_match = re.match(r"(\d+\s+.+?)(?:\s{2,}|\s+[A-Z][a-z]+\s*$)", cleaned)
    if street_match:
        street = street_match.group(1).strip()
        city = cleaned[len(street):].strip() or None
        return street or None, city, postal_code

    return cleaned or None, None, postal_code


def _parse_reason(text: str) -> str | None:
    """
    Detect which admission reason checkbox was ticked.

    The form label is "Reason for intake" followed by options:
    "Injured ( ) Orphaned ( ) Displaced (✓) Sick ( ) Other (Specify)"
    Vision OCR may render the checkmark as ✓, √, x, X, or similar.

    Strategy:
      1. Find checkmark adjacent to a keyword anywhere in the full text
      2. Build a window starting at "Reason for intake" label and search that block
    """
    checkmark = r"[✓✗√xX\*]"

    # Strategy 1: checkmark adjacent to keyword anywhere in full text
    for keyword, value in _REASON_KEYWORDS:
        pattern = rf"{keyword}\s*\({checkmark}|{checkmark}\s*\)?\s*{keyword}|{keyword}\s*{checkmark}|\({checkmark}\)\s*{keyword}"
        if re.search(pattern, text, re.IGNORECASE):
            return value

    # Build a reason window starting at the "Reason for intake" label,
    # spanning up to 4 lines to capture multi-line OCR output
    lines = text.splitlines()
    reason_window = []
    for i, line in enumerate(lines):
        if re.search(r"reason\s+for\s+intake", line, re.IGNORECASE):
            reason_window = lines[i : min(i + 4, len(lines))]
            break

    # Fall back to any line containing a reason keyword if label not found
    if not reason_window:
        for i, line in enumerate(lines):
            if re.search(r"injured|orphaned|displaced|sick", line, re.IGNORECASE):
                reason_window = lines[i : min(i + 3, len(lines))]
                break

    if not reason_window:
        return None

    reason_block = " ".join(reason_window)
    logger.debug("Reason block: %s", reason_block)

    # Strategy 2: checkmark near keyword in the joined block
    for keyword, value in _REASON_KEYWORDS:
        pattern = rf"{keyword}\s*\({checkmark}|{checkmark}\s*\)?\s*{keyword}|{keyword}\s*{checkmark}|\({checkmark}\)\s*{keyword}"
        if re.search(pattern, reason_block, re.IGNORECASE):
            return value

    return None


# ── Public API ───────────────────────────────────────────────────────────────

def extract_intake_fields(image_bytes: bytes) -> IntakeRecord:
    """
    Main entry point: send image to Vision API and parse into IntakeRecord.
    Raises RuntimeError on Vision API failure.
    """
    raw_text = _extract_raw_text(image_bytes)
    logger.debug("Raw OCR text:\n%s", raw_text)

    # ── Date ──────────────────────────────────────────────────────────────────
    # The form's "Date" field is used for both found and admitted dates.
    form_date = parse_date(_find_field(raw_text, "Date", "Date Found")) or ""
    found_at = form_date or None
    admitted_at = form_date

    # ── Species ───────────────────────────────────────────────────────────────
    # The form has "Species/Common Name:" label with the value on the NEXT line.
    # Use max_lines=2 to avoid jumping into the rescuer section if the field is blank.
    common_name = (
        _find_field_after(raw_text, "Species/Common Name", max_lines=2)
        or _find_field_after(raw_text, "Common Name", max_lines=2)
        or ""
    )
    # Guard: if it still looks like a label, clear it
    if _is_label(common_name):
        common_name = ""

    # ── Rescuer name ──────────────────────────────────────────────────────────
    full_name = _find_field(raw_text, "Full Name", "Rescuer Name", "Finder")
    rescuer_first, rescuer_last = _parse_name(full_name)

    # ── Rescuer phone ─────────────────────────────────────────────────────────
    # Try the label first; fall back to regex scan for any 10-digit number.
    raw_phone = _find_field(raw_text, "Contact Number", "Phone", "Phone Number")
    if not raw_phone:
        phone_match = re.search(r"\b(\(?\d{3}\)?[\-\.\s]\d{3}[\-\.\s]\d{4})\b", raw_text)
        raw_phone = phone_match.group(1).strip() if phone_match else None
    rescuer_phone = raw_phone

    # ── Rescuer address ───────────────────────────────────────────────────────
    # Try the label first; fall back to finding the first line that starts with
    # a street number (handles same-line and next-line OCR layouts).
    raw_address = _find_field(raw_text, "Address")
    if not raw_address:
        for line in raw_text.splitlines():
            line = line.strip()
            if re.match(r"^\d+\s+[A-Za-z]", line):
                if not re.match(r"^\d{5}$", line) and not re.search(r"\d{3}[\-\.]\d{4}", line):
                    raw_address = line
                    break
    rescuer_address, rescuer_city, rescuer_postal_code = _parse_address(raw_address)

    # ── Location found (if different) ─────────────────────────────────────────
    raw_location = _find_field(
        raw_text,
        "Location Found (if different)",
        "Location Found",
        "Found Location",
        "Where Found",
    )
    address_found: str | None = None
    city_found: str | None = None
    if raw_location:
        if re.search(r"\d", raw_location):
            address_found, city_found, _ = _parse_address(raw_location)
        else:
            city_found = raw_location.strip()

    # ── Intake reason ─────────────────────────────────────────────────────────
    reasons_for_admission = _parse_reason(raw_text)

    # ── Free-text fields ──────────────────────────────────────────────────────
    notes_about_rescue = _find_field(
        raw_text,
        "Details about rescue or other relevant information",
        "Details about rescue",
        "Rescue details",
        "Notes",
    )

    care_by_rescuer = _find_field(
        raw_text,
        "Care given (food, water, medications, treatments)",
        "Care given",
        "Care provided",
        "Treatment",
    )

    return IntakeRecord(
        common_name=common_name,
        admitted_at=admitted_at,
        rescuer_first_name=rescuer_first,
        rescuer_last_name=rescuer_last,
        rescuer_phone=rescuer_phone,
        rescuer_address=rescuer_address,
        rescuer_city=rescuer_city,
        rescuer_postal_code=rescuer_postal_code,
        found_at=found_at,
        address_found=address_found,
        city_found=city_found,
        reasons_for_admission=reasons_for_admission,
        notes_about_rescue=notes_about_rescue,
        care_by_rescuer=care_by_rescuer,
    )
