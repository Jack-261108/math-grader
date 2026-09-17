import { apiRequest } from './client';

/**
 * 获取错题库宏观统计与艾宾浩斯待复习指标
 */
export async function getWrongBookStats() {
  return apiRequest('/api/wrong-book/stats');
}

/**
 * 多维检索错题列表
 */
export async function getWrongQuestions(params = {}) {
  const query = new URLSearchParams();
  if (params.source_type) query.append('source_type', params.source_type);
  if (params.status) query.append('status', params.status);
  if (params.topic) query.append('topic', params.topic);
  if (params.error_tag) query.append('error_tag', params.error_tag);
  if (params.only_due) query.append('only_due', 'true');
  if (params.keyword) query.append('keyword', params.keyword);
  if (params.limit) query.append('limit', String(params.limit));
  if (params.offset) query.append('offset', String(params.offset));

  const qs = query.toString();
  return apiRequest(`/api/wrong-book/questions${qs ? '?' + qs : ''}`);
}

/**
 * 记录一次艾宾浩斯复习作答结果
 */
export async function recordReview(questionId, isCorrect, userInput = '') {
  const fd = new FormData();
  fd.append('question_id', String(questionId));
  fd.append('is_correct', String(isCorrect));
  if (userInput) fd.append('user_input', userInput);
  return apiRequest('/api/wrong-book/review', {
    method: 'POST',
    body: fd
  });
}

/**
 * 更新错因标签或复盘笔记
 */
export async function updateWrongQuestionTag(questionId, errorTag, userNotes = null) {
  const fd = new FormData();
  fd.append('question_id', String(questionId));
  if (errorTag) fd.append('error_tag', errorTag);
  if (userNotes !== null && userNotes !== undefined) fd.append('user_notes', userNotes);
  return apiRequest('/api/wrong-book/update-tag', {
    method: 'POST',
    body: fd
  });
}

/**
 * 一键生成针对性薄弱考点自测提分卷
 */
export async function generateWeaknessSheet({ topicList, sourceType = 'all', onlyDue = false, recentDays = null, count = 15 }) {
  const fd = new FormData();
  if (topicList && topicList.length > 0) {
    fd.append('topic_list_json', JSON.stringify(topicList));
  }
  fd.append('source_type', sourceType);
  fd.append('only_due', String(onlyDue));
  if (recentDays) fd.append('recent_days', String(recentDays));
  fd.append('count', String(count));

  return apiRequest('/api/wrong-book/generate-sheet', {
    method: 'POST',
    body: fd
  });
}

/**
 * 一键从存量历史批改报告中同步错题
 */
export async function syncHistoryToWrongBook() {
  return apiRequest('/api/wrong-book/sync-history', {
    method: 'POST'
  });
}
