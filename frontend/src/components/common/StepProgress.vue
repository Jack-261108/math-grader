<template>
  <div class="bg-slate-50 rounded-xl p-3 text-left space-y-2 text-xs text-slate-600">
    <div
      v-for="(step, idx) in steps"
      :key="idx"
      :class="currentStep >= (idx + 1) ? 'flex items-center space-x-2 text-emerald-600 font-medium' : 'flex items-center space-x-2 text-slate-400'"
    >
      <i :class="currentStep >= (idx + 1) ? 'fa-solid fa-circle-check' : 'fa-regular fa-circle'"></i>
      <span>{{ step }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  currentStep: {
    type: Number,
    default: 1
  },
  steps: {
    type: Array,
    default: () => [
      '上传与文件预处理',
      '透视单应性变换与网格分割',
      '多模态视觉模型提取手写笔迹',
      '数学规则判题与高保真图层融合'
    ]
  }
});
</script>
