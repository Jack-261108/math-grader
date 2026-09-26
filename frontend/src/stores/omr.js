import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { getOmrPresets, parseAnswerImage, recognizeOmrOnly, gradeOmr } from '../api/omr';
import { useConfigStore } from './config';
import { useModalStore } from './modal';
import { compressImage } from '../utils/imageCompressor';
import { DEFAULT_EXAM_DURATION_MINUTES, formatTimerSeconds, formatSecondsToChinese, playExamChime, speakExamBroadcast, getSectionBenchmark } from '../constants/examTiming';
import { globalWakeLock } from '../utils/wakeLockHelper';

const FALLBACK_PRESETS = {
  guokao_135: {
    name: "国家公务员考试 (副省级 135题)",
    total_questions: 135,
    full_score: 100.0,
    sections: [
      { id: "common_sense", name: "常识判断", start_q: 1, end_q: 20, score_per_q: 0.5 },
      { id: "verbal", name: "言语理解与表达", start_q: 21, end_q: 60, score_per_q: 0.8 },
      { id: "quantity", name: "数量关系", start_q: 61, end_q: 75, score_per_q: 0.8 },
      { id: "reasoning", name: "判断推理", start_q: 76, end_q: 115, score_per_q: 0.75 },
      { id: "data_analysis", name: "资料分析", start_q: 116, end_q: 135, score_per_q: 0.8 }
    ]
  },
  shengkao_120: {
    name: "省公务员考试 (多省通用 120题)",
    total_questions: 120,
    full_score: 100.0,
    sections: [
      { id: "common_sense", name: "常识判断", start_q: 1, end_q: 20, score_per_q: 0.5 },
      { id: "verbal", name: "言语理解与表达", start_q: 21, end_q: 55, score_per_q: 0.9 },
      { id: "quantity", name: "数量关系", start_q: 56, end_q: 65, score_per_q: 1.0 },
      { id: "reasoning", name: "判断推理", start_q: 66, end_q: 100, score_per_q: 0.8 },
      { id: "data_analysis", name: "资料分析", start_q: 101, end_q: 120, score_per_q: 1.025 }
    ]
  },
  dagang_130: {
    name: "新大纲标准卷 (政治理论20题+五大模块 130题)",
    total_questions: 130,
    full_score: 100.0,
    sections: [
      { id: "politics", name: "政治理论", start_q: 1, end_q: 20, score_per_q: 0.5 },
      { id: "common_sense", name: "常识判断", start_q: 21, end_q: 35, score_per_q: 0.6 },
      { id: "verbal", name: "言语理解与表达", start_q: 36, end_q: 65, score_per_q: 0.9 },
      { id: "quantity", name: "数量关系", start_q: 66, end_q: 75, score_per_q: 1.0 },
      { id: "reasoning", name: "判断推理", start_q: 76, end_q: 110, score_per_q: 0.7 },
      { id: "data_analysis", name: "资料分析", start_q: 111, end_q: 130, score_per_q: 0.975 }
    ]
  },
  dagang_120: {
    name: "公考新大纲 (政治理论+五大模块 120题)",
    total_questions: 120,
    full_score: 100.0,
    sections: [
      { id: "politics", name: "政治理论", start_q: 1, end_q: 15, score_per_q: 0.6 },
      { id: "common_sense", name: "常识判断", start_q: 16, end_q: 25, score_per_q: 0.5 },
      { id: "verbal", name: "言语理解与表达", start_q: 26, end_q: 55, score_per_q: 0.9 },
      { id: "quantity", name: "数量关系", start_q: 56, end_q: 70, score_per_q: 0.9 },
      { id: "reasoning", name: "判断推理", start_q: 71, end_q: 100, score_per_q: 0.8 },
      { id: "data_analysis", name: "资料分析", start_q: 101, end_q: 120, score_per_q: 1.075 }
    ]
  },
  special_practice_20: {
    name: "模块专项突击卡 (20题 / 20分)",
    total_questions: 20,
    full_score: 20.0,
    sections: [
      { id: "practice", name: "专项练习", start_q: 1, end_q: 20, score_per_q: 1.0 }
    ]
  },
  special_practice_30: {
    name: "小卷模考练习卡 (30题 / 30分)",
    total_questions: 30,
    full_score: 30.0,
    sections: [
      { id: "practice", name: "微模考卷", start_q: 1, end_q: 30, score_per_q: 1.0 }
    ]
  }
};

