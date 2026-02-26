import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
});

/**
 * POST /api/intake
 * Upload an intake sheet image for OCR extraction.
 * @param {File} imageFile - The image file from the browser file input or camera
 * @returns {Promise<Object>} - IntakeRecord JSON with extracted fields
 */
export async function extractIntakeData(imageFile) {
  const formData = new FormData();
  formData.append('file', imageFile);
  const response = await api.post('/api/intake', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

/**
 * POST /api/intake/save
 * Save a reviewed IntakeRecord to Google Sheets.
 * @param {Object} intakeData - The reviewed IntakeRecord object
 * @returns {Promise<Object>} - Confirmation response
 *
 * NOTE: This is currently mocked — the back-end endpoint has not been built yet.
 * Remove the mock and uncomment the real call once the back-end is ready.
 */
export async function saveIntakeRecord(intakeData) {
  // --- MOCK: remove when back-end /api/intake/save is implemented ---
  console.log('Mock save — would POST to /api/intake/save:', intakeData);
  await new Promise((resolve) => setTimeout(resolve, 800)); // simulate network delay
  return { success: true };
  // --- END MOCK ---

  // const response = await api.post('/api/intake/save', intakeData);
  // return response.data;
}
