<template>
  <div class="flex bg-slate-200/80 p-1 rounded-xl text-xs font-semibold mb-3">
    <button
      type="button"
      @click="emit('switch-mode', 'math')"
      :class="currentMode === 'math'
        ? 'flex-1 py-2 rounded-lg bg-white shadow-xs text-slate-900 transition flex items-center justify-center space-x-1.5'
        : 'flex-1 py-2 rounded-lg text-slate-500 hover:text-slate-800 transition flex items-center justify-center space-x-1.5'"
    >
      <i class="fa-solid fa-calculator text-emerald-600"></i>
      <span>速算练习册 (算术)</span>
    </button>
    <button
      type="button"
      @click="emit('switch-mode', 'omr')"
      :class="currentMode === 'omr'
        ? 'flex-1 py-2 rounded-lg bg-white shadow-xs text-slate-900 transition flex items-center justify-center space-x-1.5'
        : 'flex-1 py-2 rounded-lg text-slate-500 hover:text-slate-800 transition flex items-center justify-center space-x-1.5'"
    >
      <i class="fa-solid fa-table-cells-large text-blue-600"></i>
      <span>行测答题卡 (OMR)</span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  currentMode: {
    type: String,
    default: 'math'
  }
});

const emit = defineEmits(['switch-mode']);
</script>
