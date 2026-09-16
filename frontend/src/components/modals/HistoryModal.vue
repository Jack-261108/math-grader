<template>
  <div
    v-if="modalStore.isHistoryOpen"
    class="fixed inset-0 z-[65] bg-black/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200"
    @click.self="modalStore.closeHistory"
  >
    <div class="bg-white rounded-2xl max-w-xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden relative">
      <!-- 弹窗头部 -->
      <div class="px-4 py-3 bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white flex items-center justify-between shrink-0">
        <div class="flex items-center space-x-2.5">
          <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-xs">
            <i class="fa-solid fa-clock-rotate-left text-sm"></i>
          </div>
          <div>
            <h3 class="text-sm font-bold text-white leading-tight">判题历史记录</h3>
            <p class="text-[10px] text-slate-300">一键回溯全卷诊断、电子答题卡与批改底图</p>
          </div>
        </div>
        <div class="flex items-center space-x-1.5">
          <button
            type="button"
            @click="historyStore.fetchList"
            class="w-7 h-7 rounded-full text-slate-300 hover:text-white hover:bg-white/15 flex items-center justify-center transition"
            title="刷新历史列表"
          >
            <i class="fa-solid fa-arrows-rotate text-xs"></i>
          </button>
          <button
            type="button"
            @click="modalStore.closeHistory"
            class="w-7 h-7 rounded-full text-slate-300 hover:text-white hover:bg-white/15 flex items-center justify-center transition"
            title="关闭"
          >
            <i class="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>
      </div>

      <!-- 分类过滤与计数 Tab -->
      <div class="px-4 py-2.5 bg-slate-50 border-b border-slate-200/80 flex items-center justify-between shrink-0 gap-2">
        <div class="flex bg-slate-200/90 p-0.5 rounded-xl text-xs font-semibold flex-1 max-w-xs">
          <button
            type="button"
            @click="historyStore.filterType = 'all'"
            :class="historyStore.filterType === 'all' ? 'flex-1 py-1.5 rounded-lg bg-white text-slate-900 shadow-2xs font-bold transition text-center' : 'flex-1 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition text-center'"
          >
            全部
          </button>
          <button
            type="button"
            @click="historyStore.filterType = 'omr'"
            :class="historyStore.filterType === 'omr' ? 'flex-1 py-1.5 rounded-lg bg-white text-slate-900 shadow-2xs font-bold transition text-center' : 'flex-1 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition text-center'"
          >
            行测答题卡
          </button>
          <button
            type="button"
            @click="historyStore.filterType = 'math'"
            :class="historyStore.filterType === 'math' ? 'flex-1 py-1.5 rounded-lg bg-white text-slate-900 shadow-2xs font-bold transition text-center' : 'flex-1 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition text-center'"
          >
            速算练习册
          </button>
        </div>
        <span class="text-[11px] font-bold text-slate-500 bg-white border border-slate-200/90 px-2.5 py-1 rounded-full shrink-0">
          共 {{ historyStore.filteredRecords.length }} 条
        </span>
      </div>

      <!-- 历史记录可滚动列表区 -->
      <div class="flex-1 overflow-y-auto p-3.5 sm:p-4 space-y-3 bg-slate-100/50">
        <div v-if="historyStore.isLoading" class="py-14 text-center space-y-3">
          <div class="w-10 h-10 mx-auto rounded-full border-3 border-blue-200 border-t-blue-600 animate-spin"></div>
          <p class="text-xs text-slate-500 font-medium">正在读取历史判题记录...</p>
        </div>

        <div v-else-if="historyStore.filteredRecords.length === 0" class="py-14 text-center space-y-3">
          <div class="w-14 h-14 mx-auto rounded-2xl bg-white border border-slate-200/80 flex items-center justify-center text-slate-300 shadow-2xs">
            <i class="fa-solid fa-folder-open text-2xl"></i>
          </div>
          <div class="text-xs font-bold text-slate-600">
            暂无{{ historyStore.filterType === 'omr' ? '行测答题卡' : (historyStore.filterType === 'math' ? '速算练习册' : '') }}判题历史
          </div>
          <p class="text-[11px] text-slate-400 max-w-xs mx-auto">当您完成拍照批改或在线答题判卷后，报告将自动归档于此，随时可一键回溯。</p>
        </div>

        <div
          v-else
          v-for="rec in historyStore.filteredRecords"
          :key="rec.task_id"
          class="bg-white border border-slate-200/80 hover:border-blue-300 rounded-2xl p-3.5 shadow-2xs hover:shadow-xs transition space-y-2.5 relative group cursor-pointer"
          @click="handleRestore(rec)"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center space-x-1.5 flex-wrap gap-y-1">
              <span v-if="rec.type === 'omr'" class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                <i class="fa-solid fa-table-cells-large mr-1 text-[9px]"></i>行测答题卡
              </span>
              <span v-else class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <i class="fa-solid fa-calculator mr-1 text-[9px]"></i>速算练习册
              </span>

              <span class="text-[11px] text-slate-400 flex items-center space-x-1 font-mono">
                <i class="fa-regular fa-clock text-[10px]"></i>
                <span>{{ rec.created_at || '刚刚' }}</span>
              </span>
            </div>
            <button
              type="button"
              @click.stop="handleDelete(rec.task_id)"
              class="text-slate-300 hover:text-rose-600 active:text-rose-700 p-1 transition"
              title="删除此记录"
            >
              <i class="fa-regular fa-trash-can text-xs"></i>
            </button>
          </div>

          <div class="flex items-center gap-3">
            <div
              v-if="rec.img_url"
              class="w-14 h-14 sm:w-16 sm:h-16 rounded-xl overflow-hidden border border-slate-200 bg-slate-50 shrink-0 cursor-zoom-in"
              @click.stop="modalStore.openFullscreen(rec.img_url)"
              title="点击查看批注大图"
            >
              <img :src="rec.img_url" alt="批注卡" class="w-full h-full object-cover object-top hover:scale-105 transition duration-200">
            </div>

            <div class="flex-1 min-w-0">
              <h4 class="text-xs font-bold text-slate-900 truncate leading-snug" :title="rec.title">{{ rec.title }}</h4>
              <div class="mt-1 flex items-baseline space-x-2">
                <span :class="rec.type === 'omr' ? 'text-base font-black text-blue-700 tracking-tight' : 'text-base font-black text-emerald-700 tracking-tight'">
                  {{ rec.score_str || `${rec.score_val} 分` }}
                </span>
                <span :class="rec.grade === 'A+' || rec.grade === '优秀' ? 'text-[10px] px-1.5 py-0.2 rounded font-black bg-emerald-100 text-emerald-800' : 'text-[10px] px-1.5 py-0.2 rounded font-black bg-blue-100 text-blue-800'">
                  评级 {{ rec.grade }}
                </span>
              </div>
              <div class="mt-1.5 flex items-center space-x-2 text-[10px] text-slate-500">
                <span class="text-emerald-600 font-semibold"><i class="fa-solid fa-circle-check text-[9px] mr-0.5"></i>对 {{ rec.correct_q }}</span>
                <span class="text-rose-600 font-semibold"><i class="fa-solid fa-circle-xmark text-[9px] mr-0.5"></i>错 {{ rec.wrong_q }}</span>
                <span v-if="rec.type === 'omr'" class="text-slate-400 font-medium"><i class="fa-solid fa-circle-minus text-[9px] mr-0.5"></i>未填 {{ rec.unans_q || 0 }}</span>
              </div>
            </div>
          </div>

          <div class="pt-2 border-t border-slate-100 flex items-center justify-end">
            <button
              type="button"
              class="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-blue-600 active:bg-blue-700 text-white text-xs font-bold transition flex items-center space-x-1.5 shadow-2xs group-hover:bg-blue-600"
            >
              <i class="fa-solid fa-arrow-rotate-left text-[10px]"></i>
              <span>查看报告并回溯还原</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { watch } from 'vue';
import { useHistoryStore } from '../../stores/history';
import { useModalStore } from '../../stores/modal';
import { useMathStore } from '../../stores/math';
import { useOmrStore } from '../../stores/omr';
import { useRouter } from 'vue-router';

const historyStore = useHistoryStore();
const modalStore = useModalStore();
const mathStore = useMathStore();
const omrStore = useOmrStore();
const router = useRouter();

watch(() => modalStore.isHistoryOpen, (open) => {
  if (open) {
    historyStore.fetchList();
  }
});

async function handleRestore(rec) {
  modalStore.closeHistory();
  if (rec.type === 'omr') {
    router.replace({ path: '/', query: { mode: 'omr', task_id: rec.task_id } });
    await omrStore.restoreTask(rec.task_id);
  } else {
    router.replace({ path: '/', query: { mode: 'math', task_id: rec.task_id } });
    await mathStore.restoreTask(rec.task_id);
  }
}

async function handleDelete(taskId) {
  if (!confirm('确定要删除这条判题记录吗？关联的诊断报告及批注卡底图文件也将被彻底清理。')) {
    return;
  }
  try {
    await historyStore.deleteRecord(taskId);
  } catch (err) {
    alert('删除记录失败: ' + err.message);
  }
}
</script>
