<template>
  <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden transition-all">
    <!-- 触发条 -->
    <div
      @click="isOpen = !isOpen"
      class="p-3.5 sm:p-4 flex items-center justify-between cursor-pointer select-none hover:bg-slate-50/80 transition-colors group"
    >
      <div class="flex items-center space-x-2.5 min-w-0">
        <div class="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 border border-amber-200/60 flex items-center justify-center text-xs shrink-0 shadow-2xs group-hover:bg-amber-600 group-hover:text-white transition">
          <i class="fa-solid fa-list-check"></i>
        </div>
        <div class="min-w-0">
          <div class="flex items-center space-x-2">
            <h4 class="font-bold text-xs sm:text-sm text-slate-800 truncate">填涂识别核验与在线纠偏</h4>
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200 shrink-0">
              已识别 {{ items.length }} 题
            </span>
          </div>
          <p class="text-[11px] text-slate-400 truncate mt-0.5">核对漏涂浅涂，在线改选 ABCD 并一键重新核算与重绘原卷</p>
        </div>
      </div>
      <div class="flex items-center space-x-1.5 text-xs font-bold text-amber-600 shrink-0 pl-2">
        <span>{{ isOpen ? '收起核验' : '展开核验' }}</span>
        <i :class="isOpen ? 'fa-solid fa-chevron-up text-xs' : 'fa-solid fa-chevron-down text-xs'"></i>
      </div>
    </div>

    <!-- 纠偏提醒吸顶提示栏 (当有已修改的项时展示) -->
    <div
      v-if="omrStore.correctionDiffKeys.length > 0"
      class="bg-amber-50 border-y border-amber-200 px-4 py-2.5 flex items-center justify-between gap-2"
    >
      <div class="flex items-center space-x-2 text-xs text-amber-900 min-w-0">
        <i class="fa-solid fa-triangle-exclamation text-amber-600 shrink-0"></i>
        <span class="truncate font-medium">已纠偏 {{ omrStore.correctionDiffKeys.length }} 处填涂</span>
      </div>
      <div class="flex items-center space-x-1.5 shrink-0">
        <button
          type="button"
          @click="handleCancelCorrections"
          class="px-2 py-1 text-[11px] font-medium text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-lg transition"
        >
          放弃修改
        </button>
        <button
          type="button"
          @click="handleApplyCorrections"
          :disabled="isApplying"
          class="px-3 py-1 text-xs font-bold bg-amber-500 hover:bg-amber-600 text-white rounded-lg transition shadow-2xs flex items-center space-x-1 disabled:opacity-60"
        >
          <i :class="isApplying ? 'fa-solid fa-circle-notch fa-spin' : 'fa-solid fa-bolt'"></i>
          <span>{{ isApplying ? '正在秒级重算...' : `⚡ 重新判分与重绘 (${omrStore.correctionDiffKeys.length})` }}</span>
        </button>
      </div>
    </div>

    <!-- 抽屉展开内容 -->
    <div v-show="isOpen" class="p-3.5 sm:p-4 border-t border-slate-100 space-y-3 bg-slate-50/40">
      <!-- 快捷导入与分类 Tab -->
      <div class="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-200">
        <div class="flex bg-slate-200/80 p-0.5 rounded-xl text-xs">
          <button
            type="button"
            @click="omrStore.verifyFilter = 'all'"
            :class="omrStore.verifyFilter === 'all' ? 'px-2.5 py-1 rounded-lg font-bold bg-white text-blue-700 shadow-2xs transition' : 'px-2.5 py-1 rounded-lg font-medium text-slate-600 hover:text-slate-900 transition'"
          >
            全部 ({{ items.length }})
          </button>
          <button
            type="button"
            @click="omrStore.verifyFilter = 'wrong'"
            :class="omrStore.verifyFilter === 'wrong' ? 'px-2.5 py-1 rounded-lg font-bold bg-white text-blue-700 shadow-2xs transition' : 'px-2.5 py-1 rounded-lg font-medium text-slate-600 hover:text-slate-900 transition'"
          >
            做错 ({{ wrongCount }})
          </button>
          <button
            type="button"
            @click="omrStore.verifyFilter = 'unans'"
            :class="omrStore.verifyFilter === 'unans' ? 'px-2.5 py-1 rounded-lg font-bold bg-white text-blue-700 shadow-2xs transition' : 'px-2.5 py-1 rounded-lg font-medium text-slate-600 hover:text-slate-900 transition'"
          >
            未填 ({{ unansCount }})
          </button>
          <button
            v-if="omrStore.correctionDiffKeys.length > 0"
            type="button"
            @click="omrStore.verifyFilter = 'corrected'"
            :class="omrStore.verifyFilter === 'corrected' ? 'px-2.5 py-1 rounded-lg font-bold bg-white text-blue-700 shadow-2xs transition' : 'px-2.5 py-1 rounded-lg font-medium text-slate-600 hover:text-slate-900 transition'"
          >
            已纠偏 ({{ omrStore.correctionDiffKeys.length }})
          </button>
        </div>

        <button
          type="button"
          @click="loadToOnlineSheet"
          class="text-xs text-blue-600 hover:text-blue-800 font-semibold flex items-center space-x-1 bg-blue-50 hover:bg-blue-100 px-2.5 py-1.5 rounded-xl transition"
        >
          <i class="fa-solid fa-pen-to-square text-[10px]"></i>
          <span>导入极速涂卡纸核对</span>
        </button>
      </div>

      <!-- 条目列表 -->
      <div class="max-h-[450px] overflow-y-auto matrix-scroll space-y-2">
        <div
          v-for="it in filteredList"
          :key="it.q_num"
          :class="[
            'p-2.5 rounded-xl border transition-all duration-150 space-y-1.5 shadow-2xs',
            getCardStyle(it)
          ]"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-1.5">
              <span class="w-6 h-6 rounded-md bg-slate-800 text-white font-black text-xs flex items-center justify-center shrink-0">
                {{ it.q_num }}
              </span>
              <span class="text-xs font-bold text-slate-700 truncate max-w-[80px]">{{ it.section_name }}</span>
              <span class="text-[10px] text-slate-400">{{ it.score_per_q }}分</span>
            </div>

            <div class="flex items-center space-x-1.5">
              <!-- 状态 Badge -->
              <span v-if="isItemCorrected(it.q_num)" class="px-1.5 py-0.2 rounded bg-amber-500 text-white font-extrabold text-[10px] animate-pulse">
                已纠偏 ({{ origAns(it.q_num) || '未填' }}➔{{ curAns(it.q_num) || '未填' }})
              </span>
              <span v-else-if="curAns(it.q_num) === it.standard_choice" class="px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px]">
                对 ✓
              </span>
              <span v-else-if="curAns(it.q_num)" class="px-1.5 py-0.2 rounded bg-rose-100 text-rose-800 font-bold text-[10px]">
                错 ✗ (正解: {{ it.standard_choice }})
              </span>
              <span v-else class="px-1.5 py-0.2 rounded bg-slate-200 text-slate-600 font-medium text-[10px]">
                未填 (正解: {{ it.standard_choice }})
              </span>

              <button
                type="button"
                @click="modalStore.openQuestion(it.q_num)"
                class="text-[11px] font-semibold text-blue-600 hover:text-blue-800 hover:bg-blue-50 p-1 rounded-md transition"
                :title="`查看第 ${it.q_num} 题原题题干与解析`"
              >
                <i class="fa-solid fa-book-open text-[10px]"></i>
              </button>
            </div>
          </div>

          <!-- A B C D 纠偏按钮组 -->
          <div class="flex items-center justify-between pt-0.5">
            <span class="text-[10px] text-slate-400 font-medium">填涂选项:</span>
            <div class="flex items-center space-x-1.5">
              <button
                v-for="opt in ['A', 'B', 'C', 'D']"
                :key="opt"
                type="button"
                @click="omrStore.setCorrectionAnswer(it.q_num, opt)"
                :class="getOptBtnStyle(it, opt)"
              >
                {{ opt }}
              </button>
              <button
                type="button"
                @click="omrStore.setCorrectionAnswer(it.q_num, null)"
                class="w-6 h-6 rounded-full text-[10px] font-semibold text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-transparent hover:border-rose-200 transition flex items-center justify-center"
                title="清空为此题未填/留白"
              >
                <i class="fa-solid fa-ban"></i>
              </button>
            </div>
          </div>
        </div>

        <div v-if="filteredList.length === 0" class="py-8 text-center text-slate-400 text-xs">
          <i class="fa-solid fa-circle-check text-2xl text-emerald-400 mb-1.5"></i>
          <div>当前筛选下没有对应题目</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useOmrStore } from '../../stores/omr';
