<template>
  <section class="space-y-4">
    <!-- ⏱️ 速算沉浸式计时控制台卡片 -->
    <div class="bg-white rounded-2xl p-4 border border-slate-200/90 shadow-2xs space-y-3.5">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span
            :class="[
              'w-2.5 h-2.5 rounded-full transition-all',
              mathStore.timerStatus === 'running'
                ? 'bg-emerald-500 animate-ping'
                : (mathStore.timerStatus === 'paused' ? 'bg-amber-500' : 'bg-emerald-600')
            ]"
          ></span>
          <h3 class="font-bold text-slate-800 text-sm flex items-center space-x-1.5">
            <span>⏱️ 速算刷题实战计时器</span>
            <span
              v-if="mathStore.timerStatus === 'running'"
              class="text-[10px] px-1.5 py-0.2 rounded-full font-bold bg-emerald-100 text-emerald-700"
            >
              计时专注中
            </span>
            <span
              v-else-if="mathStore.timerStatus === 'paused'"
              class="text-[10px] px-1.5 py-0.2 rounded-full font-bold bg-amber-100 text-amber-700"
            >
              已暂停
            </span>
            <span
              v-else-if="mathStore.timerStatus === 'finished'"
              class="text-[10px] px-1.5 py-0.2 rounded-full font-bold bg-blue-100 text-blue-700"
            >
              做题已完成
            </span>
          </h3>
        </div>

        <!-- 计时模式切换 (秒表 vs 倒计时) -->
        <div class="flex bg-slate-100 p-0.5 rounded-xl text-xs font-semibold">
          <button
            type="button"
            @click="switchTimerMode('stopwatch')"
            :class="mathStore.timerMode === 'stopwatch' ? 'py-1 px-2.5 rounded-lg bg-white shadow-xs text-slate-800 transition font-bold' : 'py-1 px-2.5 rounded-lg text-slate-500 hover:text-slate-800 transition'"
          >
            正向秒表
          </button>
          <button
            type="button"
            @click="switchTimerMode('countdown')"
            :class="mathStore.timerMode === 'countdown' ? 'py-1 px-2.5 rounded-lg bg-white shadow-xs text-slate-800 transition font-bold' : 'py-1 px-2.5 rounded-lg text-slate-500 hover:text-slate-800 transition'"
          >
            限时挑战
          </button>
        </div>
      </div>

      <!-- 大字数码时钟显示区 -->
      <div
        :class="[
          'rounded-2xl p-4 border transition-all duration-300 text-center relative overflow-hidden',
          mathStore.isCountdownCritical
            ? 'bg-gradient-to-br from-rose-50 via-red-50 to-amber-50 border-rose-300 ring-2 ring-rose-400/40 text-rose-900'
            : (mathStore.timerStatus === 'running'
              ? 'bg-gradient-to-br from-emerald-950 via-slate-900 to-teal-950 text-white border-emerald-700 shadow-sm'
              : 'bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 text-white border-slate-700 shadow-sm')
        ]"
      >
        <div class="text-[11px] font-medium tracking-wide flex items-center justify-center space-x-1.5 mb-1 opacity-80">
          <i class="fa-regular fa-clock text-xs"></i>
          <span>{{ mathStore.timerMode === 'countdown' ? (mathStore.isCountdownCritical ? '🚨 倒计时即将结束' : '限时倒计时目标') : '刷题累计用时秒表' }}</span>
        </div>

        <!-- 数码时间 -->
        <div
          :class="[
            'font-mono font-black text-4xl sm:text-5xl tracking-widest my-1 select-none',
            mathStore.isCountdownCritical ? 'text-rose-600 animate-pulse' : 'text-white'
          ]"
        >
          {{ mathStore.formattedTimer }}
        </div>

        <!-- 倒计时模式下的时长配置胶囊 (仅未开始时显示) -->
        <div
          v-if="mathStore.timerMode === 'countdown' && mathStore.timerStatus === 'idle'"
          class="flex items-center justify-center space-x-1.5 mt-2 flex-wrap gap-y-1"
        >
          <span class="text-[11px] text-slate-300 mr-1">目标时长:</span>
          <button
            v-for="mins in [10, 15, 20, 25, 30]"
            :key="mins"
            type="button"
            @click="mathStore.setCountdownMinutes(mins)"
            :class="[
              'px-2 py-0.5 rounded-lg text-xs font-semibold transition cursor-pointer',
              mathStore.countdownTargetMinutes === mins
                ? 'bg-emerald-500 text-white shadow-xs font-bold'
                : 'bg-white/10 hover:bg-white/20 text-slate-200'
            ]"
          >
            {{ mins }}分钟
          </button>
        </div>

        <!-- 控制器按钮 -->
        <div class="flex items-center justify-center space-x-2 mt-3.5">
          <!-- 未开始状态 -->
          <template v-if="mathStore.timerStatus === 'idle'">
            <button
              type="button"
              @click="mathStore.startTimer"
              class="px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold text-xs shadow-md transition flex items-center space-x-1.5 active:scale-95 cursor-pointer"
            >
              <i class="fa-solid fa-play text-xs"></i>
              <span>开始速算计时</span>
            </button>
          </template>

          <!-- 进行中状态 -->
          <template v-else-if="mathStore.timerStatus === 'running'">
            <button
              type="button"
              @click="mathStore.pauseTimer"
              class="px-3.5 py-2 rounded-xl bg-white/20 hover:bg-white/30 text-white font-bold text-xs transition flex items-center space-x-1.5 active:scale-95 cursor-pointer"
            >
              <i class="fa-solid fa-pause text-xs"></i>
              <span>暂停</span>
            </button>
            <button
              type="button"
              @click="handleFinishPractice"
              class="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-bold text-xs shadow-md transition flex items-center space-x-1.5 active:scale-95 cursor-pointer"
            >
              <i class="fa-solid fa-check text-xs"></i>
              <span>⏹ 完成做题，准备批改</span>
            </button>
          </template>

          <!-- 暂停状态 -->
          <template v-else-if="mathStore.timerStatus === 'paused'">
            <button
              type="button"
              @click="mathStore.resumeTimer"
              class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow transition flex items-center space-x-1.5 active:scale-95 cursor-pointer"
            >
              <i class="fa-solid fa-play text-xs"></i>
              <span>继续做题</span>
            </button>
            <button
              type="button"
              @click="handleFinishPractice"
              class="px-3.5 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs shadow transition flex items-center space-x-1.5 active:scale-95 cursor-pointer"
            >
              <i class="fa-solid fa-check text-xs"></i>
              <span>完成做题</span>
            </button>
            <button
              type="button"
              @click="mathStore.resetTimer"
              class="px-2.5 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-slate-200 font-medium text-xs transition flex items-center space-x-1 cursor-pointer"
            >
              <i class="fa-solid fa-arrows-rotate text-[10px]"></i>
              <span>重置</span>
            </button>
          </template>

          <!-- 已完成状态 -->
          <template v-else-if="mathStore.timerStatus === 'finished'">
            <button
              type="button"
              @click="triggerCamera"
              class="px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-bold text-xs shadow-md transition flex items-center space-x-1.5 active:scale-95 cursor-pointer animate-bounce"
            >
              <i class="fa-solid fa-camera text-xs"></i>
              <span>📸 立即拍照批改</span>
            </button>
            <button
              type="button"
              @click="mathStore.resetTimer"
              class="px-3 py-2 rounded-xl bg-white/15 hover:bg-white/25 text-white font-medium text-xs transition flex items-center space-x-1 cursor-pointer"
            >
              <i class="fa-solid fa-arrows-rotate text-[10px]"></i>
              <span>再练一次</span>
            </button>
          </template>
        </div>
      </div>

      <!-- 用时微调条 -->
      <div class="flex items-center justify-between text-xs text-slate-500 pt-1">
        <span class="flex items-center space-x-1">
          <i class="fa-regular fa-clock text-emerald-600"></i>
          <span>当前记录完成用时:</span>
          <b class="text-slate-800 font-mono">{{ mathStore.timeStr }}</b>
        </span>
        <div class="flex items-center space-x-1">
          <span class="text-[11px] text-slate-400">手动微调:</span>
          <input
            type="text"
            v-model="mathStore.timeStr"
            placeholder="如 18分30秒"
            class="border border-slate-200 rounded-lg px-2 py-0.5 w-24 text-center text-xs font-mono text-slate-700 focus:outline-none focus:border-emerald-500"
          >
        </div>
      </div>
    </div>

    <!-- 📸 拍照与上传交互横幅卡片 -->
    <div class="bg-gradient-to-br from-emerald-600 to-teal-700 rounded-2xl p-5 text-white shadow-md relative overflow-hidden space-y-4">
      <div class="relative z-10 space-y-3">
        <div>
          <h2 class="text-xl font-bold mb-1">对准练习册，一键拍照批改</h2>
          <p class="text-emerald-100 text-xs leading-relaxed">
            自动校正拍摄倾斜与透视，智能辨识手写笔迹并红绿勾叉标注，自动统计正确率、速度评级与名师学情诊断。
          </p>
        </div>

        <!-- 双按钮：拍照与相册选择 -->
        <div class="grid grid-cols-2 gap-2.5">
          <button
            type="button"
            @click="triggerCamera"
            class="flex items-center justify-center space-x-2 bg-white text-emerald-800 hover:bg-emerald-50 active:scale-98 transition font-bold py-3 px-3 rounded-xl shadow text-sm cursor-pointer"
          >
            <i class="fa-solid fa-camera text-base text-emerald-600"></i>
            <span>拍照批改</span>
          </button>
          <button
            type="button"
            @click="triggerAlbum"
            class="flex items-center justify-center space-x-2 bg-emerald-800/40 hover:bg-emerald-800/60 active:scale-98 transition font-medium text-white border border-white/20 py-3 px-3 rounded-xl text-sm cursor-pointer"
          >
            <i class="fa-solid fa-image text-base"></i>
            <span>相册选取</span>
          </button>
        </div>
      </div>

      <!-- 装饰背景 -->
      <i class="fa-solid fa-square-check absolute right-1 bottom-1 text-7xl text-white/10 pointer-events-none"></i>
    </div>

    <!-- 隐藏的文件选择器 -->
    <input ref="cameraInput" type="file" accept="image/*" capture="environment" class="hidden" @change="handleFileChange">
    <input ref="albumInput" type="file" accept="image/*" class="hidden" @change="handleFileChange">

    <!-- 💡 公考行测速算实战配速黄金标准标尺卡片 -->
    <div class="bg-white rounded-xl p-4 border border-slate-200/80 shadow-2xs space-y-2.5 text-xs">
      <div class="flex items-center justify-between border-b border-slate-100 pb-2">
        <h3 class="font-bold text-slate-800 flex items-center space-x-1.5">
          <i class="fa-solid fa-gauge-high text-emerald-600"></i>
          <span>公考行测速算黄金速度标尺 (资料分析必背)</span>
        </h3>
        <span class="text-[10px] text-slate-400">名师实战经验</span>
      </div>

      <div class="grid grid-cols-3 gap-2 text-center text-[11px]">
        <div class="p-2 rounded-xl bg-slate-50 border border-slate-200/70">
          <div class="text-slate-400 text-[10px]">三位数加减法</div>
          <div class="font-bold text-emerald-700 mt-0.5">≤ 8 秒/题</div>
          <div class="text-[9px] text-slate-400 mt-0.5">高位直加直减</div>
        </div>
        <div class="p-2 rounded-xl bg-slate-50 border border-slate-200/70">
          <div class="text-slate-400 text-[10px]">两位数乘法</div>
          <div class="font-bold text-blue-700 mt-0.5">≤ 12 秒/题</div>
          <div class="text-[9px] text-slate-400 mt-0.5">拆分乘与尾数法</div>
        </div>
        <div class="p-2 rounded-xl bg-slate-50 border border-slate-200/70">
          <div class="text-slate-400 text-[10px]">多位数截位除</div>
          <div class="font-bold text-amber-700 mt-0.5">≤ 18 秒/题</div>
          <div class="text-[9px] text-slate-400 mt-0.5">保留三位直除</div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue';
import { useMathStore } from '../../stores/math';
import { useRouter } from 'vue-router';

const mathStore = useMathStore();
const router = useRouter();

const cameraInput = ref(null);
const albumInput = ref(null);

function switchTimerMode(mode) {
  if (mathStore.timerStatus === 'running') {
    if (!confirm('计时正在进行中，切换模式将重置当前计时，确定要切换吗？')) return;
  }
  mathStore.resetTimer();
  mathStore.timerMode = mode;
}

function handleFinishPractice() {
  mathStore.stopTimer();
}

function triggerCamera() {
  cameraInput.value?.click();
}

function triggerAlbum() {
  albumInput.value?.click();
}

async function handleFileChange(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  try {
    const data = await mathStore.submitGrade(file);
    if (data?.task_id) {
      router.replace({ path: '/', query: { mode: 'math', task_id: data.task_id } });
    }
  } catch (err) {
    alert(err.message || '批改失败');
  } finally {
    e.target.value = '';
  }
}
</script>
