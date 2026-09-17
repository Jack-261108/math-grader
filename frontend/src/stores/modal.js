import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useModalStore = defineStore('modal', () => {
  // Settings Modal
  const isSettingsOpen = ref(false);
  function openSettings() { isSettingsOpen.value = true; }
  function closeSettings() { isSettingsOpen.value = false; }

  // History Modal
  const isHistoryOpen = ref(false);
  function openHistory() { isHistoryOpen.value = true; }
  function closeHistory() { isHistoryOpen.value = false; }

  // AI Tutor Modal
  const isAiTutorOpen = ref(false);
  const aiTutorContext = ref(null); // { type: 'math' | 'omr', questionData: {...} }
  function openAiTutor(type, questionData) {
    aiTutorContext.value = { type, questionData };
    isAiTutorOpen.value = true;
  }
  function closeAiTutor() {
    isAiTutorOpen.value = false;
    aiTutorContext.value = null;
  }

  // Question Modal (原题反向呈现)
  const isQuestionModalOpen = ref(false);
  const currentQuestionNum = ref(1);
  function openQuestion(qNum) {
    currentQuestionNum.value = qNum;
    isQuestionModalOpen.value = true;
  }
  function closeQuestion() {
    isQuestionModalOpen.value = false;
  }

  // Fullscreen Viewer Modal
  const isFullscreenOpen = ref(false);
  const fullscreenImageUrl = ref('');
  function openFullscreen(url) {
    if (!url) return;
    fullscreenImageUrl.value = url;
    isFullscreenOpen.value = true;
  }
  function closeFullscreen() {
    isFullscreenOpen.value = false;
    fullscreenImageUrl.value = '';
  }

  // Print Modal
  const isPrintModalOpen = ref(false);
  const printSource = ref('math'); // 'math' | 'omr'
  function openPrint(source = 'math') {
    printSource.value = source;
    isPrintModalOpen.value = true;
  }
  function closePrint() {
    isPrintModalOpen.value = false;
  }

  // Targeted Practice Modal (速算靶向自适应强化练)
  const isTargetedPracticeOpen = ref(false);
  const targetedPracticeMeta = ref({ weaknessType: 'borrow_error', weaknessName: '' });
  function openTargetedPractice(weaknessType = 'borrow_error', weaknessName = '') {
    targetedPracticeMeta.value = { weaknessType, weaknessName };
    isTargetedPracticeOpen.value = true;
  }
  function closeTargetedPractice() {
    isTargetedPracticeOpen.value = false;
  }

  return {
    isSettingsOpen,
    openSettings,
    closeSettings,
    isHistoryOpen,
    openHistory,
    closeHistory,
    isAiTutorOpen,
    aiTutorContext,
    openAiTutor,
    closeAiTutor,
    isQuestionModalOpen,
    currentQuestionNum,
    openQuestion,
    closeQuestion,
    isFullscreenOpen,
    fullscreenImageUrl,
    openFullscreen,
    closeFullscreen,
    isPrintModalOpen,
    printSource,
    openPrint,
    closePrint,
    isTargetedPracticeOpen,
    targetedPracticeMeta,
    openTargetedPractice,
    closeTargetedPractice
  };
});
