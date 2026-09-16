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

    <!-- 主要失分短板 -->
    <div class="bg-rose-50/70 border border-rose-100 rounded-xl p-3 text-xs space-y-1">
      <div class="font-bold text-rose-800 flex items-center">
        <i class="fa-solid fa-triangle-exclamation mr-1.5 text-rose-500"></i>
        <span>核心薄弱短板</span>
      </div>
      <p class="text-rose-900 leading-relaxed">{{ diagnosis?.primary_weakness || '表现优异，无明显计算短板！' }}</p>
      <p class="text-rose-700 text-[11px] mt-0.5">{{ diagnosis?.speed_advice || '用时稳定。' }}</p>
    </div>

    <!-- 失分题型分布标签 -->
    <div v-if="diagnosis?.error_breakdown && diagnosis.error_breakdown.length > 0" class="space-y-1.5">
      <div class="text-[11px] font-bold text-slate-500">失分题型归因分布:</div>
      <div class="flex flex-wrap gap-1.5">
        <span
          v-for="err in diagnosis.error_breakdown"
          :key="err.name"
          class="inline-flex items-center px-2 py-0.5 rounded-full bg-rose-50 border border-rose-200 text-rose-700 font-medium text-[11px]"
        >
          {{ err.name }}
          <span class="ml-1 px-1 py-0.2 bg-rose-200/80 rounded-full text-[10px] font-bold text-rose-900">{{ err.count }}</span>
        </span>
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

const props = defineProps({
  diagnosis: {
    type: Object,
    default: () => ({})
  }
});

const hasDiagnosis = computed(() => {
  return Boolean(props.diagnosis?.primary_weakness || props.diagnosis?.actionable_tips);
});

const speedBadgeText = computed(() => {
  const d = props.diagnosis;
  if (!d) return '标准节奏';
  if (d.sec_per_item && d.sec_per_item > 0) {
    return `${d.speed_level || '标准'} (${d.sec_per_item}s/题)`;
  }
  return d.speed_level || '标准节奏';
});
</script>
