import { defineStore } from 'pinia';
import { ref } from 'vue';
import { gradeMath } from '../api/math';
import { getHistoryDetail } from '../api/history';
import { useConfigStore } from './config';
import { useModalStore } from './modal';
import { compressImage } from '../utils/imageCompressor';

export const useMathStore = defineStore('math', () => {
  const configStore = useConfigStore();
  const modalStore = useModalStore();

  const isLoading = ref(false);
  const loadingStep = ref(1);
  const timeStr = ref('23分18秒');
  const resultData = ref(null);
  const activeImageTab = ref('scan'); // 'scan' | 'orig'

  let stepTimer = null;

  function startStepAnimation() {
    loadingStep.value = 1;
    if (stepTimer) clearInterval(stepTimer);
    stepTimer = setInterval(() => {
      if (loadingStep.value < 4) {
        loadingStep.value++;
      }
    }, 1200);
  }

  function stopStepAnimation() {
    if (stepTimer) {
      clearInterval(stepTimer);
      stepTimer = null;
    }
  }

  async function submitGrade(file) {
    if (!file) return;
    if (!configStore.isConfigured) {
      modalStore.openSettings();
      throw new Error('请先在右上角【设置】中配置个人 Base URL 与 API Key (BYOK)！');
    }

    isLoading.value = true;
    startStepAnimation();

    try {
      const uploadFile = await compressImage(file, 2000, 0.85);
      const fd = new FormData();
      fd.append('file', uploadFile);
      fd.append('time_str', timeStr.value || '23分18秒');
      configStore.appendApiCredentials(fd);

      const data = await gradeMath(fd);
      resultData.value = data;
      activeImageTab.value = 'scan';
      return data;
    } finally {
      isLoading.value = false;
      stopStepAnimation();
    }
  }

  async function restoreTask(taskId) {
    if (!taskId) return;
    const res = await getHistoryDetail(taskId);
    const data = res.data;
    if (data && !data.task_id) {
      data.task_id = taskId;
    }
    if (!data.scan_url) data.scan_url = `/output/${taskId}_annotated_scan.jpg`;
    if (!data.orig_url) data.orig_url = `/output/${taskId}_annotated_original.jpg`;
    resultData.value = data;
    activeImageTab.value = 'scan';
    return data;
  }

  function reset() {
    resultData.value = null;
    activeImageTab.value = 'scan';
  }

  return {
    isLoading,
    loadingStep,
    timeStr,
    resultData,
    activeImageTab,
    submitGrade,
    restoreTask,
    reset
  };
});