import { useModalStore } from '../../stores/modal';

const omrStore = useOmrStore();
const modalStore = useModalStore();

const isOpen = ref(false);
const isApplying = ref(false);

const items = computed(() => omrStore.resultData?.items || []);

const wrongCount = computed(() => {
  return items.value.filter(it => {
    const cur = curAns(it.q_num);
    return Boolean(cur && it.standard_choice && cur !== it.standard_choice);
  }).length;
});

const unansCount = computed(() => {
  return items.value.filter(it => !curAns(it.q_num)).length;
});

const filteredList = computed(() => {
  const f = omrStore.verifyFilter;
  return items.value.filter(it => {
    const cur = curAns(it.q_num);
    const orig = origAns(it.q_num);
    const std = it.standard_choice;
    const isCorrected = (cur !== orig);
    const isWrong = (Boolean(cur) && Boolean(std) && cur !== std);
    const isUnans = !cur;

    if (f === 'wrong') return isWrong;
    if (f === 'unans') return isUnans;
    if (f === 'corrected') return isCorrected;
    return true;
  });
});

function origAns(qNum) {
  return omrStore.originalStudentAnswers[qNum] || null;
}

function curAns(qNum) {
  return omrStore.workingStudentAnswers[qNum] || null;
}

function isItemCorrected(qNum) {
  return origAns(qNum) !== curAns(qNum);
}

