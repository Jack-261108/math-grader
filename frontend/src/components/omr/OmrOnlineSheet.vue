<template>
  <div class="space-y-4">
    <!-- 🏛️ 全真模拟考场中控台与倒计时看板 -->
    <div class="bg-white rounded-2xl p-4 border border-slate-200/90 shadow-2xs space-y-3.5 relative overflow-hidden">
      <!-- 考场状态顶部栏 -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span
            :class="[
              'w-3 h-3 rounded-full flex items-center justify-center transition-all',
              omrStore.isTimeCritical ? 'bg-rose-500 animate-ping' : (omrStore.examTimerStatus === 'running' ? 'bg-emerald-500 animate-pulse' : 'bg-blue-600')
            ]"
          ></span>
          <h3 class="font-bold text-slate-800 text-sm flex items-center space-x-1.5">
            <span>🏛️ 行测全真模拟考场</span>
            <span
              v-if="omrStore.examTimerStatus === 'running'"
              class="text-[10px] px-1.5 py-0.2 rounded-full font-bold bg-emerald-100 text-emerald-700"
            >
              严格控时进行中
            </span>
            <span
              v-else-if="omrStore.examTimerStatus === 'paused'"
              class="text-[10px] px-1.5 py-0.2 rounded-full font-bold bg-amber-100 text-amber-700"
            >
              模考暂停中
            </span>
          </h3>
        </div>

        <div class="flex items-center space-x-2">
          <button
            type="button"
            @click="scrollToFirstUnanswered"
            class="text-[11px] text-blue-600 hover:text-blue-800 font-semibold bg-blue-50 hover:bg-blue-100 px-2 py-0.5 rounded-lg transition flex items-center space-x-1"
            title="平滑滚动聚焦到首道未作答题目"
          >
            <i class="fa-solid fa-crosshairs text-[10px]"></i>
            <span>定位未答</span>
          </button>
          <button
            type="button"
            @click="randomFill"
            class="text-[11px] text-slate-500 hover:text-blue-600 font-medium px-1.5 py-0.5"
          >
            随机填涂
          </button>
          <button
            type="button"
            @click="clearAll"
            class="text-[11px] text-slate-400 hover:text-rose-600 font-medium px-1.5 py-0.5"
          >
            清空
          </button>
        </div>
      </div>

      <!-- ⏱️ 考场倒计时数码看板 -->
      <div
        :class="[
          'rounded-2xl p-4 border transition-all duration-300 relative overflow-hidden',
          omrStore.isTimeCritical
            ? 'bg-gradient-to-br from-rose-50 via-red-50 to-amber-50 border-rose-300 ring-2 ring-rose-400/50'
            : (omrStore.isTimeWarning
              ? 'bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 border-amber-300'
              : 'bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 text-white border-slate-700 shadow-sm')
        ]"
      >
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <!-- 倒计时大字 -->
          <div>
            <div
              :class="[
                'text-[11px] font-bold flex items-center space-x-1.5',
                omrStore.isTimeCritical ? 'text-rose-600' : (omrStore.isTimeWarning ? 'text-amber-700' : 'text-slate-300')
              ]"
            >
              <i class="fa-regular fa-clock text-xs"></i>
              <span>{{ omrStore.isTimeCritical ? '🚨 考场紧急提醒：最后冲刺阶段' : (omrStore.isTimeWarning ? '⚠️ 考场提示：离考试结束还有不到15分钟' : '全卷实战倒计时') }}</span>
            </div>
            <div
              :class="[
                'font-mono font-black text-3xl sm:text-4xl tracking-wider mt-0.5 select-none',
                omrStore.isTimeCritical ? 'text-rose-600 animate-pulse' : (omrStore.isTimeWarning ? 'text-amber-800' : 'text-white')
              ]"
            >
              {{ omrStore.formattedTimeRemaining }}
            </div>
          </div>

          <!-- 控制器与时长切换 -->
          <div class="flex items-center space-x-2 flex-wrap gap-y-1.5">
            <!-- 未开始时：启动按钮与时长选择 -->
            <template v-if="omrStore.examTimerStatus === 'idle'">
              <div class="flex items-center space-x-1.5">
                <select
                  v-model.number="selectedMinutes"
                  class="bg-white/15 border border-white/20 rounded-xl px-2 py-1.5 text-xs text-white focus:outline-none focus:bg-slate-800"
                >
                  <option :value="120" class="text-slate-800">标准 120 分钟 (行测大纲)</option>
                  <option :value="90" class="text-slate-800">高压 90 分钟 (冲刺挑战)</option>
                  <option :value="60" class="text-slate-800">强化 60 分钟</option>
                  <option :value="30" class="text-slate-800">微模 30 分钟</option>
                  <option :value="15" class="text-slate-800">专项 15 分钟</option>
                </select>
                <button
                  type="button"
                  @click="handleStartExam"
                  class="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md transition flex items-center space-x-1 active:scale-95 cursor-pointer"
                >
                  <i class="fa-solid fa-play text-[11px]"></i>
                  <span>开始模考</span>
                </button>
              </div>
            </template>

            <!-- 进行中/暂停时：控制按钮 -->
            <template v-else>
              <button
                v-if="omrStore.examTimerStatus === 'running'"
                type="button"
                @click="omrStore.pauseMockExam"
                :class="[
                  'px-3 py-1.5 rounded-xl font-bold text-xs transition flex items-center space-x-1 active:scale-95 cursor-pointer',
                  omrStore.isTimeCritical || omrStore.isTimeWarning
                    ? 'bg-amber-600 hover:bg-amber-700 text-white'
                    : 'bg-white/20 hover:bg-white/30 text-white'
                ]"
              >
                <i class="fa-solid fa-pause text-[11px]"></i>
                <span>暂停计时</span>
              </button>

              <button
                v-else-if="omrStore.examTimerStatus === 'paused'"
                type="button"
                @click="omrStore.resumeMockExam"
                class="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow transition flex items-center space-x-1 active:scale-95 cursor-pointer"
              >
                <i class="fa-solid fa-play text-[11px]"></i>
                <span>继续模考</span>
              </button>

              <button
                type="button"
                @click="handleResetExam"
                :class="[
                  'px-2.5 py-1.5 rounded-xl font-medium text-xs transition flex items-center space-x-1 cursor-pointer',
                  omrStore.isTimeCritical || omrStore.isTimeWarning
                    ? 'bg-slate-200 hover:bg-slate-300 text-slate-700'
                    : 'bg-white/10 hover:bg-white/20 text-slate-200'
                ]"
                title="重新开始模考计时"
              >
                <i class="fa-solid fa-arrows-rotate text-[10px]"></i>
                <span>重置</span>
              </button>
            </template>
          </div>
        </div>

        <!-- 模考节奏看板信息 -->
        <div
          :class="[
            'mt-3 pt-2.5 border-t grid grid-cols-3 gap-2 text-center text-xs',
            omrStore.isTimeCritical
              ? 'border-rose-200 text-rose-800'
              : (omrStore.isTimeWarning ? 'border-amber-200 text-amber-900' : 'border-slate-700/80 text-slate-200')
          ]"
        >
          <div>
            <div class="text-[10px] opacity-75">已作答用时</div>
            <div class="font-mono font-bold text-xs mt-0.5">{{ omrStore.formattedTimeElapsed || '0秒' }}</div>
          </div>
          <div>
            <div class="text-[10px] opacity-75">当前平均配速</div>
            <div class="font-mono font-bold text-xs mt-0.5">
              {{ omrStore.averagePaceSeconds > 0 ? `${omrStore.averagePaceSeconds}秒/题` : '--' }}
            </div>
          </div>
          <div>
            <div class="text-[10px] opacity-75">考场配速诊断</div>
            <div class="font-bold text-[11px] mt-0.5">
              <span v-if="omrStore.averagePaceSeconds === 0">尚未开始</span>
              <span v-else-if="omrStore.averagePaceSeconds <= 50" class="text-emerald-400">🟢 极速快攻</span>
              <span v-else-if="omrStore.averagePaceSeconds <= 58" class="text-blue-400">🟢 黄金标准</span>
              <span v-else-if="omrStore.averagePaceSeconds <= 72" class="text-amber-400">🟡 略微偏慢</span>
              <span v-else class="text-rose-400 font-extrabold">🔴 严重超时</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 做题总进度条 -->
      <div class="space-y-1.5 pt-1">
        <div class="flex justify-between text-xs font-semibold">
          <span class="text-blue-700">全卷作答进度: {{ omrStore.answeredOnlineCount }} / {{ omrStore.totalQuestions }} 题 ({{ progressPct }}%)</span>
          <span :class="remainingCount === 0 ? 'font-bold text-emerald-600' : 'font-bold text-amber-600'">
            {{ remainingCount === 0 ? '🎉 全部选项已填涂完备' : `剩余 ${remainingCount} 题待作答` }}
          </span>
        </div>
        <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
          <div class="bg-blue-600 h-full transition-all duration-300" :style="{ width: `${progressPct}%` }"></div>
        </div>
      </div>
    </div>

    <!-- 模块分组气泡矩阵容器 -->
    <div class="space-y-3.5">
      <div
        v-for="(sec, sIdx) in omrStore.currentSections"
        :key="sIdx"
        class="bg-white rounded-2xl p-3.5 sm:p-4 border border-slate-200/90 shadow-2xs space-y-3"
      >
        <!-- 模块标题与建议用时控制条 -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-2.5 gap-2">
          <div class="flex items-center space-x-2 min-w-0">
            <span class="w-2.5 h-2.5 rounded-full bg-blue-600 shrink-0"></span>
            <h4 class="font-bold text-sm text-slate-800 truncate">{{ sec.name }}</h4>
            <span class="text-[11px] text-slate-400 font-medium shrink-0">
              ({{ sec.start_q }}~{{ sec.end_q }}题 · 单题{{ sec.score_per_q }}分)
            </span>
          </div>

          <!-- 模块用时监控条 -->
          <div class="flex items-center space-x-2 shrink-0 self-end sm:self-auto text-xs">
            <!-- 用时对比 -->
            <div class="flex items-center space-x-1 text-[11px] text-slate-500 bg-slate-50 px-2.5 py-1 rounded-xl border border-slate-200/80">
              <i class="fa-regular fa-stopwatch text-[10px] text-blue-600"></i>
              <span>用时: <b>{{ formatTimerSeconds(getSecActualSeconds(sec)) }}</b></span>
              <span class="text-slate-300">/</span>
              <span class="text-slate-400">建议 {{ Math.round(getSecRecommendedSeconds(sec) / 60) }}m</span>
              <!-- 节奏标签 -->
              <span
                :class="[
                  'ml-1 text-[10px] px-1.5 py-0.2 rounded font-bold border',
                  getSecPaceBadge(sec).class
                ]"
              >
                {{ getSecPaceBadge(sec).label }}
              </span>
            </div>

            <!-- 完成题数胶囊 -->
            <span class="text-[11px] font-bold px-2 py-1 rounded-xl bg-blue-50 text-blue-700 border border-blue-100 shrink-0">
              {{ getSecAnsweredCount(sec) }} / {{ sec.end_q - sec.start_q + 1 }} 题
            </span>
          </div>
        </div>

        <!-- ABCD 气泡阵列 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5">
          <div
            v-for="q in getQuestionsInRange(sec.start_q, sec.end_q)"
            :key="q"
            :id="`q-row-${q}`"
            :class="[
              'flex items-center justify-between px-3 py-2 rounded-xl transition min-w-0 border',
              omrStore.activeTrackingQ === q
                ? 'bg-blue-50/70 border-blue-300 ring-1 ring-blue-300/60 shadow-2xs'
                : 'bg-slate-50/80 border-slate-200/70 hover:bg-slate-100/70'
            ]"
            @click="omrStore.recordQuestionFocus(q)"
          >
            <!-- 题号与单题耗时展示 -->
            <div class="flex items-center space-x-1.5 shrink-0">
              <button
                type="button"
                @click.stop="modalStore.openQuestion(q)"
                class="min-w-[2.4rem] px-2 py-1 rounded-lg bg-white border border-slate-300 hover:border-blue-500 hover:bg-blue-50 text-slate-700 hover:text-blue-700 font-extrabold text-xs transition flex items-center justify-center space-x-1 shadow-2xs active:scale-95 cursor-pointer"
                :title="`点击查看第 ${q} 题题干与解析`"
              >
                <span>{{ q }}</span>
                <i class="fa-regular fa-file-lines text-[9px] text-slate-400"></i>
              </button>

              <!-- 单题耗时指示徽章 -->
              <span
                v-if="omrStore.questionTimes[q] > 0"
                class="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded-md bg-white border border-slate-200 text-slate-500"
                :title="`第 ${q} 题累计作答用时: ${omrStore.questionTimes[q]} 秒`"
              >
                {{ omrStore.questionTimes[q] }}s
              </span>
            </div>

            <!-- A B C D 气泡 -->
            <div class="flex items-center space-x-2 shrink-0">
              <button
                v-for="opt in ['A', 'B', 'C', 'D']"
                :key="opt"
                type="button"
                @click.stop="handleBubbleClick(q, opt)"
                :class="omrStore.onlineAnswers[q] === opt
                  ? 'w-8 h-8 rounded-full font-black text-xs transition-all duration-150 flex items-center justify-center cursor-pointer select-none bg-blue-600 border-2 border-blue-700 text-white shadow-xs scale-105 shrink-0'
                  : 'w-8 h-8 rounded-full font-bold text-xs transition-all duration-150 flex items-center justify-center cursor-pointer select-none bg-white border border-slate-300 text-slate-700 hover:border-blue-400 hover:bg-blue-50/60 shrink-0'"
              >
                {{ opt }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部提交答卷大按钮 -->
    <div class="pt-2 sticky bottom-4 z-20">
      <button
        type="button"
        @click="handleSubmit"
        class="w-full bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-700 hover:to-indigo-800 active:scale-98 text-white font-bold py-3.5 px-4 rounded-xl shadow-lg transition flex items-center justify-center space-x-2 text-sm cursor-pointer"
      >
        <i class="fa-solid fa-paper-plane text-xs"></i>
        <span>🚀 提交在线答卷 · 智能秒批 (已作答 {{ omrStore.answeredOnlineCount }} 题 · 用时 {{ omrStore.formattedTimeElapsed || '0秒' }})</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useOmrStore } from '../../stores/omr';
