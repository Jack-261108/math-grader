<template>
  <div
    v-if="modalStore.isAiTutorOpen"
    class="fixed inset-0 z-[70] bg-black/60 backdrop-blur-xs flex items-center justify-center p-3 animate-in fade-in duration-200"
    @click.self="modalStore.closeAiTutor"
  >
    <div class="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden relative">
      <!-- 头部 -->
      <div class="px-4 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white flex items-center justify-between shrink-0">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center text-white">
            <i class="fa-solid fa-graduation-cap text-base"></i>
          </div>
          <div>
            <div class="text-[11px] font-semibold text-amber-100 uppercase tracking-wider">公考名师一对一复盘</div>
            <h3 class="text-sm font-bold text-white leading-tight">
              {{ isMath ? '资料分析速算 · 错题秒杀指导' : `行测 · 第 ${qInfo.q_num || 1} 题名师复盘` }}
            </h3>
          </div>
        </div>
        <button
          type="button"
          @click="modalStore.closeAiTutor"
          class="w-7 h-7 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center text-white transition"
        >
          <i class="fa-solid fa-xmark text-sm"></i>
        </button>
      </div>

      <!-- 内容可滚动区 -->
      <div class="flex-1 overflow-y-auto p-4 space-y-3.5 text-xs text-slate-700">
        <!-- 题目基础卡片 -->
        <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 flex items-center justify-between">
          <div>
            <span class="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-100 text-amber-800">
              {{ isMath ? (qInfo.error_name || '计算失误') : (qInfo.section_name || '行测客观题') }}
            </span>
            <div class="text-sm font-bold text-slate-800 mt-1">
              {{ isMath ? qInfo.expression : `第 ${qInfo.q_num} 题 (${qInfo.score_per_q || 1.0}分)` }}
            </div>
          </div>
          <div class="text-right">
            <div class="text-slate-400 line-through text-[11px]">
              {{ isMath ? `作答: ${qInfo.student_raw || '未填写'}` : `考生填涂: ${qInfo.student_choice || qInfo.student_ans || '未作答'}` }}
            </div>
            <div class="text-rose-600 font-bold text-sm">
              {{ isMath ? `正解: ${qInfo.expected}` : `参考正解: ${qInfo.standard_choice || qInfo.standard_ans || 'A'}` }}
            </div>
          </div>
        </div>

        <!-- 💡 公考速算与模块口诀知识库卡片 -->
        <div class="bg-gradient-to-br from-amber-50/80 via-orange-50/50 to-slate-50 border border-amber-200/90 rounded-2xl p-3 space-y-2.5 shadow-2xs">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-1.5 text-amber-900 font-bold text-xs">
              <span class="w-5 h-5 rounded-md bg-gradient-to-tr from-amber-500 to-orange-500 text-white flex items-center justify-center text-[10px] shadow-2xs">
                <i class="fa-solid fa-wand-magic-sparkles"></i>
              </span>
              <span>公考秒杀公式与口诀库</span>
            </div>
            <div class="text-[10px] text-amber-700/80 font-medium">
              {{ activeFormula ? '点击已选标签收起' : '点击标签展开推导与例题' }}
            </div>
          </div>

          <!-- 横向滑动快捷标签栏 -->
          <div class="flex items-center space-x-1.5 overflow-x-auto pb-1 -mx-0.5 px-0.5 text-[11px] scrollbar-none">
            <button
              v-for="formula in displayedFormulas"
              :key="formula.id"
              type="button"
              @click="toggleFormula(formula.id)"
              :class="[
                'shrink-0 px-2.5 py-1.5 rounded-xl transition flex items-center space-x-1.5 border select-none',
                activeFormulaId === formula.id
                  ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white font-bold border-amber-600 shadow-xs scale-102'
                  : 'bg-white/90 hover:bg-amber-100/60 text-slate-700 hover:text-amber-900 border-amber-200/70'
              ]"
            >
              <i :class="[formula.icon, 'text-[10px]', activeFormulaId === formula.id ? 'text-white' : 'text-amber-600']"></i>
              <span>{{ formula.shortName || formula.name }}</span>
            </button>
          </div>

          <!-- 激活公式展开卡片 (标准推导 + 典型例题) -->
          <div
            v-if="activeFormula"
            class="mt-1 bg-white border border-amber-300/80 rounded-xl p-3 space-y-3 shadow-xs animate-in fade-in slide-in-from-top-2 duration-150"
          >
            <!-- 卡片头部与标签 -->
            <div class="flex items-start justify-between border-b border-amber-100 pb-2">
              <div>
                <div class="flex items-center space-x-2">
                  <h4 class="font-bold text-slate-900 text-xs flex items-center space-x-1.5">
                    <span class="w-2 h-2 rounded-full bg-amber-500"></span>
                    <span>{{ activeFormula.name }}</span>
                  </h4>
                  <span
                    v-for="tag in activeFormula.tags"
                    :key="tag"
                    class="text-[9px] px-1.5 py-0.2 rounded-full bg-amber-100 text-amber-800 font-medium"
                  >
                    {{ tag }}
                  </span>
                </div>
              </div>
              <button
                type="button"
                @click="activeFormulaId = null"
                class="w-5 h-5 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 flex items-center justify-center transition text-[10px]"
                title="收起公式卡片"
              >
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>

            <!-- 核心口诀金句框 -->
            <div class="bg-gradient-to-r from-amber-50 via-orange-50 to-amber-100/60 border-l-3 border-amber-500 rounded-r-xl p-2.5 space-y-1">
              <div class="text-[10px] font-bold text-amber-800 flex items-center space-x-1">
                <i class="fa-solid fa-bolt text-amber-500"></i>
                <span>【核心秒杀口诀】</span>
              </div>
              <p class="font-bold text-amber-950 text-xs tracking-wide leading-relaxed">
                {{ activeFormula.jingle }}
              </p>
            </div>

            <!-- 标准推导与应用法则 -->
            <div class="space-y-1.5">
              <div class="text-[10px] font-bold text-slate-700 flex items-center space-x-1">
                <i class="fa-solid fa-square-root-variable text-blue-500"></i>
                <span>【标准数学推导与要领】</span>
              </div>
              <ul class="space-y-1 text-[11px] text-slate-600 bg-slate-50/80 rounded-xl p-2.5 border border-slate-100">
                <li
                  v-for="(step, idx) in activeFormula.derivation"
                  :key="idx"
                  class="leading-relaxed flex items-start space-x-1.5"
                >
                  <span class="text-amber-500 font-bold shrink-0">•</span>
                  <span>{{ step }}</span>
                </li>
              </ul>
            </div>

            <!-- 公考真题实战例题与秒杀示范 -->
            <div class="space-y-1.5">
              <div class="text-[10px] font-bold text-slate-700 flex items-center space-x-1">
                <i class="fa-solid fa-book-open-reader text-emerald-600"></i>
                <span>【公考真题经典例题】</span>
              </div>
              <div class="bg-emerald-50/50 border border-emerald-200/70 rounded-xl p-2.5 space-y-2 text-[11px]">
                <p class="text-slate-800 font-medium leading-relaxed">
                  {{ activeFormula.example.question }}
                </p>
                <div class="grid grid-cols-2 gap-1 text-[10px] text-slate-600">
                  <span v-for="opt in activeFormula.example.options" :key="opt">{{ opt }}</span>
                </div>
                <div class="pt-1.5 border-t border-emerald-200/60 flex items-start space-x-1.5 text-[11px] text-emerald-950 leading-relaxed">
                  <span class="px-1.5 py-0.5 rounded bg-emerald-600 text-white font-black text-[9px] shrink-0 mt-0.5">
                    正解 {{ activeFormula.example.answer }}
                  </span>
                  <span><b>名师秒杀：</b>{{ activeFormula.example.analysis }}</span>
                </div>
              </div>
            </div>

            <!-- 考场避坑要领 -->
            <div v-if="activeFormula.pitfalls" class="text-[10px] text-slate-500 flex items-start space-x-1 bg-slate-50 p-2 rounded-lg border border-slate-100">
              <i class="fa-solid fa-triangle-exclamation text-amber-500 shrink-0 mt-0.5"></i>
              <span><b>考场避坑：</b>{{ activeFormula.pitfalls }}</span>
            </div>

            <!-- 底部操作条：引用追问 & 复制口诀 -->
            <div class="flex items-center justify-end space-x-2 pt-1 border-t border-slate-100">
              <button
                type="button"
                @click="copyJingle(activeFormula)"
                class="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 text-[10px] font-medium transition flex items-center space-x-1"
              >
                <i :class="copiedJingleId === activeFormula.id ? 'fa-solid fa-check text-emerald-600' : 'fa-regular fa-copy'"></i>
                <span>{{ copiedJingleId === activeFormula.id ? '已复制口诀' : '复制口诀' }}</span>
              </button>
              <button
                type="button"
                @click="applyFormulaToQuery(activeFormula)"
                class="px-2.5 py-1 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white text-[10px] font-bold transition flex items-center space-x-1 shadow-2xs"
              >
                <i class="fa-solid fa-comment-dots"></i>
                <span>引用此公式追问</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 加载动画 -->
        <div v-if="tutorStore.isLoading" class="py-12 text-center space-y-3">
          <div class="w-9 h-9 mx-auto rounded-full border-3 border-amber-200 border-t-amber-500 animate-spin"></div>
          <div class="text-xs font-bold text-slate-700">名师正在为您梳理公考秒杀思路与错因剖析...</div>
          <p class="text-[11px] text-slate-400">调用大模型深度复盘本题核心设错陷阱与速算技巧</p>
        </div>

        <!-- 解析内容卡片 -->
        <div v-else-if="tutorStore.currentExplanation" class="space-y-3">
          <!-- 1. 错因剖析 -->
          <div class="p-3 rounded-xl bg-rose-50/70 border border-rose-200/80 space-y-1">
            <div class="font-bold text-rose-900 flex items-center space-x-1.5">
              <i class="fa-solid fa-crosshairs text-rose-600"></i>
              <span>【错因透视与设错陷阱】</span>
            </div>
            <p class="text-[11px] text-rose-950 leading-relaxed whitespace-pre-wrap">
              {{ tutorStore.currentExplanation.core_cause }}
            </p>
          </div>

          <!-- 2. 秒杀技巧 -->
          <div class="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200/80 space-y-1">
            <div class="font-bold text-emerald-900 flex items-center space-x-1.5">
              <i class="fa-solid fa-bolt text-emerald-600"></i>
              <span>【公考名师秒杀秘籍 & 心算步骤】</span>
            </div>
            <p class="text-[11px] text-emerald-950 leading-relaxed whitespace-pre-wrap">
              {{ tutorStore.currentExplanation.speed_tricks }}
            </p>
          </div>

          <!-- 3. 考场避坑 -->
          <div class="p-3 rounded-xl bg-blue-50/70 border border-blue-200/80 space-y-1">
            <div class="font-bold text-blue-900 flex items-center space-x-1.5">
              <i class="fa-solid fa-shield-halved text-blue-600"></i>
              <span>【实战考场避坑与选项差距研判】</span>
            </div>
            <p class="text-[11px] text-blue-950 leading-relaxed whitespace-pre-wrap">
              {{ tutorStore.currentExplanation.pitfall_tips }}
            </p>
          </div>

          <!-- 4. 名师寄语 -->
          <div class="p-3 rounded-xl bg-amber-50/70 border border-amber-200/80 text-[11px] text-amber-900 flex items-start space-x-2">
            <i class="fa-solid fa-quote-left text-amber-500 mt-0.5 shrink-0"></i>
            <span class="font-medium italic leading-relaxed">
              {{ tutorStore.currentExplanation.summary }}
            </span>
          </div>
        </div>
      </div>

      <!-- 底部追问输入栏 -->
      <div class="p-3 bg-slate-50 border-t border-slate-200 shrink-0">
        <div class="flex items-center space-x-2">
          <input
            ref="queryInputRef"
            type="text"
            v-model="userQuery"
            @keydown.enter="handleQuery"
            placeholder="对本题有疑问？输入问题追问名师 (如: '如何结合选项差距速算?')"
            class="flex-1 bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
          >
          <button
            type="button"
            @click="handleQuery"
            :disabled="tutorStore.isLoading"
            class="px-3.5 py-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold rounded-xl text-xs transition shadow-xs disabled:opacity-60 flex items-center space-x-1 shrink-0"
          >
            <i class="fa-solid fa-paper-plane text-[11px]"></i>
            <span>追问</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import { useModalStore } from '../../stores/modal';
