import { apiRequest } from './client';

export function getOmrPresets() {
  return apiRequest('/api/omr/presets');
}

export function parseAnswerImage(formData) {
  return apiRequest('/api/omr/parse_answer_image', {
    method: 'POST',
    body: formData
  });
}

export function recognizeOmrOnly(formData) {
  return apiRequest('/api/omr/recognize', {
    method: 'POST',
    body: formData
  });
}

export function gradeOmr(formData) {
  return apiRequest('/api/grade/omr', {
    method: 'POST',
    body: formData
  });
}
