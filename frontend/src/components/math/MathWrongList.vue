<template>
  <div class="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-3">
    <div class="flex items-center justify-between border-b border-slate-100 pb-2.5">
      <div class="flex items-center space-x-2">
        <div class="w-6 h-6 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center text-xs">
          <i class="fa-solid fa-list-check"></i>
        </div>
        <h3 class="font-bold text-slate-800 text-sm">错题精细复盘</h3>
      </div>
      <span
        :class="wrongItems.length > 0 ? 'text-xs font-semibold px-2 py-0.5 rounded-full bg-rose-100 text-rose-700' : 'text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700'"
      >
        {{ wrongItems.length > 0 ? `${wrongItems.length} 题错误` : '全对满分' }}
      </span>
    </div>

    <!-- 全对提示 -->
    <div v-if="wrongItems.length === 0" class="py-6 text-center text-slate-500">
      <i class="fa-solid fa-champagne-glasses text-emerald-500 text-3xl mb-2"></i>
      <p class="text-xs font-medium">全卷无任何错题，正确率 100%！</p>
    </div>

    <!-- 错题列表 -->
    <div v-else class="space-y-2.5">
      <div
        v-for="(it, idx) in wrongItems"
        :key="idx"
        class="p-3 rounded-xl bg-slate-50 border border-slate-200/90 space-y-2 text-xs shadow-2xs"
      >
        <div class="flex items-center justify-between">
          <div class="space-y-0.5">
            <div class="flex items-center space-x-1.5">
              <span class="px-1.5 py-0.5 rounded bg-rose-600 text-white font-bold text-[10px]">#{{ idx + 1 }}</span>
              <span class="text-slate-500 font-medium text-[11px]">第 {{ it.row_num }} 行 · 第 {{ it.col_idx }} 列</span>
              <span class="px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 font-semibold text-[10px]">{{ it.error_name || '计算偏差' }}</span>
            </div>
            <div class="text-slate-800 font-bold text-sm pt-0.5 tracking-wide">{{ it.expression }}</div>
          </div>
          <div class="text-right">
            <div class="text-slate-400 line-through text-[11px]">作答: {{ it.student_raw || '未填写' }}</div>
            <div class="text-rose-600 font-bold text-sm">正解: {{ it.expected }}</div>
          </div>
        </div>

        <div v-if="it.diagnosis" class="bg-rose-50/80 rounded-lg p-2 text-[11px] text-rose-800 border border-rose-200/60 flex items-start space-x-1.5">
          <i class="fa-solid fa-circle-exclamation text-rose-500 mt-0.5 shrink-0"></i>
          <span class="leading-relaxed"><b>错因诊断</b>: {{ it.diagnosis }}</span>
        </div>

        <div v-if="it.advice" class="bg-amber-50/80 rounded-lg p-2 text-[11px] text-amber-900 border border-amber-200/60 flex items-start space-x-1.5">
          <i class="fa-regular fa-lightbulb text-amber-600 mt-0.5 shrink-0"></i>
          <span class="leading-relaxed"><b>提分建议</b>: {{ it.advice }}</span>
        </div>

        <div class="pt-1.5 flex justify-end">
          <button
            type="button"
            @click="modalStore.openAiTutor('math', it)"
            class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white transition flex items-center space-x-1 shadow-2xs active:scale-95"
          >
            <i class="fa-solid fa-graduation-cap text-[10px]"></i>
            <span>💡 问名师秒杀解法</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useModalStore } from '../../stores/modal';

defineProps({
  wrongItems: {
    type: Array,
    default: () => []
  }
});

const modalStore = useModalStore();
</script>
