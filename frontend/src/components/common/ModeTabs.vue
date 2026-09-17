<template>
  <div class="flex bg-slate-200/80 p-1 rounded-xl text-xs font-semibold mb-3 shadow-2xs">
    <button
      type="button"
      @click="emit('switch-mode', 'math')"
      :class="currentMode === 'math'
        ? 'flex-1 py-2 rounded-lg bg-white shadow-xs text-slate-900 transition flex items-center justify-center space-x-1.5 cursor-pointer'
        : 'flex-1 py-2 rounded-lg text-slate-500 hover:text-slate-800 transition flex items-center justify-center space-x-1.5 cursor-pointer'"
    >
      <i class="fa-solid fa-calculator text-emerald-600"></i>
      <span>速算练习册</span>
    </button>

    <button
      type="button"
      @click="emit('switch-mode', 'omr')"
      :class="currentMode === 'omr'
        ? 'flex-1 py-2 rounded-lg bg-white shadow-xs text-slate-900 transition flex items-center justify-center space-x-1.5 cursor-pointer'
        : 'flex-1 py-2 rounded-lg text-slate-500 hover:text-slate-800 transition flex items-center justify-center space-x-1.5 cursor-pointer'"
    >
      <i class="fa-solid fa-table-cells-large text-blue-600"></i>
      <span>行测答题卡</span>
    </button>

    <button
      type="button"
      @click="emit('switch-mode', 'wrongbook')"
      :class="currentMode === 'wrongbook'
        ? 'flex-1 py-2 rounded-lg bg-white shadow-xs text-purple-900 transition flex items-center justify-center space-x-1.5 cursor-pointer relative font-bold'
        : 'flex-1 py-2 rounded-lg text-slate-500 hover:text-slate-800 transition flex items-center justify-center space-x-1.5 cursor-pointer relative'"
    >
      <i class="fa-solid fa-brain text-purple-600"></i>
      <span>错题库 (艾宾浩斯)</span>
      <!-- 待复习红点角标 -->
      <span
        v-if="wrongBookStore.todayDueCount > 0"
        class="ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-black bg-rose-500 text-white animate-pulse"
      >
        {{ wrongBookStore.todayDueCount }}
      </span>
    </button>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useWrongBookStore } from '../../stores/wrongbook';

defineProps({
  currentMode: {
    type: String,
    default: 'math'
  }
});

const emit = defineEmits(['switch-mode']);
const wrongBookStore = useWrongBookStore();

onMounted(() => {
  wrongBookStore.fetchStats();
});
</script>
