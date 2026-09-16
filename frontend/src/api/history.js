import { apiRequest } from './client';

export function getHistoryList(type = 'all', limit = 100) {
  return apiRequest(`/api/history?type=${type}&limit=${limit}`);
}

export function getHistoryDetail(taskId) {
  return apiRequest(`/api/history/${taskId}`);
}

export function deleteHistoryItem(taskId) {
  return apiRequest(`/api/history/${taskId}`, {
    method: 'DELETE'
  });
}
