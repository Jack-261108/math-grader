<template>
  <div
    v-if="modalStore.isQuestionModalOpen && currentItem"
    class="fixed inset-0 z-[65] bg-black/60 backdrop-blur-xs flex items-center justify-center p-3 animate-in fade-in duration-200"
    @click.self="modalStore.closeQuestion"
  >
    <div class="bg-white rounded-2xl max-w-lg w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden relative">
      <!-- 头部 -->
      <div class="px-4 py-3 bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white flex items-center justify-between shrink-0">
        <div class="flex items-center space-x-2 min-w-0">
          <span class="w-7 h-7 rounded-lg bg-blue-600 font-black text-sm flex items-center justify-center text-white shrink-0 shadow-xs">
            {{ currentItem.q_num }}
          </span>
          <div class="min-w-0">
            <div class="flex items-center space-x-1.5 flex-wrap">
              <span class="text-xs font-bold text-slate-100 truncate">{{ currentItem.section_name }}</span>
              <span class="text-[10px] text-slate-300">单题 {{ currentItem.score_per_q }}分</span>
            </div>
            <p class="text-[10px] text-slate-400 truncate">{{ omrStore.resultData?.exam_title || '行测全真模考卷' }}</p>
          </div>
        </div>

        <div class="flex items-center space-x-1.5 shrink-0 pl-2">
          <!-- 状态徽章 -->
          <span
            v-if="itemStatus === 'correct'"
            class="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/25 text-emerald-200 border border-emerald-500/40 inline-flex items-center space-x-1"
          >
            <i class="fa-solid fa-check text-[10px]"></i>
            <span>作答正确 ({{ currentItem.student_choice || currentItem.standard_choice }})</span>
          </span>
          <span
            v-else-if="itemStatus === 'wrong'"
            class="text-[11px] font-bold px-2 py-0.5 rounded-full bg-rose-500/25 text-rose-200 border border-rose-500/40 inline-flex items-center space-x-1"
          >
            <span>错选 <b class="text-rose-100">{{ currentItem.student_choice }}</b></span>
            <span class="text-rose-400/80">➔</span>
            <span>正解 <b class="text-emerald-300">{{ currentItem.standard_choice }}</b></span>
          </span>
          <span
            v-else
            class="text-[11px] font-bold px-2 py-0.5 rounded-full bg-slate-500/25 text-slate-200 border border-slate-500/40 inline-flex items-center space-x-1"
          >
            <span>未填 ➔ 正解 <b class="text-emerald-300">{{ currentItem.standard_choice }}</b></span>
          </span>

          <button
            type="button"
            @click="modalStore.closeQuestion"
            class="w-7 h-7 rounded-full text-slate-300 hover:text-white hover:bg-white/15 flex items-center justify-center transition ml-1"
          >
            <i class="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>
      </div>

      <!-- 可滚动内容区 -->
      <div class="flex-1 overflow-y-auto p-4 space-y-3.5 text-xs text-slate-700">
        <!-- 资料分析材料卡片 -->
        <div v-if="hasMaterial" class="bg-amber-50/70 border border-amber-200/80 rounded-xl p-3 space-y-2">
          <div class="flex items-center justify-between border-b border-amber-200/60 pb-1.5">
            <div class="font-bold text-amber-900 flex items-center space-x-1.5">
              <i class="fa-solid fa-book-open-reader text-amber-600"></i>
              <span>【本组题目资料与图表】</span>
            </div>
            <button
              type="button"
              @click="showMaterialText = !showMaterialText"
              class="text-[11px] text-amber-700 hover:text-amber-900 font-medium"
            >
              {{ showMaterialText ? '收起材料' : '展开材料' }}
            </button>
          </div>

          <div v-show="showMaterialText" class="text-[11px] text-slate-700 leading-relaxed max-h-48 overflow-y-auto" v-html="materialHtml"></div>

          <!-- 材料配图 -->
          <div v-if="currentItem.material_images && currentItem.material_images.length > 0" class="space-y-2 pt-1">
            <div
              v-for="(imgUrl, idx) in currentItem.material_images"
              :key="idx"
              class="rounded-xl overflow-hidden border border-amber-200 bg-white p-1 cursor-zoom-in relative group"
              @click="modalStore.openFullscreen(imgUrl)"
            >
              <img :src="imgUrl" alt="材料图表" class="w-full h-auto max-h-48 object-contain rounded">
              <div class="absolute bottom-2 right-2 text-[9px] bg-black/60 text-white px-2 py-0.5 rounded-full backdrop-blur-xs flex items-center space-x-1 pointer-events-none">
                <i class="fa-solid fa-magnifying-glass-plus"></i>
                <span>点击全屏查看大图</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 题干卡片 -->
        <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 space-y-2">
          <div class="font-bold text-slate-900 text-sm leading-relaxed whitespace-pre-wrap">
            {{ currentItem.stem || `第 ${currentItem.q_num} 题：请从下列选项中选出最符合题意的一项。` }}
          </div>

          <!-- 题干配图 -->
          <div v-if="currentItem.stem_images && currentItem.stem_images.length > 0" class="space-y-2 pt-1">
            <div
              v-for="(imgUrl, idx) in currentItem.stem_images"
              :key="idx"
              class="rounded-xl overflow-hidden border border-slate-200 bg-white p-1 cursor-zoom-in relative group"
              @click="modalStore.openFullscreen(imgUrl)"
            >
              <img :src="imgUrl" alt="题干图" class="w-full h-auto max-h-52 object-contain rounded">
            </div>
          </div>
        </div>

        <!-- 四选项卡片 -->
        <div class="space-y-2">
          <div
            v-for="opt in ['A', 'B', 'C', 'D']"
            :key="opt"
            :class="getOptionClass(opt)"
          >
            <div class="flex items-start justify-between">
              <div class="flex items-start space-x-2">
                <span :class="getOptionBadgeClass(opt)">
                  {{ opt }}
                </span>
                <span class="leading-relaxed">{{ currentItem.options?.[opt] || `选项 ${opt}` }}</span>
              </div>
              <span v-if="opt === currentItem.standard_choice" class="shrink-0 px-1.5 py-0.2 rounded bg-emerald-600 text-white font-bold text-[10px]">
                标准正解 ✓
              </span>
              <span v-else-if="opt === currentItem.student_choice" class="shrink-0 px-1.5 py-0.2 rounded bg-rose-600 text-white font-bold text-[10px]">
                考生错选 ✗
              </span>
            </div>
          </div>
        </div>

        <!-- 单题改选纠偏卡片 (如果是在出分结果页查看) -->
        <div v-if="omrStore.resultData" class="bg-blue-50/70 border border-blue-200/80 rounded-xl p-3 space-y-2">
          <div class="flex items-center justify-between">
            <div class="font-bold text-blue-900 text-xs flex items-center space-x-1.5">
              <i class="fa-solid fa-pen-to-square text-blue-600"></i>
              <span>在线改选填涂纠偏</span>
            </div>
            <div class="text-[11px] text-blue-800">
              当前识别: <b>{{ curWorkingChoice || '未填' }}</b>
            </div>
          </div>
          <div class="flex items-center space-x-1.5 pt-1">
            <button
              v-for="opt in ['A', 'B', 'C', 'D']"
              :key="opt"
              type="button"
              @click="omrStore.setCorrectionAnswer(currentItem.q_num, opt)"
              :class="curWorkingChoice === opt ? 'w-8 h-8 rounded-lg font-black text-xs bg-blue-600 text-white shadow-xs scale-105 transition' : 'w-8 h-8 rounded-lg font-bold text-xs bg-white border border-slate-300 text-slate-700 hover:bg-blue-50 hover:border-blue-400 transition'"
            >
              {{ opt }}
            </button>
            <button
              type="button"
              @click="omrStore.setCorrectionAnswer(currentItem.q_num, null)"
              class="px-2 h-8 rounded-lg font-medium text-[11px] bg-white border border-slate-300 text-slate-600 hover:bg-rose-50 hover:text-rose-600 transition"
            >
              清空
            </button>
          </div>
        </div>

        <!-- 试卷官方参考解析 (折叠) -->
        <div class="border border-slate-200 rounded-xl overflow-hidden">
          <button
            type="button"
            @click="showAnalysis = !showAnalysis"
            class="w-full p-2.5 bg-slate-50 hover:bg-slate-100 flex items-center justify-between text-xs font-bold text-slate-700 transition"
          >
            <div class="flex items-center space-x-1.5">
              <i class="fa-solid fa-lightbulb text-amber-500"></i>
              <span>官方参考解析</span>
            </div>
            <i :class="showAnalysis ? 'fa-solid fa-chevron-up text-[10px]' : 'fa-solid fa-chevron-down text-[10px]'"></i>
          </button>
          <div v-show="showAnalysis" class="p-3 bg-white text-[11px] text-slate-600 leading-relaxed border-t border-slate-100 whitespace-pre-wrap">
            {{ currentItem.analysis || '暂无官方详细解析，可点击下方【💡 问名师秒杀解法】由 AI 导师一键剖析。' }}
          </div>
        </div>
      </div>

      <!-- 底部操作与切题栏 -->
      <div class="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between shrink-0">
        <button
          type="button"
          @click="prevQ"
          :disabled="modalStore.currentQuestionNum <= 1"
          class="px-3 py-1.5 bg-white hover:bg-slate-100 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold transition disabled:opacity-40"
        >
          <i class="fa-solid fa-chevron-left mr-1"></i> 上一题
        </button>

        <button
          type="button"
          @click="askAiTutor"
          class="px-3.5 py-1.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold rounded-xl text-xs transition shadow-xs flex items-center space-x-1"
        >
          <i class="fa-solid fa-graduation-cap text-[11px]"></i>
          <span>💡 问名师秒杀</span>
        </button>

        <button
          type="button"
          @click="nextQ"
          :disabled="modalStore.currentQuestionNum >= maxQ"
          class="px-3 py-1.5 bg-white hover:bg-slate-100 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold transition disabled:opacity-40"
        >
          下一题 <i class="fa-solid fa-chevron-right ml-1"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useModalStore } from '../../stores/modal';
