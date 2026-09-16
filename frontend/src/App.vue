<template>
  <div class="min-h-screen text-slate-800 flex flex-col justify-between">
    <!-- 顶部导航栏 -->
    <Header />

    <!-- 主交互区域 -->
    <main class="max-w-md md:max-w-3xl lg:max-w-4xl w-full mx-auto px-3 sm:px-6 py-3 flex-1 min-w-0 overflow-x-hidden">
      <!-- 模式切换 Tab -->
      <ModeTabs :current-mode="currentMode" @switch-mode="handleSwitchMode" />

      <!-- 主视图渲染 -->
      <div v-show="currentMode === 'math'">
        <MathView />
      </div>
      <div v-show="currentMode === 'omr'">
        <OmrView />
      </div>
    </main>

    <!-- 底部返回顶部 -->
    <BackToTop />

    <!-- 6 个全局模态弹窗 -->
    <SettingsModal />
    <HistoryModal />
    <AiTutorModal />
    <QuestionModal />
    <FullscreenViewer />
    <PrintModal />
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Header from './components/common/Header.vue';
import ModeTabs from './components/common/ModeTabs.vue';
import BackToTop from './components/common/BackToTop.vue';
import MathView from './views/MathView.vue';
import OmrView from './views/OmrView.vue';

import SettingsModal from './components/modals/SettingsModal.vue';
import HistoryModal from './components/modals/HistoryModal.vue';
import AiTutorModal from './components/modals/AiTutorModal.vue';
import QuestionModal from './components/modals/QuestionModal.vue';
import FullscreenViewer from './components/modals/FullscreenViewer.vue';
import PrintModal from './components/modals/PrintModal.vue';

import { useMathStore } from './stores/math';
import { useOmrStore } from './stores/omr';
import { useModalStore } from './stores/modal';

const route = useRoute();
const router = useRouter();

const mathStore = useMathStore();
const omrStore = useOmrStore();
const modalStore = useModalStore();

const currentMode = ref('math');

function handleSwitchMode(mode) {
  currentMode.value = mode;

  // 路由与 URL 同步
  if (mode === 'omr') {
    if (omrStore.resultData?.task_id) {
      router.replace({ path: '/', query: { mode: 'omr', task_id: omrStore.resultData.task_id } });
    } else {
      router.replace({ path: '/', query: { mode: 'omr' } });
    }
  } else {
    if (mathStore.resultData?.task_id) {
      router.replace({ path: '/', query: { mode: 'math', task_id: mathStore.resultData.task_id } });
    } else {
      router.replace({ path: '/', query: { mode: 'math' } });
    }
  }
}

// 监听路由参数变化自动加载任务或切换模式
watch(
  () => route.query,
  async (query) => {
    const mode = query.mode;
    const taskId = query.task_id;

    if (mode === 'omr' || (taskId && String(taskId).startsWith('omr_'))) {
      currentMode.value = 'omr';
      if (taskId && (!omrStore.resultData || omrStore.resultData.task_id !== taskId)) {
        await omrStore.restoreTask(taskId);
      }
    } else if (mode === 'math' || taskId) {
      currentMode.value = 'math';
      if (taskId && (!mathStore.resultData || mathStore.resultData.task_id !== taskId)) {
        await mathStore.restoreTask(taskId);
      }
    } else if (mode === 'math') {
      currentMode.value = 'math';
    }

    if (query.settings !== undefined) {
      modalStore.openSettings();
    }
    if (query.history !== undefined) {
      modalStore.openHistory();
    }
    if (query.print_preview) {
      modalStore.openPrint(query.print_preview === 'omr' ? 'omr' : 'math');
    }
  },
  { immediate: true }
);

onMounted(() => {
  // 初次加载检查
  const urlParams = new URLSearchParams(window.location.search);
  const tId = urlParams.get('task_id');
  const m = urlParams.get('mode') || (tId && tId.startsWith('omr_') ? 'omr' : 'math');
  currentMode.value = m;
});
</script>
