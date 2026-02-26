import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  timeout: 60000, // 60s — Vision API can be slow on large images
});

/**
 * Step 1 — Upload intake form photo and get extracted fields back.
 * POST /api/intake/extract
 * @param {File} imageFile
 * @returns {Promise<Object>} IntakeRecord with extracted fields
 */
export async function extractIntakeData(imageFile) {
  const formData = new FormData();
  formData.append('image', imageFile);

  const response = await api.post('/api/intake/extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  // Response shape: { extracted: IntakeRecord, warnings: string[] }
  return response.data.extracted;
}

/**
 * Step 2 — Save the volunteer-reviewed intake record to Google Sheets.
 * POST /api/intake/save
 * @param {Object} intakeData - The reviewed IntakeRecord object
 * @returns {Promise<{ success: boolean, message: string }>}
 */
export async function saveIntakeRecord(intakeData) {
  const response = await api.post('/api/intake/save', intakeData, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
}