import { useOmrStore } from '../../stores/omr';
import { renderStructuredMaterialHtml } from '../../utils/materialFormatter';

const modalStore = useModalStore();
const omrStore = useOmrStore();

const showMaterialText = ref(true);
const showAnalysis = ref(false);

const currentItem = computed(() => {
  const qNum = modalStore.currentQuestionNum;
  const items = omrStore.resultData?.items || [];
  const found = items.find(it => it.q_num === qNum);
  if (found) return found;

  return {
    q_num: qNum,
    section_name: '客观选择题',
    score_per_q: 1.0,
    student_choice: omrStore.onlineAnswers[qNum] || '',
    standard_choice: 'A',
    stem: `第 ${qNum} 题：请从下列选项中选出最符合题意的一项。`,
    options: { A: '选项 A', B: '选项 B', C: '选项 C', D: '选项 D' },
    analysis: '官方解析'
  };
});

const maxQ = computed(() => {
  return omrStore.resultData?.summary?.total_questions || omrStore.totalQuestions || 135;
});

const curWorkingChoice = computed(() => {
  return omrStore.workingStudentAnswers[modalStore.currentQuestionNum] || null;
});

const itemStatus = computed(() => {
  const it = currentItem.value;
  const stu = (it.student_choice || '').trim().toUpperCase();
  const std = (it.standard_choice || '').trim().toUpperCase();
  if (!stu || stu === 'NULL') return 'unanswered';
  if (stu === std) return 'correct';
  return 'wrong';
});