export const useOmrStore = defineStore('omr', () => {
  const configStore = useConfigStore();
  const modalStore = useModalStore();

  const presets = ref(FALLBACK_PRESETS);
  const currentPresetId = ref('guokao_135');
  const currentSections = ref(JSON.parse(JSON.stringify(FALLBACK_PRESETS.guokao_135.sections)));
  const isSectionDrawerOpen = ref(false);

  const answerKey = ref('');
  const timeStr = ref('110分00秒');
  const activeSubMode = ref('scan'); // 'scan' | 'online'
  const onlineViewMode = ref('sheet'); // 'sheet' | 'exam'
  const onlineAnswers = ref({}); // { 1: 'A', 2: 'B', ... }

  // 全真模考与做题节奏监控
  const isMockExamActive = ref(false);
  const examDurationMinutes = ref(DEFAULT_EXAM_DURATION_MINUTES);
  const examTimeRemaining = ref(DEFAULT_EXAM_DURATION_MINUTES * 60);
  const examTimeElapsed = ref(0);
  const examTimerStatus = ref('idle'); // 'idle' | 'running' | 'paused' | 'finished'
  const paperTimerMode = ref('countdown'); // 'countdown' | 'stopwatch'
  const questionTimes = ref({}); // { [qNum]: seconds }
  const sectionTimes = ref({}); // { [secId]: seconds }
  const activeTrackingQ = ref(1);
  const activePaperSecKey = ref(''); // 当前纸质做题打卡聚焦模块
  const isScreenWakeLocked = ref(false);
  const soundAlertMode = ref('voice'); // 'voice' | 'beep' | 'mute'
  const isManualTimeOpen = ref(false);
  const manualSectionMinutes = ref({}); // { [secKey]: minutes }
  const isFullscreenPaperTimer = ref(false);
  let timerInterval = null;
  let wakeLockSentinel = null;

  const isLoading = ref(false);
  const loadingTitle = ref('正在智能批改行测答题卡...');
  const loadingSubtitle = ref('正在识别填涂卡点位并分模块核算分值');

  const resultData = ref(null);
  const currentResultTab = ref('diag'); // 'diag' | 'card'
  const isMatrixExpanded = ref(true);

  // 核验与纠偏状态
  const rawTaskId = ref('');
  const originalStudentAnswers = ref({});
  const workingStudentAnswers = ref({});
  const verifyFilter = ref('all'); // 'all' | 'wrong' | 'unans' | 'corrected'

  // 计算属性
  const totalQuestions = computed(() => {
    let t = 0;
    currentSections.value.forEach(s => {
      t += Math.max(0, s.end_q - s.start_q + 1);
    });
    return t || 135;
  });

  const fullScore = computed(() => {
    let s = 0.0;
    currentSections.value.forEach(sec => {
      s += (sec.end_q - sec.start_q + 1) * sec.score_per_q;
    });
    return Math.round(s * 100) / 100;
  });

  const answeredOnlineCount = computed(() => {
    const totalQ = totalQuestions.value;
    return Object.keys(onlineAnswers.value).filter(k => {
      const q = parseInt(k);
      return q >= 1 && q <= totalQ && Boolean(onlineAnswers.value[k]);
    }).length;
  });

  const correctionDiffKeys = computed(() => {
    return Object.keys(workingStudentAnswers.value).filter(k => {
      const orig = originalStudentAnswers.value[k] || null;
      const work = workingStudentAnswers.value[k] || null;
      return orig !== work;
    });
  });

  const formattedTimeRemaining = computed(() => formatTimerSeconds(examTimeRemaining.value));
  const formattedTimeElapsed = computed(() => formatSecondsToChinese(examTimeElapsed.value));
  const averagePaceSeconds = computed(() => {
    const answered = answeredOnlineCount.value;
    if (answered === 0 || examTimeElapsed.value === 0) return 0;
    return Math.round(examTimeElapsed.value / answered);
  });
  const isTimeCritical = computed(() => paperTimerMode.value === 'countdown' && examTimeRemaining.value > 0 && examTimeRemaining.value <= 300);
  const isTimeWarning = computed(() => paperTimerMode.value === 'countdown' && examTimeRemaining.value > 300 && examTimeRemaining.value <= 900);

  // 纸质做题当前模块计算属性
  const effectiveActivePaperSec = computed(() => {
    if (!currentSections.value || currentSections.value.length === 0) return null;
    if (activePaperSecKey.value) {
      const found = currentSections.value.find(s => (s.id || s.name) === activePaperSecKey.value);
      if (found) return found;
    }
    return currentSections.value[0];
  });

  const effectivePaperSecKey = computed(() => {
    const sec = effectiveActivePaperSec.value;
    return sec ? (sec.id || sec.name) : 'common_sense';
  });

  const activePaperBenchmark = computed(() => {
    const sec = effectiveActivePaperSec.value;
    if (!sec) return getSectionBenchmark();
    return getSectionBenchmark(sec.id, sec.name);
  });

  const activePaperSecElapsed = computed(() => {
    const key = effectivePaperSecKey.value;
    return sectionTimes.value[key] || 0;
  });

  const activePaperTargetSeconds = computed(() => {
    const sec = effectiveActivePaperSec.value;
    if (!sec) return 600;
    const qCount = Math.max(1, sec.end_q - sec.start_q + 1);
    const bench = activePaperBenchmark.value;
    // 优先采用 单题建议用时 * 题数
    return Math.round((bench.perQSec || 50) * qCount);
  });

  const activePaperProgressPct = computed(() => {
    const target = activePaperTargetSeconds.value;
    if (!target) return 0;
    const pct = Math.round((activePaperSecElapsed.value / target) * 100);
    return Math.min(100, Math.max(0, pct));
  });

  const activePaperIsOvertime = computed(() => {
    return activePaperSecElapsed.value > activePaperTargetSeconds.value;
  });

  // 动作
  function findSectionForQ(qNum) {
    const num = parseInt(qNum, 10);
    return currentSections.value.find(s => num >= s.start_q && num <= s.end_q) || null;
  }

  // 防息屏常亮控制 (基于全局高可用常亮控制器，切屏切回自动重新激活)
  globalWakeLock.onStatusChange((active) => {
    isScreenWakeLocked.value = active;
  });

  async function requestScreenWakeLock() {
    isScreenWakeLocked.value = true;
    await globalWakeLock.acquire();
  }

  async function releaseScreenWakeLock() {
    isScreenWakeLocked.value = false;
    await globalWakeLock.release();
  }

  function triggerSoundAlert(type, text = "") {
    if (soundAlertMode.value === 'mute') return;
    if (soundAlertMode.value === 'beep' || soundAlertMode.value === 'voice') {
      playExamChime(type);
    }
    if (soundAlertMode.value === 'voice' && text) {
      speakExamBroadcast(text);
    }
  }

  function tickTimer() {
    if (paperTimerMode.value === 'countdown') {
      if (examTimeRemaining.value > 0) {
        examTimeRemaining.value--;
        // 关键节点考场提醒
        if (examTimeRemaining.value === 900) {
          triggerSoundAlert('warning', '考场提示：离考试结束还有15分钟，请注意填涂答题卡并检查个人信息。');
        } else if (examTimeRemaining.value === 300) {
          triggerSoundAlert('warning', '考场紧急提示：离考试结束还有5分钟，请准备停笔。');
        }
      } else {
        examTimerStatus.value = 'finished';
        triggerSoundAlert('finish', '考试时间到，请全体考生停止答题。');
        pauseMockExam();
        return;
      }
    }
    examTimeElapsed.value++;

    // 纸质做题场景：每秒同步累加当前聚焦模块用时
    const pKey = effectivePaperSecKey.value;
    if (pKey) {
      sectionTimes.value[pKey] = (sectionTimes.value[pKey] || 0) + 1;
    }

    // 在线做题单题追踪（兼容在线答题模式）
    const q = activeTrackingQ.value;
    if (q) {
      const prev = questionTimes.value[q] || 0;
      if (prev < 300) {
        questionTimes.value[q] = prev + 1;
      }
    }
  }

  function startMockExam(durationMin, mode = 'countdown') {
    paperTimerMode.value = mode;
    const targetMin = durationMin || (totalQuestions.value <= 30 ? Math.max(15, totalQuestions.value) : DEFAULT_EXAM_DURATION_MINUTES);
    examDurationMinutes.value = targetMin;
    examTimeRemaining.value = targetMin * 60;
    examTimeElapsed.value = 0;
    isMockExamActive.value = true;
    examTimerStatus.value = 'running';
    if (!activePaperSecKey.value && currentSections.value && currentSections.value.length > 0) {
      activePaperSecKey.value = currentSections.value[0].id || currentSections.value[0].name;
    }
    requestScreenWakeLock();
    triggerSoundAlert('start', '考试开始，请全体考生开始答卷。');

    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(tickTimer, 1000);
  }

  function pauseMockExam() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
    if (examTimerStatus.value === 'running') {
      examTimerStatus.value = 'paused';
    }
    releaseScreenWakeLock();
  }

  function resumeMockExam() {
    if (examTimerStatus.value === 'paused' || examTimerStatus.value === 'idle') {
      examTimerStatus.value = 'running';
      isMockExamActive.value = true;
      requestScreenWakeLock();
      if (timerInterval) clearInterval(timerInterval);
      timerInterval = setInterval(tickTimer, 1000);
    }
  }

  function resetMockExam() {
    pauseMockExam();
    examTimerStatus.value = 'idle';
    isMockExamActive.value = false;
    const targetMin = totalQuestions.value <= 30 ? Math.max(15, totalQuestions.value) : DEFAULT_EXAM_DURATION_MINUTES;
    examDurationMinutes.value = targetMin;
    examTimeRemaining.value = targetMin * 60;
    examTimeElapsed.value = 0;
    questionTimes.value = {};
    sectionTimes.value = {};
    activeTrackingQ.value = 1;
    if (currentSections.value && currentSections.value.length > 0) {
      activePaperSecKey.value = currentSections.value[0].id || currentSections.value[0].name;
    }
    releaseScreenWakeLock();
  }

  // 纸质做题：切换当前作答模块（自由跳序作答）
  function switchPaperSection(secKey) {
    if (!secKey) return;
    activePaperSecKey.value = secKey;
    const sec = currentSections.value.find(s => (s.id || s.name) === secKey);
    if (sec) {
      triggerSoundAlert('lap', `已切换至${sec.name}，建议用时${Math.round((activePaperBenchmark.value?.targetMin || 25))}分钟。`);
    }
  }

  // 纸质做题：完成当前模块打卡并自动顺延下一模块
  function lapPaperSection() {
    const curSec = effectiveActivePaperSec.value;
    const curSecName = curSec ? curSec.name : "当前模块";
    const curElapsedSec = activePaperSecElapsed.value;
    const curElapsedStr = formatSecondsToChinese(curElapsedSec);

    // 顺延查找下一个未完结的模块
    const secs = currentSections.value || [];
    const curIdx = secs.findIndex(s => (s.id || s.name) === effectivePaperSecKey.value);
    let nextSec = null;
    if (curIdx >= 0 && curIdx < secs.length - 1) {
      nextSec = secs[curIdx + 1];
    } else if (secs.length > 0) {
      nextSec = secs[0];
    }

    if (nextSec) {
      activePaperSecKey.value = nextSec.id || nextSec.name;
      triggerSoundAlert('lap', `${curSecName}完成，用时${curElapsedStr}。已切入${nextSec.name}。`);
    } else {
      triggerSoundAlert('lap', `${curSecName}完成，用时${curElapsedStr}。`);
    }
  }

  // 纸质做题完成：停表并准备拍照批改
  function finishPaperExam() {
    pauseMockExam();
    examTimerStatus.value = 'finished';
    if (examTimeElapsed.value > 0) {
      timeStr.value = formatSecondsToChinese(examTimeElapsed.value);
    }
    triggerSoundAlert('finish', '全卷作答完成，请对准纸质答题卡进行拍照批改。');
  }

  // 手工补录各模块纸质用时
  function applyManualSectionTimes(minMap = {}) {
    let sumSec = 0;
    Object.keys(minMap).forEach(k => {
      const mins = parseFloat(minMap[k]) || 0;
      const s = Math.round(mins * 60);
      sectionTimes.value[k] = s;
      sumSec += s;
    });
    if (sumSec > 0) {
      examTimeElapsed.value = sumSec;
      timeStr.value = formatSecondsToChinese(sumSec);
    }
  }

  function recordQuestionFocus(qNum) {
    if (qNum) {
      activeTrackingQ.value = parseInt(qNum, 10);
    }
  }
  async function fetchServerPresets() {
    try {
      const res = await getOmrPresets();
      if (res.presets) {
        presets.value = res.presets;
        selectPreset(currentPresetId.value);
      }
    } catch (e) {}
  }

  function selectPreset(presetId) {
    currentPresetId.value = presetId;
    const pData = presets.value[presetId] || FALLBACK_PRESETS[presetId] || FALLBACK_PRESETS.guokao_135;
    currentSections.value = JSON.parse(JSON.stringify(pData.sections));
  }

  function adaptSectionsToAnswerCount(maxQ) {
    if (!maxQ || maxQ <= 0) return;
    const count = parseInt(maxQ, 10);
    const newPreset = {
      name: `自适应模考 (${count}题 / ${count}分)`,
      total_questions: count,
      full_score: Number(count.toFixed(2)),
      sections: [
        { id: "practice", name: "微模考卷", start_q: 1, end_q: count, score_per_q: 1.0 }
      ]
    };
    presets.value.custom_adaptive = newPreset;
    currentPresetId.value = 'custom_adaptive';
    currentSections.value = JSON.parse(JSON.stringify(newPreset.sections));
  }

  function setOnlineAnswer(qNum, choice) {
    if (!choice) {
      delete onlineAnswers.value[qNum];
    } else {
      onlineAnswers.value[qNum] = String(choice).trim().toUpperCase();
    }
    recordQuestionFocus(qNum);
    // 若尚未启动模考，在填涂第 1 题时若处于模考状态，自动启动或恢复计时
    if (isMockExamActive.value && examTimerStatus.value === 'idle') {
      resumeMockExam();
    }
  }

  function setCorrectionAnswer(qNum, newOpt) {
    const cur = workingStudentAnswers.value[qNum] || null;
    if (cur === newOpt) {
      workingStudentAnswers.value[qNum] = null;
    } else {
      workingStudentAnswers.value[qNum] = newOpt;
    }
  }

  function resetCorrections() {
    workingStudentAnswers.value = { ...originalStudentAnswers.value };
  }

  async function submitGradeFromUpload(file) {
    if (!file) return;
    if (!configStore.isConfigured) {
      modalStore.openSettings();
      throw new Error('请先在右上角【设置】中配置个人 Base URL 与 API Key (BYOK)！');
    }
    if (!answerKey.value.trim()) {
      throw new Error('请先输入或录入该场考试的标准参考答案！');
    }

    isLoading.value = true;
    loadingTitle.value = '正在智能优化答题卡并极速上传...';
    loadingSubtitle.value = '正在压缩图片并建立高保真识别信道';

    try {
      const uploadFile = await compressImage(file, 2000, 0.85);

      loadingTitle.value = '正在智能批改行测答题卡...';
      loadingSubtitle.value = '正在识别填涂卡点位并分模块核算分值';

      const fd = new FormData();
      fd.append('file', uploadFile);
      fd.append('answer_key', answerKey.value.trim());
      fd.append('preset_id', currentPresetId.value);
      fd.append('sections_json', JSON.stringify(currentSections.value));
      fd.append('time_str', timeStr.value || '110分00秒');

      // 自动封存并携带纸质模考或手动录入的 timing 节奏数据
      if (examTimerStatus.value === 'running') {
        pauseMockExam();
      }
      if (examTimeElapsed.value > 0) {
        timeStr.value = formatSecondsToChinese(examTimeElapsed.value);
      }
      const timeData = {
        is_mock_exam: isMockExamActive.value || Boolean(examTimeElapsed.value > 0),
        total_elapsed_seconds: examTimeElapsed.value,
        question_times: questionTimes.value,
        section_times: sectionTimes.value
      };
      fd.append('time_data_json', JSON.stringify(timeData));

      const pData = presets.value[currentPresetId.value] || FALLBACK_PRESETS[currentPresetId.value];
      fd.append('exam_title', pData.name || '行测答题卡诊断');
      configStore.appendApiCredentials(fd);

      const data = await gradeOmr(fd);
      initResultData(data);
      return data;
    } finally {
      isLoading.value = false;
    }
  }

  async function submitGradeFromOnline() {
    if (!answerKey.value.trim()) {
      throw new Error('请先输入或点击【一键填入范例答案】录入参考标准答案！');
    }
    const answered = answeredOnlineCount.value;
    if (answered === 0) {
      throw new Error('您尚未在答题卡填涂任何选项！请先点击选项字母填涂后再交卷。');
    }

    // 暂停并封存模考计时
    if (examTimerStatus.value === 'running') {
      pauseMockExam();
    }
    if (examTimeElapsed.value > 0) {
      timeStr.value = formatSecondsToChinese(examTimeElapsed.value);
    }

    isLoading.value = true;
    loadingTitle.value = '正在提交在线答卷并智能判分...';
    loadingSubtitle.value = '正在核算四象限做题节奏与性价比诊断';

    try {
      const fd = new FormData();
      if (rawTaskId.value) fd.append('raw_task_id', rawTaskId.value);
      fd.append('student_answers_json', JSON.stringify(onlineAnswers.value));
      fd.append('answer_key', answerKey.value.trim());
      fd.append('preset_id', currentPresetId.value);
      fd.append('sections_json', JSON.stringify(currentSections.value));
      fd.append('time_str', timeStr.value || '110分00秒');

      const timeData = {
        is_mock_exam: isMockExamActive.value,
        total_elapsed_seconds: examTimeElapsed.value,
        question_times: questionTimes.value,
        section_times: sectionTimes.value
      };
      fd.append('time_data_json', JSON.stringify(timeData));

      const pData = presets.value[currentPresetId.value] || FALLBACK_PRESETS[currentPresetId.value];
      fd.append('exam_title', pData.name || '行测在线模考答题卡');
      configStore.appendApiCredentials(fd);

      const data = await gradeOmr(fd);
      initResultData(data);
      return data;
    } finally {
      isLoading.value = false;
    }
  }

  async function recognizeOnly(file) {
    if (!file) return;
    if (!configStore.isConfigured) {
      modalStore.openSettings();
      throw new Error('请先在右上角【设置】中配置个人 Base URL 与 API Key (BYOK)！');
    }

    isLoading.value = true;
    loadingTitle.value = '正在识别答题卡填涂选项...';
    loadingSubtitle.value = '正在多模态视觉提取填涂 ABCD 标记';

    try {
      const uploadFile = await compressImage(file, 2000, 0.85);
      const fd = new FormData();
      fd.append('file', uploadFile);
      fd.append('preset_id', currentPresetId.value);
      fd.append('sections_json', JSON.stringify(currentSections.value));
      configStore.appendApiCredentials(fd);

      const res = await recognizeOmrOnly(fd);
      rawTaskId.value = res.raw_task_id || '';
      onlineAnswers.value = {};
      const identified = res.student_answers || {};
      Object.keys(identified).forEach(k => {
        const opt = identified[k];
        if (opt && opt !== 'null' && opt !== 'multiple') {
          onlineAnswers.value[parseInt(k)] = opt;
        }
      });
      activeSubMode.value = 'online';
      onlineViewMode.value = 'sheet';
      return res;
    } finally {
      isLoading.value = false;
    }
  }

  async function applyCorrectionAndRegrade() {
    if (correctionDiffKeys.value.length === 0) {
      throw new Error('当前没有需要纠偏的修改项。');
    }
    if (!answerKey.value.trim()) {
      throw new Error('请确认已输入标准答案。');
    }

    const fd = new FormData();
    if (rawTaskId.value) fd.append('raw_task_id', rawTaskId.value);
    fd.append('student_answers_json', JSON.stringify(workingStudentAnswers.value));
    fd.append('answer_key', answerKey.value.trim());
    fd.append('preset_id', currentPresetId.value);
    fd.append('sections_json', JSON.stringify(currentSections.value));
    fd.append('time_str', timeStr.value || '110分00秒');

    const pData = presets.value[currentPresetId.value] || FALLBACK_PRESETS[currentPresetId.value];
    fd.append('exam_title', pData.name || '行测答题卡诊断');
    configStore.appendApiCredentials(fd);

    const data = await gradeOmr(fd);
    initResultData(data);
    return data;
  }

  function initResultData(data) {
    resultData.value = data;
    rawTaskId.value = data.raw_task_id || data.task_id || '';
    currentResultTab.value = 'diag';
    isMatrixExpanded.value = true;

    // 初始化纠偏数据
    originalStudentAnswers.value = {};
    workingStudentAnswers.value = {};

    if (data.student_answers && Object.keys(data.student_answers).length > 0) {
      Object.keys(data.student_answers).forEach(k => {
        const qNum = parseInt(k);
        const v = data.student_answers[k];
        const cleanV = (v && String(v).trim().toUpperCase() !== 'NULL') ? String(v).trim().toUpperCase() : null;
        originalStudentAnswers.value[qNum] = cleanV;
        workingStudentAnswers.value[qNum] = cleanV;
      });
    } else if (data.items) {
      data.items.forEach(it => {
        const qNum = it.q_num;
        const v = it.student_choice;
        const cleanV = (v && v !== 'null' && v !== 'multiple') ? v : (v === 'multiple' ? 'multiple' : null);
        originalStudentAnswers.value[qNum] = cleanV;
        workingStudentAnswers.value[qNum] = cleanV;
      });
    }
  }

  function reset() {
    resultData.value = null;
    rawTaskId.value = '';
    originalStudentAnswers.value = {};
    workingStudentAnswers.value = {};
    resetMockExam();
  }

  return {
    presets,
    currentPresetId,
    currentSections,
    isSectionDrawerOpen,
    answerKey,
    timeStr,
    activeSubMode,
    onlineViewMode,
    onlineAnswers,
    isMockExamActive,
    examDurationMinutes,
    examTimeRemaining,
    examTimeElapsed,
    examTimerStatus,
    questionTimes,
    sectionTimes,
    activeTrackingQ,
    paperTimerMode,
    activePaperSecKey,
    isScreenWakeLocked,
    soundAlertMode,
    isManualTimeOpen,
    manualSectionMinutes,
    isFullscreenPaperTimer,
    effectiveActivePaperSec,
    effectivePaperSecKey,
    activePaperBenchmark,
    activePaperSecElapsed,
    activePaperTargetSeconds,
    activePaperProgressPct,
    activePaperIsOvertime,
    formattedTimeRemaining,
    formattedTimeElapsed,
    averagePaceSeconds,
    isTimeCritical,
    isTimeWarning,
    startMockExam,
    pauseMockExam,
    resumeMockExam,
    resetMockExam,
    switchPaperSection,
    lapPaperSection,
    finishPaperExam,
    applyManualSectionTimes,
    requestScreenWakeLock,
    releaseScreenWakeLock,
    triggerSoundAlert,
    recordQuestionFocus,
    isLoading,
    loadingTitle,
    loadingSubtitle,
    resultData,
    currentResultTab,
    isMatrixExpanded,
    rawTaskId,
    originalStudentAnswers,
    workingStudentAnswers,
    verifyFilter,
    totalQuestions,
    fullScore,
    answeredOnlineCount,
    correctionDiffKeys,
    fetchServerPresets,
    selectPreset,
    adaptSectionsToAnswerCount,
    setOnlineAnswer,
    setCorrectionAnswer,
    resetCorrections,
    submitGradeFromUpload,
    submitGradeFromOnline,
    recognizeOnly,
    applyCorrectionAndRegrade,
    initResultData,
    reset
  };
});
