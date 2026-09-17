import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { gradeMath } from '../api/math';
import { getHistoryDetail } from '../api/history';
import { useConfigStore } from './config';
import { useModalStore } from './modal';
import { compressImage } from '../utils/imageCompressor';
import { formatTimerSeconds, formatSecondsToChinese, playExamChime, speakExamBroadcast } from '../constants/examTiming';

export const useMathStore = defineStore('math', () => {
  const configStore = useConfigStore();
  const modalStore = useModalStore();

  const isLoading = ref(false);
  const loadingStep = ref(1);
  const timeStr = ref('23分18秒');
  const resultData = ref(null);
  const activeImageTab = ref('scan'); // 'scan' | 'orig'

  // ⏱️ 速算计时器系统 (秒表 / 极速倒计时 / 配速段位联动)
  const timerMode = ref('stopwatch'); // 'stopwatch' | 'countdown'
  const timerStatus = ref('idle'); // 'idle' | 'running' | 'paused' | 'finished'
  const timeElapsed = ref(0);
  const countdownTargetMinutes = ref(5); // 默认 5 分钟极速挑战
  const timeRemaining = ref(5 * 60);
  const targetItemCount = ref(20); // 预设计划题量 (默认 20 题)
  const isScreenWakeLocked = ref(false);
  const soundMode = ref('beep'); // 'beep' | 'voice' | 'mute'
  const isFullscreenTimer = ref(false);
  const laps = ref([]); // 分段打卡记录: [{ id, lapSeconds, totalSeconds, label, pace }]
  let mathTimerInterval = null;
  let wakeLockSentinel = null;

  const formattedTimer = computed(() => {
    if (timerMode.value === 'countdown') {
      return formatTimerSeconds(timeRemaining.value);
    }
    return formatTimerSeconds(timeElapsed.value);
  });

  const isCountdownWarning = computed(() => {
    return timerMode.value === 'countdown' && timeRemaining.value > 20 && timeRemaining.value <= 60;
  });

  const isCountdownCritical = computed(() => {
    return timerMode.value === 'countdown' && timeRemaining.value > 0 && timeRemaining.value <= 20;
  });

  // 实时单题平均耗时 (秒/题)
  const realtimePace = computed(() => {
    const count = targetItemCount.value || 20;
    if (timeElapsed.value === 0 || count === 0) return 0.0;
    return Math.round((timeElapsed.value / count) * 10) / 10;
  });

  // 实时段位评价
  const speedRank = computed(() => {
    const pace = realtimePace.value;
    if (pace === 0) {
      return { level: '待开跑', color: 'slate', icon: '⏱️', text: '开始计时后将实时评估配速段位', badgeClass: 'bg-slate-100 text-slate-700 border-slate-200' };
    }
    if (pace <= 8.0) {
      return { level: '王者极速', color: 'emerald', icon: '🏆', text: '极速神算！达国家级高手心算水准', badgeClass: 'bg-emerald-100 text-emerald-800 border-emerald-300 font-extrabold' };
    }
    if (pace <= 15.0) {
      return { level: '黄金标准', color: 'blue', icon: '⚡', text: '完全达标公考行测资料分析黄金配速', badgeClass: 'bg-blue-100 text-blue-800 border-blue-300 font-bold' };
    }
    if (pace <= 25.0) {
      return { level: '进阶钻石', color: 'amber', icon: '📈', text: '节奏稳健，重点强化截位直除可破15秒', badgeClass: 'bg-amber-100 text-amber-800 border-amber-300' };
    }
    return { level: '青铜蓄力', color: 'rose', icon: '⏳', text: '单题耗时略长，实战容易超时需提速', badgeClass: 'bg-rose-100 text-rose-800 border-rose-300' };
  });

  // 防息屏常亮控制 (Web Screen Wake Lock API)
  async function requestScreenWakeLock() {
    if (typeof navigator !== 'undefined' && 'wakeLock' in navigator) {
      try {
        wakeLockSentinel = await navigator.wakeLock.request('screen');
        isScreenWakeLocked.value = true;
        wakeLockSentinel.addEventListener('release', () => {
          isScreenWakeLocked.value = false;
        });
      } catch (err) {
        isScreenWakeLocked.value = false;
      }
    }
  }

  async function releaseScreenWakeLock() {
    if (wakeLockSentinel) {
      try {
        await wakeLockSentinel.release();
        wakeLockSentinel = null;
      } catch (e) {}
      isScreenWakeLocked.value = false;
    }
  }

  function triggerSoundAlert(type, text = "") {
    if (soundMode.value === 'mute') return;
    if (soundMode.value === 'beep' || soundMode.value === 'voice') {
      playExamChime(type);
    }
    if (soundMode.value === 'voice' && text) {
      speakExamBroadcast(text);
    }
  }

  function tickMathTimer() {
    timeElapsed.value++;
    if (timerMode.value === 'countdown') {
      if (timeRemaining.value > 0) {
        timeRemaining.value--;
        // 关键冲刺节点提示音
        if (timeRemaining.value === 60) {
          triggerSoundAlert('warning', '速算冲刺提示：离挑战结束还有1分钟');
        } else if (timeRemaining.value === 10) {
          triggerSoundAlert('warning', '最后10秒');
        } else if (timeRemaining.value <= 3 && timeRemaining.value >= 1) {
          triggerSoundAlert('lap');
        }
      } else {
        timerStatus.value = 'finished';
        pauseTimer();
        timeStr.value = formatSecondsToChinese(timeElapsed.value);
        triggerSoundAlert('finish', '挑战时间到，请立即停笔准备批改');
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
    requestScreenWakeLock();
    triggerSoundAlert('start', '开始速算挑战');
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
    releaseScreenWakeLock();
  }

  function resumeTimer() {
    if (timerStatus.value === 'paused' || timerStatus.value === 'idle') {
      timerStatus.value = 'running';
      requestScreenWakeLock();
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
    triggerSoundAlert('finish', '速算作答完成，请对准练习册拍照批改');
    releaseScreenWakeLock();
  }

  function resetTimer() {
    pauseTimer();
    timerStatus.value = 'idle';
    timeElapsed.value = 0;
    timeRemaining.value = countdownTargetMinutes.value * 60;
    laps.value = [];
    releaseScreenWakeLock();
  }

  function setCountdownMinutes(mins) {
    countdownTargetMinutes.value = mins;
    timeRemaining.value = mins * 60;
    if (timerStatus.value === 'idle') {
      timeElapsed.value = 0;
    }
  }

  // 记录分段打卡 (如第 10 题或前半部分耗时)
  function recordLap(customLabel = "") {
    const prevLapTotal = laps.value.length > 0 ? laps.value[laps.value.length - 1].totalSeconds : 0;
    const lapSpent = timeElapsed.value - prevLapTotal;
    const label = customLabel || `第 ${laps.value.length + 1} 阶段`;
    laps.value.push({
      id: laps.value.length + 1,
      lapSeconds: Math.max(1, lapSpent),
      totalSeconds: timeElapsed.value,
      label,
      lapTimeStr: formatSecondsToChinese(lapSpent),
      totalTimeStr: formatSecondsToChinese(timeElapsed.value)
    });
    triggerSoundAlert('lap', `${label}打卡`);
  }

  // 快捷微调用时 (加减秒数)
  function adjustTimeSeconds(deltaSec) {
    timeElapsed.value = Math.max(0, timeElapsed.value + deltaSec);
    timeStr.value = formatSecondsToChinese(timeElapsed.value);
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
    targetItemCount,
    isScreenWakeLocked,
    soundMode,
    isFullscreenTimer,
    laps,
    formattedTimer,
    isCountdownWarning,
    isCountdownCritical,
    realtimePace,
    speedRank,
    startTimer,
    pauseTimer,
    resumeTimer,
    stopTimer,
    resetTimer,
    setCountdownMinutes,
    recordLap,
    adjustTimeSeconds,
    requestScreenWakeLock,
    releaseScreenWakeLock,
    triggerSoundAlert,
    submitGrade,
    restoreTask,
    reset
  };
});
