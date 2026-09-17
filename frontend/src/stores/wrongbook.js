import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import {
  getWrongBookStats,
  getWrongQuestions,
  recordReview,
  updateWrongQuestionTag,
  generateWeaknessSheet,
  syncHistoryToWrongBook
} from '../api/wrongbook';

export const useWrongBookStore = defineStore('wrongbook', () => {
  const activeTab = ref('ebbinghaus'); // 'ebbinghaus' | 'all' | 'sheet'
  const isLoading = ref(false);
  const isSyncing = ref(false);
  const errorMsg = ref('');

  // 统计数据
  const stats = ref({
    total_count: 0,
    today_due_count: 0,
    mastered_count: 0,
    learning_count: 0,
    module_dist: [],
    topic_ranking: [],
    tag_dist: {},
    today_str: ''
  });

  // 列表筛选条件
  const filterSourceType = ref('all'); // 'all' | 'omr' | 'math'
  const filterStatus = ref('all'); // 'all' | 'reviewing' | 'mastered'
  const filterTopic = ref('all');
  const filterErrorTag = ref('all');
  const searchKeyword = ref('');

  // 错题数据集
  const questions = ref([]);
  const dueQuestions = ref([]);
  const totalQuestions = ref(0);

  // 针对性组卷状态
  const generatedSheet = ref(null);
  const isSheetLoading = ref(false);
  const selectedTopicsForSheet = ref([]);
  const customSheetCount = ref(15);
  const practiceSourceType = ref('all');

  // 在线自测做题状态
  const isPracticing = ref(false);
  const practiceIndex = ref(0);
  const practiceUserAnswers = ref({}); // { [qId]: answer }
  const practiceRevealed = ref({}); // { [qId]: boolean }

  const todayDueCount = computed(() => stats.value.today_due_count || 0);

  async function fetchStats() {
    try {
      const res = await getWrongBookStats();
      stats.value = res;
    } catch (e) {
      console.error('获取错题库统计失败', e);
    }
  }

  async function fetchQuestions() {
    isLoading.value = true;
    errorMsg.value = '';
    try {
      const res = await getWrongQuestions({
        source_type: filterSourceType.value,
        status: filterStatus.value,
        topic: filterTopic.value,
        error_tag: filterErrorTag.value,
        keyword: searchKeyword.value,
        limit: 100
      });
      questions.value = res.questions || [];
      totalQuestions.value = res.total || 0;
    } catch (err) {
      errorMsg.value = err.message || '加载错题失败';
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchDueQuestions() {
    isLoading.value = true;
    try {
      const res = await getWrongQuestions({
        only_due: true,
        limit: 100
      });
      dueQuestions.value = res.questions || [];
    } catch (e) {
      console.error('加载待复习错题失败', e);
    } finally {
      isLoading.value = false;
    }
  }

  async function submitReviewResult(questionId, isCorrect, userInput = '') {
    try {
      const res = await recordReview(questionId, isCorrect, userInput);
      // 局部更新列表状态
      const q = questions.value.find(item => item.id === questionId);
      if (q && res.result) {
        q.review_stage = res.result.new_stage;
        q.mastery_streak = res.result.mastery_streak;
        q.status = res.result.status;
        q.next_review_at = res.result.next_review_at;
        q.is_due = false;
      }
      // 同步待复习列表
      dueQuestions.value = dueQuestions.value.filter(item => item.id !== questionId);
      await fetchStats();
      return res.result;
    } catch (e) {
      alert(e.message || '记录复习结果失败');
      throw e;
    }
  }

  async function updateTagAndNotes(questionId, errorTag, userNotes) {
    try {
      await updateWrongQuestionTag(questionId, errorTag, userNotes);
      const q = questions.value.find(item => item.id === questionId);
      if (q) {
        if (errorTag) q.error_tag = errorTag;
        if (userNotes !== null && userNotes !== undefined) q.user_notes = userNotes;
      }
    } catch (e) {
      alert(e.message || '更新标签失败');
    }
  }

  async function generateCustomSheet({ onlyDue = false, recentDays = null, count = 15 }) {
    isSheetLoading.value = true;
    try {
      const res = await generateWeaknessSheet({
        topicList: selectedTopicsForSheet.value,
        sourceType: practiceSourceType.value,
        onlyDue,
        recentDays,
        count
      });
      generatedSheet.value = res.sheet;
      practiceIndex.value = 0;
      practiceUserAnswers.value = {};
      practiceRevealed.value = {};
      return res.sheet;
    } catch (e) {
      alert(e.message || '组装专项卷失败');
      throw e;
    } finally {
      isSheetLoading.value = false;
    }
  }

  async function syncHistory() {
    isSyncing.value = true;
    try {
      const res = await syncHistoryToWrongBook();
      await fetchStats();
      await fetchQuestions();
      await fetchDueQuestions();
      alert(`🎉 成功从历史批改中同步录入 ${res.imported_count || 0} 道错题！`);
    } catch (e) {
      alert(e.message || '同步历史失败');
    } finally {
      isSyncing.value = false;
    }
  }

  return {
    activeTab,
    isLoading,
    isSyncing,
    errorMsg,
    stats,
    todayDueCount,
    filterSourceType,
    filterStatus,
    filterTopic,
    filterErrorTag,
    searchKeyword,
    questions,
    dueQuestions,
    totalQuestions,
    generatedSheet,
    isSheetLoading,
    selectedTopicsForSheet,
    customSheetCount,
    practiceSourceType,
    isPracticing,
    practiceIndex,
    practiceUserAnswers,
    practiceRevealed,
    fetchStats,
    fetchQuestions,
    fetchDueQuestions,
    submitReviewResult,
    updateTagAndNotes,
    generateCustomSheet,
    syncHistory
  };
});