const hasMaterial = computed(() => {
  const it = currentItem.value;
  return Boolean(it.material?.trim() || (it.material_images && it.material_images.length > 0));
});

const materialHtml = computed(() => {
  return renderStructuredMaterialHtml(currentItem.value.material || '', false);
});

function getOptionClass(opt) {
  const std = currentItem.value.standard_choice;
  const stu = currentItem.value.student_choice;
  if (opt === std) {
    return 'p-2.5 rounded-xl border bg-emerald-50/90 border-emerald-400 text-emerald-950 font-medium shadow-2xs';
  }
  if (opt === stu) {
    return 'p-2.5 rounded-xl border bg-rose-50/90 border-rose-400 text-rose-950 font-medium shadow-2xs';
  }
  return 'p-2.5 rounded-xl border bg-white border-slate-200 text-slate-700';
}

function getOptionBadgeClass(opt) {
  const std = currentItem.value.standard_choice;
  const stu = currentItem.value.student_choice;
  if (opt === std) return 'w-5 h-5 rounded-full bg-emerald-600 text-white font-bold text-xs flex items-center justify-center shrink-0';
  if (opt === stu) return 'w-5 h-5 rounded-full bg-rose-600 text-white font-bold text-xs flex items-center justify-center shrink-0';
  return 'w-5 h-5 rounded-full bg-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center shrink-0';
}

function prevQ() {
  if (modalStore.currentQuestionNum > 1) {
    modalStore.currentQuestionNum--;
  }
}

function nextQ() {
  if (modalStore.currentQuestionNum < maxQ.value) {
    modalStore.currentQuestionNum++;
  }
}

function askAiTutor() {
  const it = currentItem.value;
  modalStore.closeQuestion();
  modalStore.openAiTutor('omr', it);
}
</script>
