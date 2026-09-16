import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { getHistoryList, deleteHistoryItem } from '../api/history';

export const useHistoryStore = defineStore('history', () => {
  const records = ref([]);
  const filterType = ref('all'); // 'all' | 'omr' | 'math'
  const isLoading = ref(false);
  const errorMsg = ref('');

  const filteredRecords = computed(() => {
    if (filterType.value === 'all') return records.value;
    return records.value.filter(r => r.type === filterType.value);
  });

  async function fetchList() {
    isLoading.value = true;
    errorMsg.value = '';
    try {
      const res = await getHistoryList('all', 100);
      records.value = res.records || [];
    } catch (err) {
      errorMsg.value = err.message || '读取历史记录失败';
    } finally {
      isLoading.value = false;
    }
  }

  async function deleteRecord(taskId) {
    await deleteHistoryItem(taskId);
    records.value = records.value.filter(r => r.task_id !== taskId);
  }

  return {
    records,
    filterType,
    isLoading,
    errorMsg,
    filteredRecords,
    fetchList,
    deleteRecord
  };
});
