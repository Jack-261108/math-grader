import { apiRequest } from './client';

export function gradeMath(formData) {
  return apiRequest('/api/grade', {
    method: 'POST',
    body: formData
  });
}
