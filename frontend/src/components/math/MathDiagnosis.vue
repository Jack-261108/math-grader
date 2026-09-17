<template>
  <div v-if="hasDiagnosis" class="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-3">
    <div class="flex items-center justify-between border-b border-slate-100 pb-2.5">
      <div class="flex items-center space-x-2">
        <div class="w-6 h-6 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs">
          <i class="fa-solid fa-chart-simple"></i>
        </div>
        <h3 class="font-bold text-slate-800 text-sm">智能学情诊断画像</h3>
      </div>
      <span class="text-[11px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
        {{ speedBadgeText }}
      </span>
    </div>

    <!-- 主要失分短板与即时针对强化横幅 -->
    <div class="bg-rose-50/70 border border-rose-100 rounded-xl p-3.5 text-xs space-y-2.5">
      <div class="flex items-center justify-between">
        <div class="font-bold text-rose-800 flex items-center">
          <i class="fa-solid fa-triangle-exclamation mr-1.5 text-rose-500"></i>
          <span>核心薄弱短板</span>
        </div>
        <span v-if="primaryErrorType" class="text-[10px] px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 font-bold">
          系统已精准锁定题型
        </span>
      </div>
      <p class="text-rose-900 leading-relaxed font-medium">{{ diagnosis?.primary_weakness || '表现优异，无明显计算短板！' }}</p>
      <p class="text-rose-700 text-[11px]">{{ diagnosis?.speed_advice || '用时稳定。' }}</p>

      <!-- 🎯 速算自适应强化练一键启动横幅 -->
      <div class="pt-1">
        <button
          type="button"
          @click="startAdaptivePractice(primaryErrorType, diagnosis?.primary_weakness)"
          class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-indigo-600 hover:from-emerald-500 hover:to-indigo-500 text-white font-black text-xs shadow-md transition flex items-center justify-center space-x-2 active:scale-98 cursor-pointer"
        >
          <i class="fa-solid fa-wand-magic-sparkles text-amber-300 text-sm"></i>
          <span>🎯 针对该薄弱短板：立即生成 20 道同型算式强化突破</span>
          <i class="fa-solid fa-arrow-right text-[10px]"></i>
        </button>
      </div>
    </div>

    <!-- 失分题型分布标签 -->
    <div v-if="diagnosis?.error_breakdown && diagnosis.error_breakdown.length > 0" class="space-y-1.5">
      <div class="text-[11px] font-bold text-slate-500 flex items-center justify-between">
        <span>失分题型归因分布 (点击可单独针对练 20 题):</span>
        <span class="text-[10px] text-slate-400">点击标签专项突破</span>
      </div>
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="err in diagnosis.error_breakdown"
          :key="err.name"
          type="button"
          @click="startAdaptivePractice(err.error_type || err.name, err.name)"
          class="inline-flex items-center px-2.5 py-1 rounded-full bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 font-medium text-[11px] transition cursor-pointer group shadow-2xs"
          :title="`针对【${err.name}】即时生成 20 道同型算式突破`"
        >
          <span>{{ err.name }}</span>
          <span class="ml-1 px-1 py-0.2 bg-rose-200/80 rounded-full text-[10px] font-bold text-rose-900">{{ err.count }}</span>
          <i class="fa-solid fa-crosshairs text-[9px] text-rose-400 group-hover:text-rose-600 ml-1"></i>
        </button>
      </div>
    </div>

    <!-- 针对性提分建议锦囊 -->
    <div v-if="diagnosis?.actionable_tips && diagnosis.actionable_tips.length > 0" class="bg-amber-50/80 border border-amber-200/60 rounded-xl p-3 text-xs space-y-1.5">
      <div class="font-bold text-amber-900 text-xs flex items-center space-x-1.5">
        <i class="fa-solid fa-lightbulb text-amber-600"></i>
        <span>名师避坑锦囊</span>
      </div>
      <ul class="space-y-1.5 text-[11px] text-amber-800 list-disc list-inside">
        <li v-for="(tip, idx) in diagnosis.actionable_tips" :key="idx">{{ tip }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useModalStore } from '../../stores/modal';

const props = defineProps({
  diagnosis: {
    type: Object,
    default: () => ({})
  }
});

const modalStore = useModalStore();

const hasDiagnosis = computed(() => {
  return Boolean(props.diagnosis?.primary_weakness || props.diagnosis?.actionable_tips);
});

const primaryErrorType = computed(() => {
  const bd = props.diagnosis?.error_breakdown;
  if (bd && bd.length > 0) {
    return bd[0].error_type || bd[0].name;
  }
  const pw = props.diagnosis?.primary_weakness || '';
  if (pw.includes('借位') || pw.includes('退位') || pw.includes('减法')) return 'borrow_error';
  if (pw.includes('除法') || pw.includes('截位') || pw.includes('直除')) return 'division_truncate';
  if (pw.includes('进位') || pw.includes('加法')) return 'carry_error';
  if (pw.includes('乘法') || pw.includes('尾数')) return 'multiplication';
  if (pw.includes('负号') || pw.includes('负数')) return 'missing_negative';
  return 'borrow_error';
});

function startAdaptivePractice(errType, errName) {
  modalStore.openTargetedPractice(errType || 'borrow_error', errName || '针对薄弱短板');
}

const speedBadgeText = computed(() => {
  const d = props.diagnosis;
  if (!d) return '标准节奏';
  if (d.sec_per_item && d.sec_per_item > 0) {
    return `${d.speed_level || '标准'} (${d.sec_per_item}s/题)`;
  }
  return d.speed_level || '标准节奏';
});
</script>
