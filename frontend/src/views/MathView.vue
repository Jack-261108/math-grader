<template>
  <div class="space-y-4">
    <!-- 等待中 Loading 状态 -->
    <section v-if="mathStore.isLoading" class="space-y-4 py-8 text-center">
      <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
        <div class="relative w-20 h-20 mx-auto">
          <div class="w-20 h-20 rounded-full border-4 border-emerald-100 border-t-emerald-600 animate-spin"></div>
          <div class="absolute inset-0 flex items-center justify-center text-emerald-600">
            <i class="fa-solid fa-wand-magic-sparkles text-2xl animate-pulse"></i>
          </div>
        </div>

        <div>
          <h3 class="font-bold text-slate-800 text-base mb-1">正在智能识别并批改练习册...</h3>
          <p class="text-xs text-slate-500">透视矫正 · 笔迹提取 · 数学规则核验</p>
        </div>

        <StepProgress :current-step="mathStore.loadingStep" />
      </div>
    </section>

    <!-- 结果页 -->
    <MathResult v-else-if="mathStore.resultData" />

    <!-- 初始上传页 -->
    <MathUpload v-else />
  </div>
</template>

<script setup>
import { useMathStore } from '../stores/math';
import StepProgress from '../components/common/StepProgress.vue';
import MathUpload from '../components/math/MathUpload.vue';
import MathResult from '../components/math/MathResult.vue';

const mathStore = useMathStore();
</script>
