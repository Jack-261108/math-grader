<template>
  <div class="space-y-4">
    <!-- 在线做题工具栏与进度卡片 -->
    <div class="bg-white rounded-2xl p-4 border border-slate-200/90 shadow-2xs space-y-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="w-2.5 h-2.5 rounded-full bg-blue-600 animate-pulse"></span>
          <h3 class="font-bold text-slate-800 text-sm">极速在线答题卡 (原生涂卡纸)</h3>
        </div>
        <div class="flex items-center space-x-2">
          <button
            type="button"
            @click="randomFill"
            class="text-[11px] text-slate-500 hover:text-blue-600 font-medium"
          >
            随机填涂
          </button>
          <button
            type="button"
            @click="clearAll"
            class="text-[11px] text-slate-400 hover:text-rose-600 font-medium"
          >
            清空
          </button>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="space-y-1.5">
        <div class="flex justify-between text-xs font-semibold">
          <span class="text-blue-700">已作答 {{ omrStore.answeredOnlineCount }} / {{ omrStore.totalQuestions }} 题 ({{ progressPct }}%)</span>
          <span :class="remainingCount === 0 ? 'font-bold text-emerald-600' : 'font-bold text-amber-600'">
            {{ remainingCount === 0 ? '🎉 全部作答完成' : `剩余 ${remainingCount} 题未答` }}
          </span>
        </div>
        <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
          <div class="bg-blue-600 h-full transition-all duration-300" :style="{ width: `${progressPct}%` }"></div>
        </div>
      </div>
    </div>

    <!-- 模块分组气泡矩阵容器 -->
    <div class="space-y-3">
      <div
        v-for="(sec, sIdx) in omrStore.currentSections"
        :key="sIdx"
        class="bg-white rounded-2xl p-3.5 sm:p-4 border border-slate-200/90 shadow-2xs space-y-2.5"
      >
        <div class="flex items-center justify-between border-b border-slate-100 pb-2">
          <div class="flex items-center space-x-1.5 min-w-0">
            <span class="w-2 h-2 rounded-full bg-blue-600 shrink-0"></span>
            <h4 class="font-bold text-xs text-slate-800 truncate">{{ sec.name }}</h4>
            <span class="text-[10px] text-slate-400 font-medium shrink-0">({{ sec.start_q }}~{{ sec.end_q }}题 · 单题{{ sec.score_per_q }}分)</span>
          </div>
          <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 shrink-0">
            {{ getSecAnsweredCount(sec) }} / {{ sec.end_q - sec.start_q + 1 }} 题
          </span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5">
          <div
            v-for="q in getQuestionsInRange(sec.start_q, sec.end_q)"
            :key="q"
            class="flex items-center justify-between px-3 py-2 rounded-xl bg-slate-50/80 border border-slate-200/70 hover:bg-slate-100/70 transition min-w-0"
          >
            <button
              type="button"
              @click="modalStore.openQuestion(q)"
              class="shrink-0 min-w-[2.5rem] px-2 py-1 rounded-lg bg-white border border-slate-300 hover:border-blue-500 hover:bg-blue-50 text-slate-700 hover:text-blue-700 font-extrabold text-xs transition flex items-center justify-center space-x-1 shadow-2xs active:scale-95 cursor-pointer"
              :title="`点击查看第 ${q} 题题干与解析`"
            >
              <span>{{ q }}</span>
              <i class="fa-regular fa-file-lines text-[9px] text-slate-400"></i>
            </button>

            <!-- A B C D 气泡 -->
            <div class="flex items-center space-x-2 shrink-0">
              <button
                v-for="opt in ['A', 'B', 'C', 'D']"
                :key="opt"
                type="button"
                @click="handleBubbleClick(q, opt)"
                :class="omrStore.onlineAnswers[q] === opt
                  ? 'w-8 h-8 rounded-full font-black text-xs transition-all duration-150 flex items-center justify-center cursor-pointer select-none bg-blue-600 border-2 border-blue-700 text-white shadow-xs scale-105 shrink-0'
                  : 'w-8 h-8 rounded-full font-bold text-xs transition-all duration-150 flex items-center justify-center cursor-pointer select-none bg-white border border-slate-300 text-slate-700 hover:border-blue-400 hover:bg-blue-50/60 shrink-0'"
              >
                {{ opt }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部提交答卷大按钮 -->
    <div class="pt-2 sticky bottom-4 z-20">
      <button
        type="button"
        @click="handleSubmit"
        class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 active:scale-98 text-white font-bold py-3.5 px-4 rounded-xl shadow-lg transition flex items-center justify-center space-x-2 text-sm cursor-pointer"
      >
        <i class="fa-solid fa-paper-plane text-xs"></i>
        <span>🚀 提交在线答卷 · 智能秒批 (已作答 {{ omrStore.answeredOnlineCount }} 题)</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useOmrStore } from '../../stores/omr';
import { useModalStore } from '../../stores/modal';
import { useRouter } from 'vue-router';

const omrStore = useOmrStore();
const modalStore = useModalStore();
const router = useRouter();

const progressPct = computed(() => {
  const total = omrStore.totalQuestions;
  if (!total) return 0;
  return Math.round((omrStore.answeredOnlineCount / total) * 100);
});

const remainingCount = computed(() => {
  return Math.max(0, omrStore.totalQuestions - omrStore.answeredOnlineCount);
});

function getQuestionsInRange(start, end) {
  const arr = [];
  for (let i = start; i <= end; i++) arr.push(i);
  return arr;
}

function getSecAnsweredCount(sec) {
  let c = 0;
  for (let q = sec.start_q; q <= sec.end_q; q++) {
    if (omrStore.onlineAnswers[q]) c++;
  }
  return c;
}

function handleBubbleClick(qNum, opt) {
  if (omrStore.onlineAnswers[qNum] === opt) {
    omrStore.setOnlineAnswer(qNum, null);
  } else {
    omrStore.setOnlineAnswer(qNum, opt);
  }
}

function randomFill() {
  const opts = ['A', 'B', 'C', 'D'];
  const total = omrStore.totalQuestions;
  for (let i = 1; i <= total; i++) {
    omrStore.setOnlineAnswer(i, opts[Math.floor(Math.random() * opts.length)]);
  }
}

function clearAll() {
  if (confirm('确定要清空当前所有在线填涂吗？')) {
    omrStore.onlineAnswers = {};
  }
}

async function handleSubmit() {
  try {
    const data = await omrStore.submitGradeFromOnline();
    if (data?.task_id) {
      router.replace({ path: '/', query: { mode: 'omr', task_id: data.task_id } });
    }
  } catch (err) {
    alert(err.message || '提交失败');
  }
}
</script>
