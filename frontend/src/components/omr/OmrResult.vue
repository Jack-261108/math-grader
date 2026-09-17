<template>
  <section v-if="omrStore.resultData" class="space-y-4">
    <!-- 行测总分成绩卡片 -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-sm relative overflow-hidden">
      <div class="flex items-start justify-between">
        <div>
          <div class="text-[11px] text-blue-600 uppercase tracking-wider font-semibold">行测实战模考成绩单</div>
          <h2 class="text-lg font-bold text-slate-900 mt-0.5">{{ omrStore.resultData.exam_title || '行测答题卡诊断' }}</h2>
          <p class="text-xs text-slate-500 mt-0.5">交卷用时: {{ omrStore.resultData.summary?.time_str || '110分00秒' }}</p>
        </div>
        <!-- 评级印章与答题卡按钮 -->
        <div class="flex items-center space-x-2">
          <button
            type="button"
            @click="omrStore.currentResultTab = 'card'"
            class="px-2.5 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200/90 font-bold text-xs flex items-center space-x-1.5 shadow-2xs transition active:scale-95 cursor-pointer"
            title="点击查看电子答题卡全卷涂点还原矩阵"
          >
            <i class="fa-solid fa-table-cells text-blue-600"></i>
            <span>答题卡</span>
          </button>
          <div class="stamp-badge-blue px-3 py-1 text-center font-serif font-black">
            <div class="text-[9px] tracking-widest uppercase">评级</div>
            <div class="text-2xl leading-none">{{ omrStore.resultData.summary?.grade_badge || 'B' }}</div>
          </div>
        </div>
      </div>

      <!-- 分数大卡 -->
      <div class="mt-4 pt-3 border-t border-slate-100 flex items-baseline justify-between">
        <div>
          <span class="text-xs text-slate-500 font-medium">行测实得分</span>
          <div class="flex items-baseline space-x-1">
            <span class="text-4xl font-extrabold text-blue-600">{{ omrStore.resultData.summary?.total_earned_score || 0 }}</span>
            <span class="text-sm font-bold text-slate-400">/ {{ omrStore.resultData.summary?.total_max_score || 100 }} 分</span>
          </div>
        </div>
        <div class="text-right">
          <span class="text-xs text-slate-500 font-medium">得分率</span>
          <div class="text-2xl font-bold text-slate-800">{{ omrStore.resultData.summary?.score_ratio_pct || 0 }}%</div>
        </div>
      </div>

      <!-- 4列指标胶囊 -->
      <div class="grid grid-cols-4 gap-1.5 mt-3 pt-2 text-center text-xs">
        <div
          class="bg-slate-50 hover:bg-slate-100 rounded-xl p-2 cursor-pointer transition"
          @click="omrStore.currentResultTab = 'card'"
        >
          <div class="text-[10px] text-slate-400">总题数</div>
          <div class="text-sm font-bold text-slate-800">{{ omrStore.resultData.summary?.total_questions || 0 }}</div>
        </div>
        <div class="bg-emerald-50 hover:bg-emerald-100 rounded-xl p-2 cursor-pointer transition">
          <div class="text-[10px] text-emerald-600">答对</div>
          <div class="text-sm font-bold text-emerald-600">{{ omrStore.resultData.summary?.total_correct || 0 }}</div>
        </div>
        <div
          class="bg-rose-50 hover:bg-rose-100 rounded-xl p-2 cursor-pointer transition ring-1 ring-rose-200/80"
          @click="omrStore.currentResultTab = 'card'"
        >
          <div class="text-[10px] text-rose-600 font-medium flex items-center justify-center space-x-0.5">
            <span>做错</span>
            <i class="fa-solid fa-arrow-right text-[8px]"></i>
          </div>
          <div class="text-sm font-bold text-rose-600">{{ omrStore.resultData.summary?.total_wrong || 0 }}</div>
        </div>
        <div class="bg-amber-50 hover:bg-amber-100 rounded-xl p-2 cursor-pointer transition">
          <div class="text-[10px] text-amber-600">未涂/多涂</div>
          <div class="text-sm font-bold text-amber-600">{{ omrStore.resultData.summary?.total_unanswered || 0 }}</div>
        </div>
      </div>
    </div>

    <!-- ⚡ 混合 OMR 极速识别成效卡片 (如果包含混合指标) -->
    <div
      v-if="hybridStat"
      class="bg-gradient-to-r from-blue-50/90 via-indigo-50/70 to-emerald-50/70 border border-blue-200/80 rounded-2xl px-3.5 py-2.5 flex items-center justify-between text-xs text-slate-700 shadow-2xs"
    >
      <div class="flex items-center space-x-2 min-w-0">
        <span class="w-6 h-6 rounded-lg bg-blue-600 text-white flex items-center justify-center text-xs shrink-0 shadow-2xs">
          <i class="fa-solid fa-bolt"></i>
        </span>
        <div class="min-w-0">
          <div class="font-bold text-blue-950 flex items-center space-x-1.5 flex-wrap">
            <span>CV + 多模态混合极速批改</span>
            <span class="text-[10px] px-1.5 py-0.2 rounded-full bg-emerald-100 text-emerald-800 font-bold">
              节约 Token {{ hybridStat.token_saved_pct }}%
            </span>
          </div>
          <p class="text-[10px] text-slate-500 truncate mt-0.5">
            本地直出: <b>{{ hybridStat.local_resolved }}</b> 题 · 靶向审验: <b>{{ hybridStat.reviewed_count }}</b> 题 · 耗时: <b>{{ hybridStat.elapsed_ms }}ms</b>
          </p>
        </div>
      </div>
      <span class="text-[10px] text-blue-700 font-bold bg-white/80 px-2 py-1 rounded-xl border border-blue-100 shrink-0 ml-2 hidden sm:inline">
        准确率双重互验
      </span>
    </div>

    <!-- 结果页三大核心维度 Segmented Tabs -->
    <div class="sticky top-2 z-30 bg-white/95 backdrop-blur-md p-1 rounded-2xl border border-slate-200/90 shadow-sm flex items-center gap-1 text-xs">
      <button
        type="button"
        @click="omrStore.currentResultTab = 'diag'"
        :class="omrStore.currentResultTab === 'diag'
          ? 'flex-1 py-2 px-2.5 rounded-xl font-bold transition flex items-center justify-center space-x-1.5 bg-blue-600 text-white shadow-xs cursor-pointer'
          : 'flex-1 py-2 px-2.5 rounded-xl font-semibold transition flex items-center justify-center space-x-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 cursor-pointer'"
      >
        <i class="fa-solid fa-chart-pie text-xs"></i>
        <span>成绩与学情</span>
      </button>
      <button
        type="button"
        @click="omrStore.currentResultTab = 'timing'"
        :class="omrStore.currentResultTab === 'timing'
          ? 'flex-1 py-2 px-2.5 rounded-xl font-bold transition flex items-center justify-center space-x-1.5 bg-blue-600 text-white shadow-xs cursor-pointer'
          : 'flex-1 py-2 px-2.5 rounded-xl font-semibold transition flex items-center justify-center space-x-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 cursor-pointer'"
      >
        <i class="fa-solid fa-stopwatch text-xs text-amber-400"></i>
        <span>模考配速与象限</span>
      </button>
      <button
        type="button"
        @click="omrStore.currentResultTab = 'card'"
        :class="omrStore.currentResultTab === 'card'
          ? 'flex-1 py-2 px-2.5 rounded-xl font-bold transition flex items-center justify-center space-x-1.5 bg-blue-600 text-white shadow-xs cursor-pointer'
          : 'flex-1 py-2 px-2.5 rounded-xl font-semibold transition flex items-center justify-center space-x-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 cursor-pointer'"
      >
        <i class="fa-solid fa-id-card text-xs text-blue-400"></i>
        <span>答题卡批注</span>
      </button>
    </div>

    <!-- Tab 1: 【📊 成绩与学情诊断】 -->
    <div v-show="omrStore.currentResultTab === 'diag'" class="space-y-4">
      <!-- 五大模块得分明细 -->
      <div class="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="font-bold text-xs text-slate-800 flex items-center space-x-1.5">
            <i class="fa-solid fa-chart-pie text-blue-600"></i>
            <span>五大模块得分率与题数明细</span>
          </h3>
          <span class="text-[10px] text-slate-400">客观题分模块计分与正确率统计</span>
        </div>

        <div class="space-y-2.5">
          <div
            v-for="sec in omrStore.resultData.section_results"
            :key="sec.name"
            class="bg-slate-50 hover:bg-slate-100/90 p-2.5 rounded-xl border border-slate-200/80 hover:border-blue-300 space-y-1.5 text-xs transition cursor-pointer group shadow-2xs"
            @click="omrStore.currentResultTab = 'card'"
          >
            <div class="flex items-center justify-between">
              <div class="font-bold text-slate-800 flex items-center space-x-1">
                <span>{{ sec.name }}</span>
                <span class="text-[10px] text-slate-400 font-normal">({{ sec.start_q }}~{{ sec.end_q }}题)</span>
                <i class="fa-solid fa-chevron-right text-[9px] text-slate-300 group-hover:text-blue-500 group-hover:translate-x-0.5 transition-all ml-0.5"></i>
              </div>
              <div class="flex items-center space-x-1.5">
                <span class="font-bold text-blue-700">{{ sec.earned_score }} / {{ sec.max_score }}分</span>
                <span :class="getAccBadgeClass(sec.accuracy_pct)">{{ sec.accuracy_pct }}% 正确率</span>
              </div>
            </div>
            <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
              <div :class="[getAccBarClass(sec.accuracy_pct), 'h-full transition-all duration-500']" :style="{ width: `${sec.accuracy_pct}%` }"></div>
            </div>
            <div class="flex justify-between text-[10px] text-slate-400">
              <span>对: {{ sec.correct_q }} 题 · 错: {{ sec.wrong_q }} 题</span>
              <span class="group-hover:text-blue-600 transition">单题分值: {{ sec.score_per_q }}分 · <strong>查看答题卡</strong></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 学情诊断与提分锦囊 -->
      <div class="bg-gradient-to-br from-blue-50/80 via-white to-amber-50/50 rounded-2xl p-4 border border-blue-100 shadow-sm space-y-3">
        <div class="flex items-center space-x-2 border-b border-blue-100/60 pb-2">
          <div class="w-6 h-6 rounded-lg bg-blue-600 text-white flex items-center justify-center text-xs">
            <i class="fa-solid fa-lightbulb"></i>
          </div>
          <h3 class="font-bold text-slate-800 text-sm">行测备考学情诊断</h3>
        </div>
        <div class="space-y-1.5 text-xs">
          <div class="flex items-start space-x-2">
            <span class="text-rose-600 font-bold shrink-0">需重点突击:</span>
            <span class="text-slate-700 font-medium">{{ omrStore.resultData.diagnosis?.weakest_section || '均衡' }}</span>
          </div>
          <div class="flex items-start space-x-2">
            <span class="text-emerald-600 font-bold shrink-0">优势主力模块:</span>
            <span class="text-slate-700 font-medium">{{ omrStore.resultData.diagnosis?.strongest_section || '均衡' }}</span>
          </div>
        </div>
        <div v-if="omrStore.resultData.diagnosis?.actionable_tips?.length" class="bg-amber-50/80 border border-amber-200/60 rounded-xl p-3 text-xs space-y-1.5">
          <div class="font-bold text-amber-900 text-xs flex items-center space-x-1.5">
            <i class="fa-solid fa-bullseye text-amber-600"></i>
            <span>名师提分点拨</span>
          </div>
          <ul class="space-y-1.5 text-[11px] text-amber-800 list-disc list-inside">
            <li v-for="(tip, idx) in omrStore.resultData.diagnosis.actionable_tips" :key="idx">{{ tip }}</li>
          </ul>
        </div>
      </div>

      <!-- 行动横幅：直通电子答题卡 -->
      <div class="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-4 text-white shadow-sm flex items-center justify-between">
        <div class="min-w-0 pr-2">
          <div class="font-bold text-sm">公考电子答题卡与红笔批注</div>
          <p class="text-xs text-blue-100 mt-0.5">全卷客观题对错色块还原、原图红笔批注与在线改选重判</p>
        </div>
        <button
          type="button"
          @click="omrStore.currentResultTab = 'card'"
          class="px-4 py-2 bg-white text-blue-700 hover:bg-blue-50 active:scale-95 font-bold text-xs rounded-xl shadow-sm transition shrink-0 cursor-pointer flex items-center space-x-1"
        >
          <span>查看答题卡</span>
          <i class="fa-solid fa-arrow-right"></i>
        </button>
      </div>
    </div>

    <!-- Tab 2: 【⏱️ 模考配速与性价比四象限诊断】 -->
    <div v-show="omrStore.currentResultTab === 'timing'" class="space-y-4">
      <OmrTimingAnalysis />
    </div>

    <!-- Tab 3: 【📋 卷面与答题卡】 -->
    <div v-show="omrStore.currentResultTab === 'card'" class="space-y-4">
      <!-- 批注答题卡全景图 -->
      <div v-if="omrStore.resultData.card_url" class="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-1.5">
            <span class="font-bold text-xs sm:text-sm text-slate-800">批注答题卡全景图</span>
            <span class="text-[10px] px-2 py-0.5 bg-rose-50 text-rose-600 rounded-full font-bold border border-rose-100">红笔对错原卷批改</span>
          </div>
          <a
            :href="omrStore.resultData.card_url"
            download="批改答题卡全景图.jpg"
            class="text-rose-600 hover:text-rose-700 text-xs font-semibold flex items-center bg-rose-50 hover:bg-rose-100 px-2.5 py-1 rounded-lg transition"
          >
            <i class="fa-solid fa-download mr-1 text-[11px]"></i> 保存批改答题卡
          </a>
        </div>
        <div
          class="rounded-xl overflow-hidden bg-slate-900 border border-slate-200 cursor-zoom-in relative group max-h-[70vh] flex items-center justify-center"
          @click="modalStore.openFullscreen(omrStore.resultData.card_url)"
        >
          <img
            :src="omrStore.resultData.card_url"
            alt="批注答题卡"
            class="w-full h-auto max-h-[70vh] object-contain"
          >
          <div class="absolute bottom-2 right-2 px-2.5 py-1 bg-black/70 backdrop-blur-sm text-white text-[11px] rounded-lg pointer-events-none flex items-center space-x-1.5">
            <i class="fa-solid fa-magnifying-glass-plus"></i>
            <span>点击全屏查看批注细节 (支持双指缩放)</span>
          </div>
        </div>
      </div>

      <!-- 电子答题卡全卷色块还原矩阵 -->
      <OmrMatrixCard />

      <!-- 考生填涂核验与在线纠偏抽屉 -->
      <OmrCorrectionDrawer />
    </div>

    <!-- A4 排版导出横幅 -->
    <div class="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-4 text-white shadow-sm flex items-center justify-between">
      <div class="min-w-0 pr-2">
        <div class="font-bold text-sm">🖨️ A4 错题本与自测重做卷导出</div>
        <p class="text-xs text-blue-100 mt-0.5">一键生成标准 A4 错题重做卷，包含原题题干与名师解析</p>
      </div>
      <button
        type="button"
        @click="modalStore.openPrint('omr')"
        class="px-4 py-2 bg-white text-blue-700 hover:bg-blue-50 active:scale-95 font-bold text-xs rounded-xl shadow-sm transition shrink-0 cursor-pointer flex items-center space-x-1"
      >
        <span>生成自测卷</span>
        <i class="fa-solid fa-arrow-right"></i>
      </button>
    </div>

    <!-- 重新批改按钮 -->
    <div class="pt-2">
      <button
        type="button"
        @click="handleRetry"
        class="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-3 px-4 rounded-xl shadow-sm transition flex items-center justify-center space-x-2 text-sm cursor-pointer"
      >
        <i class="fa-solid fa-camera-rotate"></i>
        <span>批改下一张答题卡</span>
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import { useOmrStore } from '../../stores/omr';
import { useModalStore } from '../../stores/modal';
import { useRouter } from 'vue-router';
import OmrMatrixCard from './OmrMatrixCard.vue';
import OmrCorrectionDrawer from './OmrCorrectionDrawer.vue';
import OmrTimingAnalysis from './OmrTimingAnalysis.vue';

const omrStore = useOmrStore();
const modalStore = useModalStore();
const router = useRouter();

const hybridStat = computed(() => omrStore.resultData?.summary?.hybrid_stats || null);

function getAccBarClass(acc) {
  if (acc >= 80) return 'bg-emerald-500';
  if (acc >= 60) return 'bg-blue-500';
  return 'bg-rose-500';
}

function getAccBadgeClass(acc) {
  if (acc >= 80) return 'px-1.5 py-0.2 rounded font-bold text-[10px] text-emerald-700 bg-emerald-50';
  if (acc >= 60) return 'px-1.5 py-0.2 rounded font-bold text-[10px] text-blue-700 bg-blue-50';
  return 'px-1.5 py-0.2 rounded font-bold text-[10px] text-rose-700 bg-rose-50';
}

function handleRetry() {
  omrStore.reset();
  router.replace({ path: '/', query: { mode: 'omr' } });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
</script>
