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
import { ref, computed, watch } from 'vue';
import { useModalStore } from '../../stores/modal';
import { useTutorStore } from '../../stores/tutor';
import { useConfigStore } from '../../stores/config';

const modalStore = useModalStore();
const tutorStore = useTutorStore();
const configStore = useConfigStore();

const userQuery = ref('');

const isMath = computed(() => modalStore.aiTutorContext?.type === 'math');
const qInfo = computed(() => modalStore.aiTutorContext?.questionData || {});

watch(() => modalStore.isAiTutorOpen, (open) => {
  if (open && modalStore.aiTutorContext) {
    if (!configStore.isConfigured) {
      modalStore.closeAiTutor();
      modalStore.openSettings();
      alert('⚠️ 请先在右上角【设置】中配置个人 Base URL 与 API Key (BYOK)！');
      return;
    }
    userQuery.value = '';
    tutorStore.askTutor(modalStore.aiTutorContext.type, modalStore.aiTutorContext.questionData);
  }
});

function handleQuery() {
  if (!userQuery.value.trim()) return;
  tutorStore.askTutor(modalStore.aiTutorContext.type, modalStore.aiTutorContext.questionData, userQuery.value.trim());
}
</script>
