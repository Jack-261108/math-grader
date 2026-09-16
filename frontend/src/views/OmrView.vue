<template>
  <div class="space-y-4">
    <!-- 等待中 Loading 状态 -->
    <section v-if="omrStore.isLoading" class="space-y-4 py-8 text-center">
      <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
        <div class="relative w-20 h-20 mx-auto">
          <div class="w-20 h-20 rounded-full border-4 border-blue-100 border-t-blue-600 animate-spin"></div>
          <div class="absolute inset-0 flex items-center justify-center text-blue-600">
            <i class="fa-solid fa-wand-magic-sparkles text-2xl animate-pulse"></i>
          </div>
        </div>

        <div>
          <h3 class="font-bold text-slate-800 text-base mb-1">{{ omrStore.loadingTitle }}</h3>
          <p class="text-xs text-slate-500">{{ omrStore.loadingSubtitle }}</p>
        </div>

        <StepProgress
          :current-step="3"
          :steps="[
            '上传答题卡照片或在线作答',
            '提取 ABCD 填涂与手写选项',
            '行测五大模块分模块核算',
            '生成电子答题卡报告与学情诊断'
          ]"
        />
      </div>
    </section>

    <!-- 结果页 -->
    <OmrResult v-else-if="omrStore.resultData" />

    <!-- 初始上传/作答页 -->
    <OmrUpload v-else />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useOmrStore } from '../stores/omr';
import StepProgress from '../components/common/StepProgress.vue';
import OmrUpload from '../components/omr/OmrUpload.vue';
import OmrResult from '../components/omr/OmrResult.vue';

const omrStore = useOmrStore();

onMounted(() => {
  omrStore.fetchServerPresets();
});
</script>
