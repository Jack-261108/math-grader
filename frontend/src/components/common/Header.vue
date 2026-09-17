<template>
  <header class="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200 px-3 sm:px-6 py-3 shadow-xs w-full overflow-hidden">
    <div class="max-w-md md:max-w-3xl lg:max-w-4xl w-full mx-auto flex items-center justify-between min-w-0">
      <div class="flex items-center space-x-2">
        <div class="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-xs">
          <i class="fa-solid fa-graduation-cap text-base"></i>
        </div>
        <div>
          <h1 class="font-bold text-base text-slate-900 tracking-tight leading-tight">公考智能批改系统</h1>
          <p class="text-[11px] text-slate-500">速算批注 · 行测答题卡 · 智能诊断</p>
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <span
          @click="modalStore.openSettings"
          :class="configStore.isConfigured
            ? 'inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-100 text-emerald-800 cursor-pointer hover:bg-emerald-200 transition'
            : 'inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-rose-100 text-rose-800 border border-rose-200 cursor-pointer hover:bg-rose-200 transition animate-pulse'"
          :title="configStore.isConfigured ? '已配置个人 API Key 与 Base URL，点击修改' : '未配置个人 API Key 与 Base URL，点击进行配置'"
        >
          <span :class="configStore.isConfigured ? 'w-1.5 h-1.5 mr-1 bg-emerald-500 rounded-full animate-pulse' : 'w-1.5 h-1.5 mr-1 bg-rose-600 rounded-full'"></span>
          {{ configStore.isConfigured ? '自定义Key已就绪' : '未配置Key (点击配置)' }}
        </span>

        <button
          type="button"
          @click="openWrongBook"
          class="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 active:bg-slate-300 flex items-center justify-center text-slate-600 transition relative cursor-pointer"
          title="错题知识库与艾宾浩斯复习"
        >
          <i class="fa-solid fa-book-bookmark text-sm text-purple-600"></i>
          <span
            v-if="wrongBookStore.todayDueCount > 0"
            class="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-rose-500 text-white font-black text-[9px] flex items-center justify-center border-2 border-white"
          >
            {{ wrongBookStore.todayDueCount > 9 ? '9+' : wrongBookStore.todayDueCount }}
          </span>
        </button>

        <button
          type="button"
          @click="modalStore.openHistory"
          class="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 active:bg-slate-300 flex items-center justify-center text-slate-600 transition cursor-pointer"
          title="查看判题历史记录"
        >
          <i class="fa-solid fa-clock-rotate-left text-sm text-blue-600"></i>
        </button>

        <button
          type="button"
          @click="modalStore.openSettings"
          class="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 active:bg-slate-300 flex items-center justify-center text-slate-600 transition"
          title="配置 API Key"
        >
          <i class="fa-solid fa-gear text-sm"></i>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useConfigStore } from '../../stores/config';
import { useModalStore } from '../../stores/modal';
import { useWrongBookStore } from '../../stores/wrongbook';
import { useRouter } from 'vue-router';

const configStore = useConfigStore();
const modalStore = useModalStore();
const wrongBookStore = useWrongBookStore();
const router = useRouter();

function openWrongBook() {
  router.replace({ path: '/', query: { mode: 'wrongbook' } });
}
</script>
