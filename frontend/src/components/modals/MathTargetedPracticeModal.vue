<template>
  <Teleport to="body">
    <div
      v-if="modalStore.isTargetedPracticeOpen"
      class="fixed inset-0 z-[85] bg-black/75 backdrop-blur-sm flex flex-col justify-between overflow-y-auto p-2 sm:p-6 select-text"
    >
      <!-- 主内容卡片容器 -->
      <div class="max-w-4xl w-full mx-auto bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col my-auto max-h-[92vh]">
        <!-- 弹窗顶部栏 -->
        <div class="bg-gradient-to-r from-emerald-600 via-teal-600 to-indigo-700 text-white p-4 sm:p-5 flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-white/20 backdrop-blur-xs flex items-center justify-center text-xl font-black shadow-xs">
              🎯
            </div>
            <div>
              <div class="flex items-center space-x-2">
                <h3 class="font-black text-base sm:text-lg tracking-wide text-white">
                  {{ sheetData?.title || '速算靶向自适应强化练' }}
                </h3>
                <span class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-white/20 text-emerald-100 border border-white/25">
                  共 20 题
                </span>
              </div>
              <p class="text-xs text-emerald-100 mt-0.5">
                {{ sheetData?.target_description || '针对性同型算式即时动态生成 · 现场突破短板' }}
              </p>
            </div>
          </div>

          <!-- 右侧：秒表、重练、A4打印与关闭按钮 -->
          <div class="flex items-center space-x-2">
            <!-- 实时计时器 -->
            <div class="bg-black/30 backdrop-blur-xs px-3 py-1.5 rounded-xl border border-white/20 text-xs font-mono flex items-center space-x-1.5">
              <i class="fa-regular fa-clock text-amber-300"></i>
              <span>用时: <b class="text-white">{{ formattedElapsed }}</b></span>
            </div>

            <!-- 重新生成一组 -->
            <button
              type="button"
              @click="fetchExercises"
              :disabled="isLoading"
              class="px-3 py-1.5 bg-white/15 hover:bg-white/25 active:scale-95 text-white font-bold text-xs rounded-xl transition flex items-center space-x-1 cursor-pointer disabled:opacity-50"
              title="重新生成一套全新的 20 道同型变式题"
            >
              <i class="fa-solid fa-arrows-rotate text-[11px]" :class="isLoading ? 'fa-spin' : ''"></i>
              <span class="hidden sm:inline">换一组</span>
            </button>

            <!-- 导出 A4 打印 -->
            <button
              type="button"
              @click="handlePrintA4"
              class="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 active:scale-95 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center space-x-1 cursor-pointer"
              title="导出为 A4 纸张空白练习卷打印"
            >
              <i class="fa-solid fa-print text-[11px]"></i>
              <span>A4打印</span>
            </button>

            <!-- 关闭弹窗 -->
            <button
              type="button"
              @click="closeModal"
              class="w-8 h-8 rounded-full bg-white/15 hover:bg-white/25 text-white flex items-center justify-center transition cursor-pointer"
            >
              <i class="fa-solid fa-xmark text-sm"></i>
            </button>
          </div>
        </div>

        <!-- 名师解题技巧提分锦囊 -->
        <div v-if="sheetData?.core_tip" class="bg-amber-50/90 border-b border-amber-200/80 px-4 py-2.5 text-xs text-amber-900 flex items-start space-x-2 shrink-0">
          <i class="fa-solid fa-lightbulb text-amber-600 mt-0.5 shrink-0 text-sm"></i>
          <div class="leading-relaxed">
            <span class="font-bold">破局口诀: </span>{{ sheetData.core_tip }}
          </div>
        </div>

        <!-- 题目作答区域 (可滚动) -->
        <div class="p-4 sm:p-6 overflow-y-auto flex-1 space-y-4">
          <!-- 正在加载中状态 -->
          <div v-if="isLoading" class="py-16 text-center text-slate-400 text-xs space-y-2">
            <i class="fa-solid fa-spinner fa-spin text-2xl text-emerald-600"></i>
            <div>正在动态生成 20 道高拟真度同型强化算式...</div>
          </div>

          <!-- 20 道题目网格 -->
          <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            <div
              v-for="(item, idx) in sheetData?.items"
              :key="item.q_num"
              class="p-3.5 rounded-xl border transition-all text-xs space-y-2"
              :class="getItemBorderClass(item)"
            >
              <div class="flex items-center justify-between">
                <span class="font-black text-[11px] text-slate-400 font-mono">#{{ idx + 1 }}</span>
                <span v-if="isGraded" class="font-bold text-xs" :class="itemResults[item.q_num]?.isCorrect ? 'text-emerald-600' : 'text-rose-600'">
                  {{ itemResults[item.q_num]?.isCorrect ? '正确 ✓' : '错误 ✗' }}
                </span>
                <span v-else class="text-[10px] text-slate-400">心算题</span>
              </div>

              <!-- 算式 -->
              <div class="text-base sm:text-lg font-black font-mono text-slate-800 tracking-wide">
                {{ item.expression }} =
              </div>

              <!-- 输入框 -->
              <div class="flex items-center space-x-1.5">
                <input
                  :id="`target_input_${idx}`"
                  type="text"
                  v-model="userAnswers[item.q_num]"
                  :disabled="isGraded"
                  @keydown.enter="handleEnterKey(idx)"
                  placeholder="输入答案"
                  class="w-full bg-slate-50 border rounded-lg px-2 py-1 text-sm font-bold font-mono focus:outline-none focus:ring-2 transition"
                  :class="getInputClass(item)"
                >
              </div>

              <!-- 判卷后的解析与正解提示 -->
              <div v-if="isGraded && !itemResults[item.q_num]?.isCorrect" class="text-[11px] pt-1 border-t border-rose-100 text-slate-600">
                <div>正解: <b class="text-emerald-700 font-mono font-bold">{{ item.expected }}</b></div>
                <div class="text-[10px] text-slate-400 mt-0.5">{{ item.tip }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部判卷与成果结算栏 -->
        <div class="p-4 bg-slate-50 border-t border-slate-200 shrink-0 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <!-- 成果结算指标 (判卷后展示) -->
          <div v-if="isGraded" class="flex items-center space-x-3 text-xs">
            <div class="flex items-center space-x-1.5">
              <span class="text-slate-500">强化战果:</span>
              <b class="text-base font-black" :class="accuracyPct >= 80 ? 'text-emerald-600' : 'text-amber-600'">
                {{ correctCount }} / 20 对 (正确率 {{ accuracyPct }}%)
              </b>
            </div>
            <span class="text-slate-300">|</span>
            <div class="text-slate-500">
              平均配速: <b class="text-slate-800 font-mono">{{ avgPaceSec }} 秒/题</b>
            </div>
          </div>

          <div v-else class="text-xs text-slate-500">
            作答进度: <b class="text-emerald-700 font-bold font-mono">{{ filledCount }}</b> / 20 题已填写
          </div>

          <!-- 动作大按钮 -->
          <div class="flex items-center space-x-2">
            <template v-if="!isGraded">
              <button
                type="button"
                @click="gradePractice"
                :disabled="isLoading"
                class="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 active:scale-95 text-white font-bold text-xs sm:text-sm shadow-md transition flex items-center space-x-2 cursor-pointer disabled:opacity-50"
              >
                <i class="fa-solid fa-check"></i>
                <span>交卷批改，查看强化成效</span>
              </button>
            </template>

            <template v-else>
              <button
                type="button"
                @click="fetchExercises"
                class="px-4 py-2 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-800 font-bold text-xs transition flex items-center space-x-1.5 cursor-pointer"
              >
                <i class="fa-solid fa-arrows-rotate text-xs"></i>
                <span>再练一组 20 题</span>
              </button>

              <button
                type="button"
                @click="closeModal"
                class="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition flex items-center space-x-1 cursor-pointer"
              >
                <span>完成强化，返回主页 ✓</span>
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue';
import { useModalStore } from '../../stores/modal';
import { useWrongBookStore } from '../../stores/wrongbook';
import { getTargetedExercises } from '../../api/math';
import { formatTimerSeconds } from '../../constants/examTiming';

const modalStore = useModalStore();
const wrongBookStore = useWrongBookStore();

const sheetData = ref(null);
const isLoading = ref(false);
const userAnswers = ref({});
const isGraded = ref(false);
const itemResults = ref({});

// 秒表
const elapsedSeconds = ref(0);
let timerInterval = null;

const formattedElapsed = computed(() => formatTimerSeconds(elapsedSeconds.value));

const filledCount = computed(() => {
  return Object.values(userAnswers.value).filter(v => v !== undefined && String(v).trim() !== '').length;
});

const correctCount = computed(() => {
  return Object.values(itemResults.value).filter(r => r.isCorrect).length;
});

const accuracyPct = computed(() => {
  if (!sheetData.value?.items?.length) return 0;
  return Math.round((correctCount.value / sheetData.value.items.length) * 100);
});

const avgPaceSec = computed(() => {
  if (elapsedSeconds.value === 0) return 0;
  return Math.round((elapsedSeconds.value / 20) * 10) / 10;
});

function startTimer() {
  elapsedSeconds.value = 0;
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    elapsedSeconds.value++;
  }, 1000);
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

