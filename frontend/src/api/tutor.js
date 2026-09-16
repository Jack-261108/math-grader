import { apiRequest } from './client';

export function getAiExplanation(formData) {
  return apiRequest('/api/ai/explain', {
    method: 'POST',
    body: formData
  });
}

export function testApiConfig(formData) {
  return apiRequest('/api/test_config', {
    method: 'POST',
    body: formData
  });
}