import { useModalStore } from '../../stores/modal';
import { useRouter } from 'vue-router';
import { getSectionBenchmark, formatTimerSeconds } from '../../constants/examTiming';

const omrStore = useOmrStore();
const modalStore = useModalStore();
const router = useRouter();

const selectedMinutes = ref(120);

const progressPct = computed(() => {
  const total = omrStore.totalQuestions;
  if (!total) return 0;
  return Math.round((omrStore.answeredOnlineCount / total) * 100);
});

const remainingCount = computed(() => {
  return Math.max(0, omrStore.totalQuestions - omrStore.answeredOnlineCount);
});

function getQuestionsInRange(start, end) {
  const arr = [];
  for (let i = start; i <= end; i++) arr.push(i);
  return arr;
}

function getSecAnsweredCount(sec) {
  let c = 0;
  for (let q = sec.start_q; q <= sec.end_q; q++) {
    if (omrStore.onlineAnswers[q]) c++;
  }
  return c;
}

function getSecActualSeconds(sec) {
  const secKey = sec.id || sec.name;
  return omrStore.sectionTimes[secKey] || 0;
}

function getSecRecommendedSeconds(sec) {
  const bench = getSectionBenchmark(sec.id, sec.name);
  const qCount = sec.end_q - sec.start_q + 1;
  return Math.round(bench.perQSec * qCount);
}

