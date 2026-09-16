<template>
  <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden transition-all">
    <!-- 卡片头部触发条 -->
    <div
      @click="omrStore.isMatrixExpanded = !omrStore.isMatrixExpanded"
      class="p-3.5 sm:p-4 flex items-center justify-between cursor-pointer select-none hover:bg-slate-50/80 transition-colors group"
    >
      <div class="flex items-center space-x-2.5 min-w-0">
        <div class="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 border border-blue-200/60 flex items-center justify-center text-xs shrink-0 shadow-2xs group-hover:bg-blue-600 group-hover:text-white transition">
          <i class="fa-solid fa-table-cells"></i>
        </div>
        <div class="min-w-0">
          <div class="flex items-center space-x-2">
            <h4 class="font-bold text-xs sm:text-sm text-slate-800 truncate">电子答题卡涂点还原矩阵</h4>
            <span
              :class="omrStore.isMatrixExpanded ? 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200 shrink-0' : 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/80 shrink-0'"
            >
              {{ omrStore.isMatrixExpanded ? '点击收起' : `共 ${itemsCount} 题 · 点击展开` }}
            </span>
          </div>
          <p class="text-[11px] text-slate-400 truncate mt-0.5">全卷题号对错还原分布，支持点击题号查看试卷原题解析</p>
        </div>
      </div>
      <div class="flex items-center space-x-1.5 text-xs font-bold text-blue-600 shrink-0 pl-2">
        <span>{{ omrStore.isMatrixExpanded ? '收起答题卡' : '展开答题卡' }}</span>
        <i :class="omrStore.isMatrixExpanded ? 'fa-solid fa-chevron-up text-xs transition-transform group-hover:-translate-y-0.5' : 'fa-solid fa-chevron-down text-xs transition-transform group-hover:translate-y-0.5'"></i>
      </div>
    </div>

    <!-- 展开内容区 -->
    <div v-show="omrStore.isMatrixExpanded" class="p-3.5 sm:p-4 border-t border-slate-100 space-y-3 bg-slate-50/30">
      <!-- 头部图例 -->
      <div class="flex items-center justify-between pb-1 border-b border-slate-100">
        <span class="text-xs font-bold text-slate-700">涂点还原对错明细</span>
        <div class="flex items-center space-x-2.5 text-[10px] text-slate-500 font-medium">
          <span class="flex items-center"><span class="w-2.5 h-2.5 rounded bg-emerald-500 mr-1"></span>对</span>
          <span class="flex items-center"><span class="w-2.5 h-2.5 rounded bg-rose-500 mr-1"></span>错</span>
          <span class="flex items-center"><span class="w-2.5 h-2.5 rounded bg-white border border-slate-300 mr-1"></span>未填</span>
        </div>
      </div>

      <p class="text-[11px] text-slate-400">
        💡 点击下方单题色块可查看考生填涂与标准答案，支持在线快速纠偏改选并重新判分。
      </p>

      <!-- 浅色柔和答题卡面板 -->
      <div class="bg-slate-50/70 border border-slate-200/70 rounded-xl p-3 sm:p-3.5 max-h-[500px] overflow-y-auto matrix-scroll space-y-4">
        <div
          v-for="grp in sectionGroups"
          :key="grp.name"
          class="space-y-2"
        >
          <!-- 模块分类标题 -->
          <div class="text-slate-600 text-xs font-bold tracking-wide flex items-center space-x-1.5">
            <span class="w-1.5 h-3 rounded-full bg-blue-500"></span>
            <span>{{ grp.name }}</span>
            <span class="text-[10px] text-slate-400 font-normal ml-1">({{ grp.items.length }}题)</span>
          </div>

          <!-- 题号方块 -->
          <div class="flex flex-wrap gap-1.5 sm:gap-2">
            <button
              v-for="it in grp.items"
              :key="it.q_num"
              type="button"
              @click="modalStore.openQuestion(it.q_num)"
              :class="[
                'w-7 h-7 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center font-semibold text-xs transition-all duration-150 cursor-pointer select-none hover:scale-105 active:scale-95',
                getItemClass(it)
              ]"
              :title="`第 ${it.q_num} 题 [${grp.name}] · 点击查看原题解析`"
            >
              {{ it.q_num }}
            </button>
          </div>
        </div>
      </div>

      <!-- 底部收起按钮 -->
      <div class="pt-1 text-center">
        <button
          type="button"
          @click="omrStore.isMatrixExpanded = false"
          class="text-xs text-slate-400 hover:text-slate-600 font-medium inline-flex items-center space-x-1 py-1.5 px-3 rounded-lg hover:bg-slate-100 transition cursor-pointer"
        >
          <i class="fa-solid fa-chevron-up text-[10px]"></i>
          <span>收起矩阵</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useOmrStore } from '../../stores/omr';
import { useModalStore } from '../../stores/modal';

const omrStore = useOmrStore();
const modalStore = useModalStore();

const itemsCount = computed(() => {
  return omrStore.resultData?.items?.length || 0;
});

const sectionGroups = computed(() => {
  const items = omrStore.resultData?.items || [];
  const groups = [];
  const secMap = new Map();

  items.forEach(it => {
    const secName = it.section_name || '全部试题';
    if (!secMap.has(secName)) {
      const grp = { name: secName, items: [] };
      secMap.set(secName, grp);
      groups.push(grp);
    }
    secMap.get(secName).items.push(it);
  });

  return groups;
});

function getItemClass(it) {
  const stu = (it.student_choice || '').trim().toUpperCase();
  const std = (it.standard_choice || '').trim().toUpperCase();
  if (stu && stu === std) {
    return 'bg-emerald-500 text-white shadow-2xs hover:bg-emerald-600';
  }
  if (stu && stu !== std) {
    return 'bg-rose-500 text-white shadow-2xs hover:bg-rose-600';
  }
  return 'bg-white text-slate-400 border border-slate-200/90 shadow-2xs hover:bg-slate-50';
}
</script>