onBeforeUnmount(() => {
  stopTimer();
});

watch(
  () => modalStore.isTargetedPracticeOpen,
  (isOpen) => {
    if (isOpen) {
      fetchExercises();
    } else {
      stopTimer();
      sheetData.value = null;
    }
  }
);

async function fetchExercises() {
  isLoading.value = true;
  isGraded.value = false;
  userAnswers.value = {};
  itemResults.value = {};
  stopTimer();

  try {
    const meta = modalStore.targetedPracticeMeta || {};
    const res = await getTargetedExercises(meta.weaknessType, 20, meta.weaknessName);
    sheetData.value = res;
    startTimer();
  } catch (err) {
    alert(err.message || '生成强化题失败');
  } finally {
    isLoading.value = false;
  }
}

function handleEnterKey(idx) {
  const nextInput = document.getElementById(`target_input_${idx + 1}`);
  if (nextInput) {
    nextInput.focus();
  }
}

function gradePractice() {
  stopTimer();
  isGraded.value = true;
  const items = sheetData.value?.items || [];

  items.forEach(it => {
    const userVal = String(userAnswers.value[it.q_num] || '').trim();
    const expVal = String(it.expected).trim();
    const isCorr = (userVal === expVal);
    itemResults.value[it.q_num] = {
      isCorrect: isCorr,
      userAnswer: userVal,
      expected: expVal
    };
  });
}