function getSecPaceBadge(sec) {
  const actual = getSecActualSeconds(sec);
  const rec = getSecRecommendedSeconds(sec);
  if (actual === 0) {
    return { label: '未耗时', class: 'text-slate-400 bg-slate-50 border-slate-200' };
  }
  if (actual <= rec * 1.05) {
    return { label: '节奏良好', class: 'text-emerald-700 bg-emerald-50 border-emerald-200' };
  }
  if (actual <= rec * 1.25) {
    return { label: '稍显滞后', class: 'text-amber-700 bg-amber-50 border-amber-200' };
  }
  return { label: '严重超时', class: 'text-rose-700 bg-rose-50 border-rose-200 font-extrabold' };
}

function handleStartExam() {
  omrStore.startMockExam(selectedMinutes.value);
}

function handleResetExam() {
  if (confirm('确定要重置当前模考倒计时与做题耗时记录吗？填涂的选项将予以保留。')) {
    omrStore.resetMockExam();
  }
}

function handleBubbleClick(qNum, opt) {
  if (omrStore.onlineAnswers[qNum] === opt) {
    omrStore.setOnlineAnswer(qNum, null);
  } else {
    omrStore.setOnlineAnswer(qNum, opt);
  }
}

function scrollToFirstUnanswered() {
  const total = omrStore.totalQuestions;
  for (let q = 1; q <= total; q++) {
    if (!omrStore.onlineAnswers[q]) {
      omrStore.recordQuestionFocus(q);
      const el = document.getElementById(`q-row-${q}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.add('ring-2', 'ring-blue-500');
        setTimeout(() => {
          el.classList.remove('ring-2', 'ring-blue-500');
        }, 1500);
      }
      return;
    }
  }
  alert('🎉 您已完成全卷所有题目的选项填涂！');
}

function randomFill() {
  const opts = ['A', 'B', 'C', 'D'];
  const total = omrStore.totalQuestions;
  for (let i = 1; i <= total; i++) {
    omrStore.setOnlineAnswer(i, opts[Math.floor(Math.random() * opts.length)]);
  }
}

function clearAll() {
  if (confirm('确定要清空当前所有在线填涂吗？')) {
    omrStore.onlineAnswers = {};
    omrStore.resetMockExam();
  }
}

async function handleSubmit() {
  try {
    const data = await omrStore.submitGradeFromOnline();
    if (data?.task_id) {
      router.replace({ path: '/', query: { mode: 'omr', task_id: data.task_id } });
    }
  } catch (err) {
    alert(err.message || '提交失败');
  }
}
</script>
