import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { getOmrPresets, parseAnswerImage, recognizeOmrOnly, gradeOmr } from '../api/omr';
import { getHistoryDetail } from '../api/history';
import { useConfigStore } from './config';
import { useModalStore } from './modal';
import { compressImage } from '../utils/imageCompressor';

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

  // 动作
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

  function setOnlineAnswer(qNum, choice) {
    if (!choice) {
      delete onlineAnswers.value[qNum];
    } else {
      onlineAnswers.value[qNum] = String(choice).trim().toUpperCase();
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

    isLoading.value = true;
    loadingTitle.value = '正在提交在线答卷并智能判分...';
    loadingSubtitle.value = '正在分模块核算得分率并生成全景答题卡';

    try {
      const fd = new FormData();
      if (rawTaskId.value) fd.append('raw_task_id', rawTaskId.value);
      fd.append('student_answers_json', JSON.stringify(onlineAnswers.value));
      fd.append('answer_key', answerKey.value.trim());
      fd.append('preset_id', currentPresetId.value);
      fd.append('sections_json', JSON.stringify(currentSections.value));
      fd.append('time_str', timeStr.value || '110分00秒');

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

  async function restoreTask(taskId) {
    if (!taskId) return;
    const res = await getHistoryDetail(taskId);
    const data = res.data;
    if (data && !data.task_id) {
      data.task_id = taskId;
    }
    if (!data.card_url) data.card_url = `/output/${taskId}_card.jpg`;
    initResultData(data);
    return data;
  }

  function reset() {
    resultData.value = null;
    rawTaskId.value = '';
    originalStudentAnswers.value = {};
    workingStudentAnswers.value = {};
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
    setOnlineAnswer,
    setCorrectionAnswer,
    resetCorrections,
    submitGradeFromUpload,
    submitGradeFromOnline,
    recognizeOnly,
    applyCorrectionAndRegrade,
    initResultData,
    restoreTask,
    reset
  };
});
