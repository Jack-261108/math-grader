import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { testApiConfig } from '../api/tutor';

const STORAGE_KEY = 'math_grader_api_config';

export const useConfigStore = defineStore('config', () => {
  const baseUrl = ref('');
  const apiKey = ref('');
  const model = ref('');

  // 初始化从 localStorage 读取
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      baseUrl.value = parsed.base_url || '';
      apiKey.value = parsed.api_key || '';
      model.value = parsed.model || '';
    }
  } catch (e) {}

  const isConfigured = computed(() => {
    return Boolean(baseUrl.value.trim() && apiKey.value.trim());
  });

  function saveConfig(cfg) {
    baseUrl.value = cfg.base_url?.trim() || '';
    apiKey.value = cfg.api_key?.trim() || '';
    model.value = cfg.model?.trim() || '';
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        base_url: baseUrl.value,
        api_key: apiKey.value,
        model: model.value
      }));
    } catch (e) {}
  }

  function clearConfig() {
    baseUrl.value = '';
    apiKey.value = '';
    model.value = '';
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {}
  }

  function appendApiCredentials(formData) {
    if (baseUrl.value) formData.append('api_base_url', baseUrl.value);
    if (apiKey.value) formData.append('api_key', apiKey.value);
    if (model.value) formData.append('model', model.value);
  }

  async function testConnection(testBaseUrl, testApiKey, testModel) {
    const fd = new FormData();
    fd.append('api_base_url', testBaseUrl.trim());
    fd.append('api_key', testApiKey.trim());
    if (testModel?.trim()) {
      fd.append('model', testModel.trim());
    }
    return testApiConfig(fd);
  }

  return {
    baseUrl,
    apiKey,
    model,
    isConfigured,
    saveConfig,
    clearConfig,
    appendApiCredentials,
    testConnection
  };
});
