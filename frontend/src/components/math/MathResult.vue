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

    <!-- ⏱️ 速算做题配速与段位画像卡片 -->
    <div class="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-3">
      <div class="flex items-center justify-between border-b border-slate-100 pb-2">
        <div class="flex items-center space-x-1.5">
          <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
          <h3 class="font-bold text-xs text-slate-800">速算心算配速与段位画像</h3>
        </div>
        <span class="text-[11px] font-bold px-2 py-0.5 rounded-full border" :class="speedBadgeClass">
          {{ speedBadgeText }}
        </span>
      </div>

      <div class="grid grid-cols-2 gap-2 text-xs">
        <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200/70">
          <div class="text-[10px] text-slate-400">实测单题平均耗时</div>
          <div class="text-base font-bold text-slate-800 mt-0.5 font-mono">
            {{ secPerItem }} <span class="text-xs font-normal text-slate-500">秒/题</span>
          </div>
          <div class="text-[10px] text-slate-400 mt-0.5">全卷用时 {{ mathStore.resultData.summary?.time_str || '23分18秒' }}</div>
        </div>

        <div class="bg-emerald-50/60 p-2.5 rounded-xl border border-emerald-200/60">
          <div class="text-[10px] text-emerald-600 font-medium">行测实战标准标尺</div>
          <div class="text-base font-bold text-emerald-700 mt-0.5 font-mono">
            ≤ 15.0 <span class="text-xs font-normal text-emerald-600">秒/题</span>
          </div>
          <div class="text-[10px] text-emerald-600 mt-0.5">资料分析标准答题速度</div>
        </div>
      </div>

      <!-- 配速评价与建议 -->
      <div v-if="mathStore.resultData.diagnosis?.speed_advice" class="text-[11px] text-slate-600 bg-slate-50/80 p-2.5 rounded-xl border border-slate-200/70 leading-relaxed flex items-start space-x-1.5">
        <i class="fa-solid fa-stopwatch text-emerald-600 mt-0.5 shrink-0"></i>
        <span><b>名师配速建议</b>: {{ mathStore.resultData.diagnosis.speed_advice }}</span>
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

const secPerItem = computed(() => {
  const d = mathStore.resultData?.diagnosis;
  if (d && d.sec_per_item && d.sec_per_item > 0) return d.sec_per_item;
  const total = mathStore.resultData?.summary?.total || 0;
  return total > 0 ? (23 * 60 / total).toFixed(1) : '18.0';
});

const speedLevel = computed(() => {
  return mathStore.resultData?.diagnosis?.speed_level || '良好';
});

const speedBadgeText = computed(() => {
  const lvl = speedLevel.value;
  if (lvl === '极速') return '⚡ 极速神算手';
  if (lvl === '良好') return '🎯 黄金标准配速';
  if (lvl === '偏慢') return '⏳ 稳健深算型';
  return '标准配速';
});

const speedBadgeClass = computed(() => {
  const lvl = speedLevel.value;
  if (lvl === '极速') return 'bg-blue-50 text-blue-700 border-blue-200';
  if (lvl === '良好') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  return 'bg-amber-50 text-amber-700 border-amber-200';
});

function handleRetry() {
  mathStore.reset();
  router.replace({ path: '/', query: { mode: 'math' } });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
</script>