function getCardStyle(it) {
  if (isItemCorrected(it.q_num)) {
    return 'bg-amber-50/90 border-amber-300 ring-1 ring-amber-200';
  }
  const cur = curAns(it.q_num);
  if (cur && cur !== it.standard_choice) {
    return 'bg-rose-50/60 border-rose-200/90';
  }
  return 'bg-white border-slate-200/80 hover:bg-slate-50/80';
}

function getOptBtnStyle(it, opt) {
  const cur = curAns(it.q_num);
  const isSel = (cur === opt);
  const corrected = isItemCorrected(it.q_num);
  const isCorrect = (cur === it.standard_choice);

  if (isSel) {
    if (corrected) {
      return 'w-7 h-7 rounded-full text-xs transition flex items-center justify-center cursor-pointer border bg-amber-500 border-amber-600 text-white font-black shadow-xs ring-2 ring-amber-300 scale-105';
    }
    if (isCorrect) {
      return 'w-7 h-7 rounded-full text-xs transition flex items-center justify-center cursor-pointer border bg-emerald-600 border-emerald-700 text-white font-black shadow-xs';
    }
    return 'w-7 h-7 rounded-full text-xs transition flex items-center justify-center cursor-pointer border bg-rose-600 border-rose-700 text-white font-black shadow-xs';
  }
  return 'w-7 h-7 rounded-full text-xs transition flex items-center justify-center cursor-pointer border bg-white border-slate-300 text-slate-700 hover:border-blue-400 hover:bg-blue-50/70';
}

function handleCancelCorrections() {
  if (confirm('确认放弃当前的填涂修改，还原为原始系统识别结果吗？')) {
    omrStore.resetCorrections();
  }
}

async function handleApplyCorrections() {
  isApplying.value = true;
  try {
    const diffCount = omrStore.correctionDiffKeys.length;
    await omrStore.applyCorrectionAndRegrade();
    alert(`🎉 纠偏重判成功！\n已成功纠正 ${diffCount} 处填涂，重新核算全卷总分并在原卷上重绘了批注！`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } catch (err) {
    alert('纠偏重判失败: ' + err.message);
  } finally {
    isApplying.value = false;
  }
}

function loadToOnlineSheet() {
  omrStore.onlineAnswers = { ...omrStore.workingStudentAnswers };
  omrStore.activeSubMode = 'online';
  omrStore.reset();
  window.scrollTo({ top: 0, behavior: 'smooth' });
  alert('🎉 已成功将答题卡识别填涂载入极速涂卡纸！\n核验无误后点击下方【提交在线答卷】即可生成最新报告。');
}
</script>
