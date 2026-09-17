import { apiRequest } from './client';

export function gradeMath(formData) {
  return apiRequest('/api/grade', {
    method: 'POST',
    body: formData
  });
}

export function getTargetedExercises(weaknessType, count = 20, weaknessName = '') {
  const fd = new FormData();
  if (weaknessType) fd.append('weakness_type', weaknessType);
  fd.append('count', String(count));
  if (weaknessName) fd.append('weakness_name', weaknessName);
  return apiRequest('/api/math/generate-targeted-exercises', {
    method: 'POST',
    body: fd
  });
}