import { useTutorStore } from '../../stores/tutor';
import { useConfigStore } from '../../stores/config';
import { FORMULA_LIST, getRecommendedFormulas } from '../../constants/formulas';

const modalStore = useModalStore();
const tutorStore = useTutorStore();
const configStore = useConfigStore();

const userQuery = ref('');
const queryInputRef = ref(null);
const activeFormulaId = ref(null);
const copiedJingleId = ref(null);

const isMath = computed(() => modalStore.aiTutorContext?.type === 'math');
const qInfo = computed(() => modalStore.aiTutorContext?.questionData || {});

// 根据错题上下文智能重排推荐公式
const displayedFormulas = computed(() => {
  return getRecommendedFormulas(modalStore.aiTutorContext || {});
});

const activeFormula = computed(() => {
  if (!activeFormulaId.value) return null;
  return FORMULA_LIST.find(f => f.id === activeFormulaId.value) || null;
});

function toggleFormula(id) {
  if (activeFormulaId.value === id) {
    activeFormulaId.value = null;
  } else {
    activeFormulaId.value = id;
  }
}

function applyFormulaToQuery(formula) {
  if (!formula) return;
  userQuery.value = `请问本题如何运用【${formula.name}】进行考场速算秒杀？`;
  nextTick(() => {
    if (queryInputRef.value) {
      queryInputRef.value.focus();
      queryInputRef.value.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  });
}

async function copyJingle(formula) {
  if (!formula || !formula.jingle) return;
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(`【${formula.name}口诀】：${formula.jingle}`);
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = `【${formula.name}口诀】：${formula.jingle}`;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
    copiedJingleId.value = formula.id;
    setTimeout(() => {
      if (copiedJingleId.value === formula.id) {
        copiedJingleId.value = null;
      }
    }, 2000);
  } catch (err) {
    console.error('复制口诀失败', err);
  }
}

watch(() => modalStore.isAiTutorOpen, (open) => {
  if (open && modalStore.aiTutorContext) {
    if (!configStore.isConfigured) {
      modalStore.closeAiTutor();
      modalStore.openSettings();
      alert('⚠️ 请先在右上角【设置】中配置个人 Base URL 与 API Key (BYOK)！');
      return;
    }
    userQuery.value = '';
    activeFormulaId.value = null;
    copiedJingleId.value = null;
    tutorStore.askTutor(modalStore.aiTutorContext.type, modalStore.aiTutorContext.questionData);
  }
});

function handleQuery() {
  if (!userQuery.value.trim()) return;
  tutorStore.askTutor(modalStore.aiTutorContext.type, modalStore.aiTutorContext.questionData, userQuery.value.trim());
}
</script>
