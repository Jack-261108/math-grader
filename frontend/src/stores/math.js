import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { gradeMath } from '../api/math';
import { getHistoryDetail } from '../api/history';
import { useConfigStore } from './config';
import { useModalStore } from './modal';
import { compressImage } from '../utils/imageCompressor';
import { formatTimerSeconds, formatSecondsToChinese } from '../constants/examTiming';

export const useMathStore = defineStore('math', () => {
  const configStore = useConfigStore();
  const modalStore = useModalStore();

  const isLoading = ref(false);
  const loadingStep = ref(1);
  const timeStr = ref('23分18秒');
  const resultData = ref(null);
  const activeImageTab = ref('scan'); // 'scan' | 'orig'

  // ⏱️ 速算计时器系统 (秒表 / 倒计时)
  const timerMode = ref('stopwatch'); // 'stopwatch' | 'countdown'
  const timerStatus = ref('idle'); // 'idle' | 'running' | 'paused' | 'finished'
  const timeElapsed = ref(0);
  const countdownTargetMinutes = ref(20);
  const timeRemaining = ref(20 * 60);
  let mathTimerInterval = null;

  const formattedTimer = computed(() => {
    if (timerMode.value === 'countdown') {
      return formatTimerSeconds(timeRemaining.value);
    }
    return formatTimerSeconds(timeElapsed.value);
  });

  const isCountdownCritical = computed(() => {
    return timerMode.value === 'countdown' && timeRemaining.value > 0 && timeRemaining.value <= 180;
  });

  function tickMathTimer() {
    timeElapsed.value++;
    if (timerMode.value === 'countdown') {
      if (timeRemaining.value > 0) {
        timeRemaining.value--;
      } else {
        timerStatus.value = 'finished';
        pauseTimer();
        timeStr.value = formatSecondsToChinese(timeElapsed.value);
        return;
      }
    }
  }

  function startTimer() {
    if (timerMode.value === 'countdown') {
      if (timeRemaining.value <= 0) {
        timeRemaining.value = countdownTargetMinutes.value * 60;
      }
    }
    timerStatus.value = 'running';
    if (mathTimerInterval) clearInterval(mathTimerInterval);
    mathTimerInterval = setInterval(tickMathTimer, 1000);
  }

  function pauseTimer() {
    if (mathTimerInterval) {
      clearInterval(mathTimerInterval);
      mathTimerInterval = null;
    }
    if (timerStatus.value === 'running') {
      timerStatus.value = 'paused';
    }
  }

  function resumeTimer() {
    if (timerStatus.value === 'paused' || timerStatus.value === 'idle') {
      timerStatus.value = 'running';
      if (mathTimerInterval) clearInterval(mathTimerInterval);
      mathTimerInterval = setInterval(tickMathTimer, 1000);
    }
  }

  function stopTimer() {
    pauseTimer();
    timerStatus.value = 'finished';
    if (timeElapsed.value > 0) {
      timeStr.value = formatSecondsToChinese(timeElapsed.value);
    }
  }

  function resetTimer() {
    pauseTimer();
    timerStatus.value = 'idle';
    timeElapsed.value = 0;
    timeRemaining.value = countdownTargetMinutes.value * 60;
  }

  function setCountdownMinutes(mins) {
    countdownTargetMinutes.value = mins;
    timeRemaining.value = mins * 60;
    if (timerStatus.value === 'idle') {
      timeElapsed.value = 0;
    }
  }

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

    if (timerStatus.value === 'running') {
      stopTimer();
    }

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
    resetTimer();
  }

  return {
    isLoading,
    loadingStep,
    timeStr,
    resultData,
    activeImageTab,
    timerMode,
    timerStatus,
    timeElapsed,
    countdownTargetMinutes,
    timeRemaining,
    formattedTimer,
    isCountdownCritical,
    startTimer,
    pauseTimer,
    resumeTimer,
    stopTimer,
    resetTimer,
    setCountdownMinutes,
    submitGrade,
    restoreTask,
    reset
  };
});
