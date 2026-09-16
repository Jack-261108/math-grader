<template>
  <section v-if="mathStore.resultData" class="space-y-4">
    <!-- 成绩概览大卡片 -->
    <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm relative overflow-hidden">
      <div class="flex items-start justify-between">
        <div>
          <div class="text-[11px] text-emerald-600 uppercase tracking-wider font-semibold">速算实战批改</div>
          <h2 class="text-xl font-bold text-slate-900 mt-0.5">{{ mathStore.resultData.title || '速算技巧练习' }}</h2>
          <p class="text-xs text-slate-500 mt-0.5">用时: {{ mathStore.resultData.summary?.time_str || '23分18秒' }}</p>
        </div>
        <!-- 评级印章 -->
        <div class="stamp-badge px-3 py-1 text-center font-serif font-black">
          <div class="text-[9px] tracking-widest uppercase">评级</div>
          <div class="text-2xl leading-none">{{ mathStore.resultData.summary?.grade_level || 'A+' }}</div>
        </div>
      </div>

      <!-- 数据指标 -->
      <div class="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate-100 text-center">
        <div class="bg-slate-50 rounded-xl p-2.5">
          <div class="text-[10px] text-slate-400">总题数</div>
          <div class="text-base font-bold text-slate-800 mt-0.5">{{ mathStore.resultData.summary?.total || 0 }}</div>
        </div>
        <div class="bg-emerald-50 rounded-xl p-2.5">
          <div class="text-[10px] text-emerald-600">正确率</div>
          <div class="text-base font-bold text-emerald-600 mt-0.5">{{ mathStore.resultData.summary?.accuracy_pct || 0 }}%</div>
        </div>
        <div class="bg-rose-50 rounded-xl p-2.5">
          <div class="text-[10px] text-rose-600">错题数</div>
          <div class="text-base font-bold text-rose-600 mt-0.5">{{ mathStore.resultData.summary?.wrong || 0 }}</div>
        </div>
      </div>
    </div>

    <!-- 标注图片展示区域 -->
    <div class="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-3">
      <div class="flex items-center justify-between">
        <!-- 切换 Tab: 扫视矫正图 vs 原拍摄图 -->
        <div class="flex bg-slate-100 p-0.5 rounded-xl text-xs font-semibold">
          <button
            type="button"
            @click="mathStore.activeImageTab = 'scan'"
            :class="mathStore.activeImageTab === 'scan' ? 'flex-1 py-1.5 px-3 rounded-lg bg-white shadow-xs text-slate-800 transition font-bold' : 'flex-1 py-1.5 px-3 rounded-lg text-slate-500 hover:text-slate-800 transition'"
          >
            正射纠偏图
          </button>
          <button
            type="button"
            @click="mathStore.activeImageTab = 'orig'"
            :class="mathStore.activeImageTab === 'orig' ? 'flex-1 py-1.5 px-3 rounded-lg bg-white shadow-xs text-slate-800 transition font-bold' : 'flex-1 py-1.5 px-3 rounded-lg text-slate-500 hover:text-slate-800 transition'"
          >
            原卷批改图
          </button>
        </div>
        <a
          :href="currentImageUrl"
          download="批改原图.jpg"
          class="text-emerald-600 hover:text-emerald-700 text-xs font-semibold flex items-center bg-emerald-50 hover:bg-emerald-100 px-2.5 py-1 rounded-lg transition"
        >
          <i class="fa-solid fa-download mr-1 text-[11px]"></i> 保存图片
        </a>
      </div>

      <!-- 图片视口 -->
      <div
        class="rounded-xl overflow-hidden bg-slate-900 border border-slate-200 cursor-zoom-in relative group max-h-[70vh] flex items-center justify-center"
        @click="modalStore.openFullscreen(currentImageUrl)"
      >
        <img
          :src="currentImageUrl"
          alt="批改结果图"
          class="w-full h-auto max-h-[70vh] object-contain"
        >
        <div class="absolute bottom-2 right-2 px-2.5 py-1 bg-black/70 backdrop-blur-sm text-white text-[11px] rounded-lg pointer-events-none flex items-center space-x-1.5">
          <i class="fa-solid fa-magnifying-glass-plus"></i>
          <span>点击全屏查看批注细节 (支持双指缩放)</span>
        </div>
      </div>
    </div>

    <!-- 智能学情画像 -->
    <MathDiagnosis :diagnosis="mathStore.resultData.diagnosis" />

    <!-- 错题复盘列表 -->
    <MathWrongList :wrong-items="mathStore.resultData.wrong_items" />

    <!-- A4 错题本导出横幅 -->
    <div class="bg-gradient-to-r from-emerald-600 to-teal-700 rounded-2xl p-4 text-white shadow-sm flex items-center justify-between">
      <div class="min-w-0 pr-2">
        <div class="font-bold text-sm">🖨️ A4 错题本与自测重刷卷导出</div>
        <p class="text-xs text-emerald-100 mt-0.5">一键生成标准 A4 错题重做卷，支持随时打印或导出 PDF</p>
      </div>
      <button
        type="button"
        @click="modalStore.openPrint('math')"
        class="px-4 py-2 bg-white text-emerald-800 hover:bg-emerald-50 active:scale-95 font-bold text-xs rounded-xl shadow-sm transition shrink-0 cursor-pointer flex items-center space-x-1"
      >
        <span>生成自测卷</span>
        <i class="fa-solid fa-arrow-right"></i>
      </button>
    </div>

    <!-- 再测一张按钮 -->
    <div class="pt-2">
      <button
        type="button"
        @click="handleRetry"
        class="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-3 px-4 rounded-xl shadow-sm transition flex items-center justify-center space-x-2 text-sm cursor-pointer"
      >
        <i class="fa-solid fa-camera-rotate"></i>
        <span>再测一张</span>
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import { useMathStore } from '../../stores/math';
import { useModalStore } from '../../stores/modal';
import { useRouter } from 'vue-router';
import MathDiagnosis from './MathDiagnosis.vue';
import MathWrongList from './MathWrongList.vue';

const mathStore = useMathStore();
const modalStore = useModalStore();
const router = useRouter();

const currentImageUrl = computed(() => {
  if (mathStore.activeImageTab === 'orig') {
    return mathStore.resultData?.orig_url || '';
  }
  return mathStore.resultData?.scan_url || '';
});

function handleRetry() {
  mathStore.reset();
  router.replace({ path: '/', query: { mode: 'math' } });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
</script>
