/**
 * 统一 API 客户端封装
 */
export async function apiRequest(url, options = {}) {
  const defaultHeaders = {};

  // 如果 body 是普通对象且不是 FormData，则转为 JSON
  let body = options.body;
  if (body && typeof body === 'object' && !(body instanceof FormData) && !(body instanceof Blob)) {
    defaultHeaders['Content-Type'] = 'application/json';
    body = JSON.stringify(body);
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers || {})
    },
    body
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}`;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch (e) {
      try {
        const errText = await response.text();
        if (errText) errorDetail = errText.slice(0, 200);
      } catch (_) {}
    }
    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }

  return response.json();
}