function getItemBorderClass(item) {
  if (!isGraded.value) {
    return 'bg-white border-slate-200 hover:border-emerald-300';
  }
  const res = itemResults.value[item.q_num];
  if (res?.isCorrect) {
    return 'bg-emerald-50/70 border-emerald-300 shadow-2xs';
  }
  return 'bg-rose-50/80 border-rose-300 shadow-2xs';
}

function getInputClass(item) {
  if (!isGraded.value) {
    return 'border-slate-300 text-slate-900 focus:border-emerald-500 focus:ring-emerald-500/20';
  }
  const res = itemResults.value[item.q_num];
  if (res?.isCorrect) {
    return 'border-emerald-400 bg-emerald-100/50 text-emerald-900';
  }
  return 'border-rose-400 bg-rose-100/50 text-rose-900 line-through';
}

function handlePrintA4() {
  if (!sheetData.value?.items) return;
  // 将 20 题转换装载进 wrongBookStore 并打开 PrintModal
  const sheet = {
    title: sheetData.value.title,
    total_items: sheetData.value.items.length,
    created_date: new Date().toLocaleDateString('zh-CN'),
    items: sheetData.value.items.map((it, i) => ({
      sheet_q_num: i + 1,
      topic_category: sheetData.value.title,
      module_name: '速算自适应强化练',
      expression: it.expression,
      expected_answer: String(it.expected),
      advice: it.tip,
      score_per_q: 1.0
    }))
  };
  wrongBookStore.generatedSheet = sheet;
  modalStore.openPrint('wrong_sheet');
}

function closeModal() {
  modalStore.closeTargetedPractice();
}
</script>
