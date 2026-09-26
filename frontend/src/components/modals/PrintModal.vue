<template>
  <div
    v-if="modalStore.isPrintModalOpen"
    id="printModal"
    class="fixed inset-0 z-[80] bg-black/75 backdrop-blur-sm flex flex-col justify-between overflow-y-auto p-2 sm:p-6 select-text"
  >
    <!-- 顶部操作栏 (打印时不显示) -->
    <div class="no-print max-w-4xl w-full mx-auto bg-slate-900 text-white p-4 rounded-2xl flex flex-wrap items-center justify-between gap-3 shadow-2xl mb-4 border border-slate-700">
      <div class="flex items-center space-x-2">
        <div class="w-8 h-8 rounded-lg bg-emerald-500 text-white flex items-center justify-center font-bold">
          <i class="fa-solid fa-print"></i>
        </div>
        <div>
          <h3 class="text-sm font-bold">A4 错题本与自测重刷排版导出</h3>
          <p class="text-[11px] text-slate-400">标准 A4 纸张排版，自动适配打印机、PDF 导出与分页</p>
        </div>
      </div>

      <div class="flex items-center space-x-2">
        <div class="flex bg-slate-800 p-1 rounded-lg text-xs">
          <button
            type="button"
            @click="printView = 'clean'"
            :class="printView === 'clean' ? 'px-3 py-1 rounded-md font-medium transition bg-emerald-600 text-white shadow-xs flex items-center space-x-1' : 'px-3 py-1 rounded-md font-medium transition text-slate-300 hover:text-white flex items-center space-x-1'"
          >
            <i class="fa-solid fa-file-pen text-xs"></i>
            <span>纯净空白重刷卷</span>
          </button>
          <button
            type="button"
            @click="printView = 'review'"
            :class="printView === 'review' ? 'px-3 py-1 rounded-md font-medium transition bg-blue-600 text-white shadow-xs flex items-center space-x-1' : 'px-3 py-1 rounded-md font-medium transition text-slate-300 hover:text-white flex items-center space-x-1'"
          >
            <i class="fa-solid fa-clipboard-check text-xs"></i>
            <span>错题复盘解析版</span>
          </button>
        </div>

        <button
          type="button"
          @click="triggerPrint"
          class="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center space-x-1.5"
        >
          <i class="fa-solid fa-print"></i>
          <span>一键打印 / 存为 PDF</span>
        </button>

        <button
          type="button"
          @click="modalStore.closePrint"
          class="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white flex items-center justify-center transition text-sm"
          title="关闭"
        >
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>
    </div>

    <!-- A4 纸张预览内容区 -->
    <div id="printSheetContent" class="a4-sheet bg-white my-auto">
      <div class="border-b-2 border-slate-900 pb-4 mb-6">
        <div class="text-center space-y-1">
          <h1 class="text-xl sm:text-2xl font-black tracking-wide text-slate-900">{{ examName }}</h1>
          <div class="text-sm font-bold text-slate-700">{{ subTitle }}</div>
        </div>
        <div class="mt-4 flex flex-wrap items-center justify-between text-xs text-slate-600 border-t border-dashed border-slate-300 pt-3">
          <div>姓名：<span class="inline-block border-b border-slate-800 w-24"></span></div>
          <div>自测日期：<span class="font-medium">{{ todayStr }}</span></div>
          <div>重做得分：<span class="inline-block border-b border-slate-800 w-16 text-center"></span> / 100</div>
        </div>
        <div class="mt-2 text-[11px] text-slate-500 bg-slate-50 p-2 rounded border border-slate-200">
          {{ summaryTips }}
        </div>
      </div>

      <!-- 针对性弱项强化练习组卷排版 (当 modalStore.printSource === 'targeted_sheet') -->
      <div v-if="isTargetedSheet">
        <div v-if="targetedSheetItems.length === 0" class="text-center py-12 text-slate-400 font-bold text-base">
          暂无自适应强化练习题数据，请在速算诊断画像中生成后打印。
        </div>

        <!-- 针对性弱项空白重做卷 -->
        <div v-else-if="printView === 'clean'" class="space-y-4">
          <div
            v-for="(it, idx) in targetedSheetItems"
            :key="it.db_question_id || idx"
            class="print-avoid-break p-3.5 border-2 border-slate-300 rounded-xl bg-white space-y-2"
          >
            <div class="flex items-center justify-between border-b border-slate-200 pb-1.5">
              <div class="flex items-center space-x-2">
                <span class="w-6 h-6 rounded-full bg-purple-700 text-white font-black text-xs flex items-center justify-center font-mono">
                  {{ idx + 1 }}
                </span>
                <span class="font-bold text-xs text-slate-800">{{ it.topic_category }}</span>
                <span class="text-[10px] text-slate-400">({{ it.module_name }})</span>
              </div>
              <span class="text-[10px] font-bold text-slate-400">分值: {{ it.score_per_q || 1.0 }}分</span>
            </div>

            <!-- 速算题算式 -->
            <div v-if="it.expression" class="py-2">
              <div class="text-lg font-extrabold text-slate-900 tracking-wide font-mono">
                {{ it.expression }} = <span class="inline-block border-2 border-slate-800 w-28 h-7 align-middle ml-1 rounded"></span>
              </div>
              <div class="h-12 border border-dashed border-slate-200 rounded p-1.5 text-[9px] text-slate-300 mt-2">
                草稿速算演算区:
              </div>
            </div>

            <!-- 行测题选择题 -->
            <div v-else class="space-y-2">
              <div v-if="it.material" class="bg-slate-50 border-l-2 border-slate-400 p-2 text-[10px] text-slate-600 leading-relaxed mb-1.5" v-html="renderStructuredMaterialHtml(it.material)"></div>
              <div class="text-xs font-bold text-slate-900 leading-relaxed whitespace-pre-wrap">{{ it.stem }}</div>
              <div v-if="it.options && Object.keys(it.options).length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-800 pt-1 font-serif">
                <div v-for="(v, k) in it.options" :key="k">
                  <b>{{ k }}.</b> {{ v }}
                </div>
              </div>
              <div class="h-10 border border-dashed border-slate-200 rounded p-1 text-[9px] text-slate-300">
                草稿与代入排除标记区:
              </div>
            </div>
          </div>
        </div>

        <!-- 针对性弱项复盘解析版 -->
        <div v-else class="space-y-3.5">
          <div
            v-for="(it, idx) in targetedSheetItems"
            :key="it.db_question_id || idx"
            class="print-avoid-break p-3.5 border border-slate-300 rounded-xl bg-slate-50/80 space-y-2"
          >
            <div class="flex items-center justify-between border-b border-slate-200 pb-1.5">
              <div class="flex items-center space-x-2">
                <span class="px-2 py-0.5 rounded bg-purple-700 text-white font-bold text-xs">#{{ idx + 1 }}</span>
                <span class="font-bold text-sm text-slate-800">{{ it.topic_category }}</span>
              </div>
              <div class="text-xs">
                <span class="text-slate-400 line-through mr-2">上次作答: {{ it.user_last_answer || '未填' }}</span>
                <span class="text-emerald-700 font-black text-sm">标准答案: {{ it.expected_answer }}</span>
              </div>
            </div>

            <div class="bg-white p-2.5 rounded-lg border border-slate-200 space-y-1.5 text-xs text-slate-800">
              <div v-if="it.expression" class="font-mono font-bold text-base">{{ it.expression }} = {{ it.expected_answer }}</div>
              <div v-else class="font-bold">{{ it.stem }}</div>
              <div v-if="it.advice" class="text-[11px] text-purple-900 bg-purple-50 p-2 rounded leading-relaxed">
                <b class="text-purple-700">【名师秒杀解题要诀】：</b>{{ it.advice }}
              </div>
              <div v-if="it.diagnosis" class="text-[11px] text-slate-500">
                <b>【典型错因诊断】：</b>{{ it.diagnosis }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 速算错题排版 -->
      <div v-else-if="isMath">
        <div v-if="mathWrongItems.length === 0" class="text-center py-12 text-emerald-600 font-bold text-base">
          🎉 恭喜！本次速算全对无任何错题，无需重做！
        </div>

        <!-- 速算空白重刷版 -->
        <div v-else-if="printView === 'clean'" class="grid grid-cols-2 gap-4">
          <div
            v-for="(it, idx) in mathWrongItems"
            :key="idx"
            class="print-avoid-break p-3.5 border-2 border-slate-300 rounded-xl bg-white space-y-2"
          >
            <div class="flex items-center justify-between">
              <span class="font-black text-xs text-slate-700">第 {{ idx + 1 }} 题</span>
              <span class="text-[10px] text-slate-400 font-mono">第{{ it.row_num }}行·第{{ it.col_idx }}列</span>
            </div>
            <div class="text-base font-extrabold text-slate-900 tracking-wide font-mono py-1">
              {{ it.expression }} = <span class="inline-block border-2 border-slate-800 w-24 h-7 align-middle ml-1 rounded"></span>
            </div>
            <div class="h-14 border border-dashed border-slate-200 rounded p-1.5 text-[9px] text-slate-300">
              草稿演算区:
            </div>
          </div>
        </div>

        <!-- 速算复盘解析版 -->
        <div v-else class="space-y-3">
          <div
            v-for="(it, idx) in mathWrongItems"
            :key="idx"
            class="print-avoid-break p-3.5 border border-slate-300 rounded-xl bg-slate-50/50 space-y-2"
          >
            <div class="flex items-center justify-between border-b border-slate-200 pb-1.5">
              <div class="flex items-center space-x-2">
                <span class="px-2 py-0.5 rounded bg-rose-600 text-white font-bold text-xs">#{{ idx + 1 }}</span>
                <span class="font-bold text-sm text-slate-900 font-mono">{{ it.expression }}</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 font-semibold">{{ it.error_name || '计算偏差' }}</span>
              </div>
              <div class="text-xs">
                <span class="text-slate-400 line-through mr-2">考生作答: {{ it.student_raw || '未填写' }}</span>
                <span class="text-emerald-700 font-black">正确标准答案: {{ it.expected }}</span>
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-slate-700">
              <div class="bg-white p-2 rounded border border-rose-100">
                <b class="text-rose-600">【错因诊断】:</b> {{ it.diagnosis || '步长估算或进退位偏差' }}
              </div>
              <div class="bg-white p-2 rounded border border-emerald-100">
                <b class="text-emerald-600">【速算秒杀技巧】:</b> {{ it.advice || '建议采用拆分法或截位直除，先定首位再做微调' }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 行测 OMR 错题排版 -->
      <div v-else>
        <div v-if="omrWrongItems.length === 0" class="text-center py-12 text-emerald-600 font-bold text-base">
          🎉 恭喜！本卷答题卡全部选对，满分通过！
        </div>

        <!-- 行测空白重刷版 -->
        <div v-else-if="printView === 'clean'" class="space-y-4">
          <div
            v-for="it in omrWrongItems"
            :key="it.q_num"
            class="print-avoid-break p-3.5 border-2 border-slate-300 rounded-xl bg-white space-y-2"
          >
            <div class="flex items-center justify-between border-b border-slate-200 pb-1.5">
              <div class="flex items-center space-x-2">
                <span class="w-6 h-6 rounded-full bg-slate-900 text-white font-black text-xs flex items-center justify-center">
                  {{ it.q_num }}
                </span>
                <span class="font-bold text-xs text-slate-800">{{ it.section_name }}</span>
                <span class="text-[10px] text-slate-400">单题分值: {{ it.score_per_q }}分</span>
              </div>
              <div class="flex items-center space-x-2 text-xs font-bold font-mono">
                <span class="px-1.5 py-0.5 border border-slate-400 rounded-md">[ A ]</span>
                <span class="px-1.5 py-0.5 border border-slate-400 rounded-md">[ B ]</span>
                <span class="px-1.5 py-0.5 border border-slate-400 rounded-md">[ C ]</span>
                <span class="px-1.5 py-0.5 border border-slate-400 rounded-md">[ D ]</span>
              </div>
            </div>

            <div v-if="it.material" class="bg-slate-50 border-l-2 border-slate-400 p-2 text-[10px] text-slate-600 leading-relaxed mb-1.5" v-html="renderStructuredMaterialHtml(it.material)"></div>

            <div class="text-xs font-bold text-slate-900 leading-relaxed whitespace-pre-wrap">
              {{ it.stem || `第 ${it.q_num} 题：请从下列选项中选出最符合题意的一项。` }}
            </div>

            <div v-if="it.stem_images && it.stem_images.length > 0" class="space-y-1 my-1.5">
              <img v-for="(u, idx) in it.stem_images" :key="idx" :src="u" alt="题干图" class="max-h-44 object-contain rounded border border-slate-300 print-avoid-break">
            </div>

            <div v-if="it.options" class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-800 pt-1 font-serif">
              <div v-for="k in ['A', 'B', 'C', 'D']" :key="k">
                <b>{{ k }}.</b> {{ it.options[k] || '' }}
              </div>
            </div>

            <div class="h-10 border border-dashed border-slate-200 rounded p-1 text-[9px] text-slate-300">
              草稿演算与排除标记区:
            </div>
          </div>
        </div>

        <!-- 行测复盘解析版 -->
        <div v-else class="space-y-3.5">
          <div
            v-for="it in omrWrongItems"
            :key="it.q_num"
            class="print-avoid-break p-3.5 border border-slate-300 rounded-xl bg-slate-50/80 space-y-2"
          >
            <div class="flex items-center justify-between border-b border-slate-200 pb-1.5">
              <div class="flex items-center space-x-2">
                <span class="w-6 h-6 rounded-full bg-rose-600 text-white font-bold text-xs flex items-center justify-center">
                  {{ it.q_num }}
                </span>
                <span class="font-bold text-sm text-slate-800">{{ it.section_name }}</span>
                <span class="text-xs text-slate-500">({{ it.score_per_q }}分)</span>
              </div>
              <div class="text-xs">
                <span class="text-slate-400 line-through mr-2">考生作答: {{ it.student_choice || '未作答' }}</span>
                <span class="text-emerald-700 font-black text-sm">标准答案: {{ it.standard_choice }}</span>
              </div>
            </div>

            <div class="bg-white p-2.5 rounded-lg border border-slate-200 space-y-1.5">
              <div v-if="it.material" class="bg-amber-50/70 border-l-2 border-amber-400 p-2 text-[10px] text-slate-600 leading-relaxed mb-1 rounded-r" v-html="renderStructuredMaterialHtml(it.material)"></div>
              <div class="text-xs font-bold text-slate-900 leading-relaxed">{{ it.stem || `第 ${it.q_num} 题：请从下列选项中选出最符合题意的一项。` }}</div>
              <div v-if="it.stem_images && it.stem_images.length > 0" class="space-y-1 my-1.5">
                <img v-for="(u, idx) in it.stem_images" :key="idx" :src="u" alt="题干配图" class="max-h-44 object-contain rounded border border-slate-200 print-avoid-break">
              </div>
              <div v-if="it.options" class="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-xs pt-1">
                <div
                  v-for="k in ['A', 'B', 'C', 'D']"
                  :key="k"
                  :class="k === it.standard_choice ? 'text-emerald-700 font-bold' : (k === it.student_choice ? 'text-rose-600 line-through' : 'text-slate-700')"
                >
                  <b>{{ k }}.</b> {{ it.options[k] || '' }}
                  <span v-if="k === it.standard_choice" class="text-[10px] font-bold"> ✓ (正解)</span>
                  <span v-else-if="k === it.student_choice" class="text-[10px] font-bold"> ✗ (错填)</span>
                </div>
              </div>
            </div>

            <div class="bg-white p-2.5 rounded-lg border border-slate-200 text-[11px] text-slate-700 leading-relaxed space-y-1">
              <div v-if="it.analysis"><b class="text-amber-700">【试卷官方参考解析】：</b><br><span class="text-slate-600 whitespace-pre-wrap">{{ it.analysis }}</span></div>
              <div><b class="text-blue-700">【模块破局与防坑要诀】：</b>在【{{ it.section_name }}】中，若错选【{{ it.student_choice }}】，多由于命题人设置了常考概念偷换或选项极性诱导。建议采用『代入排除』与『优先验证矛盾项』策略。</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useModalStore } from '../../stores/modal';
import { useMathStore } from '../../stores/math';
import { useOmrStore } from '../../stores/omr';
import { renderStructuredMaterialHtml } from '../../utils/materialFormatter';

const modalStore = useModalStore();
const mathStore = useMathStore();
const omrStore = useOmrStore();

const printView = ref('clean'); // 'clean' | 'review'

const isTargetedSheet = computed(() => modalStore.printSource === 'targeted_sheet' || modalStore.printSource === 'wrong_sheet');
const isMath = computed(() => modalStore.printSource === 'math');

const todayStr = computed(() => {
  return new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
});

const examName = computed(() => {
  if (isTargetedSheet.value) {
    return modalStore.targetedSheet?.title || '针对性薄弱考点自测提分卷';
  }
  if (isMath.value) {
    return mathStore.resultData?.title || '公考资料分析速算';
  }
  return omrStore.resultData?.exam_title || '公考行测模考';
});

const subTitle = computed(() => {
  return printView.value === 'clean' ? '【纯净空白重刷自测卷】' : '【错题复盘与名师解析版】';
});

const summaryTips = computed(() => {
  return printView.value === 'clean'
    ? '说明：请在规定时间内独立重做下列错题，养成良好心算与书写习惯，做完后可对照原卷复盘。'
    : '说明：每道错题已标注您的原错误答案与命题正解，附带错因分析与秒杀点拨，建议考前精细研读。';
});

const targetedSheetItems = computed(() => {
  return modalStore.targetedSheet?.items || [];
});

const mathWrongItems = computed(() => {
  return mathStore.resultData?.wrong_items || [];
});

const omrWrongItems = computed(() => {
  const items = omrStore.resultData?.items || [];
  return items.filter(it => it.status !== 'correct');
});

function triggerPrint() {
  window.print();
}
</script>
