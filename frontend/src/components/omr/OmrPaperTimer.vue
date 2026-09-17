<template>
  <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200/90 shadow-xs space-y-4 relative">
    <!-- 顶部中控台标题与考场功能开关 -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-1 border-b border-slate-100">
      <div class="flex items-center space-x-2.5">
        <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white flex items-center justify-center font-bold text-sm shadow-2xs">
          <i class="fa-regular fa-clock text-xs"></i>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <h3 class="font-bold text-slate-800 text-sm">🏛️ 行测全真纸质模考伴考中控台</h3>
            <span
              v-if="omrStore.examTimerStatus === 'running'"
              class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-700 flex items-center space-x-1 animate-pulse"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <span>纸质模考中</span>
            </span>
            <span
              v-else-if="omrStore.examTimerStatus === 'paused'"
              class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-amber-100 text-amber-700"
            >
              计时已暂停
            </span>
            <span
              v-else-if="omrStore.examTimerStatus === 'finished'"
              class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-blue-100 text-blue-700"
            >
              作答已完成
            </span>
          </div>
          <p class="text-[11px] text-slate-400 mt-0.5">
            手机/平板立于桌边 · 专为纸质真题与涂卡设计 · 模块打卡记录实际配速
          </p>
        </div>
      </div>

      <!-- 右侧辅助控制：常亮、广播音效、全屏沉浸、手工补录 -->
      <div class="flex items-center space-x-1.5 flex-wrap">
        <!-- 屏幕防休眠常亮指示 -->
        <button
          type="button"
          @click="toggleWakeLock"
          class="px-2 py-1 rounded-lg text-[11px] font-medium border transition flex items-center space-x-1 cursor-pointer"
          :class="omrStore.isScreenWakeLocked
            ? 'bg-amber-50 border-amber-300 text-amber-800 font-bold shadow-2xs'
            : 'bg-slate-50 border-slate-200 text-slate-500 hover:text-slate-800'"
          title="保持屏幕常亮不黑屏，方便桌边看表"
        >
          <i class="fa-solid fa-sun text-[10px]" :class="omrStore.isScreenWakeLocked ? 'text-amber-500 animate-spin-slow' : ''"></i>
          <span>{{ omrStore.isScreenWakeLocked ? '常亮已开' : '常亮防息屏' }}</span>
        </button>

        <!-- 考场广播提醒切换 -->
        <button
          type="button"
          @click="cycleSoundMode"
          class="px-2 py-1 rounded-lg text-[11px] font-medium border transition flex items-center space-x-1 cursor-pointer bg-slate-50 border-slate-200 text-slate-600 hover:text-slate-900"
          :title="soundModeTitle"
        >
          <i :class="soundModeIcon"></i>
          <span>{{ soundModeLabel }}</span>
        </button>

        <!-- 沉浸全屏时钟大屏 -->
        <button
          type="button"
          @click="omrStore.isFullscreenPaperTimer = true"
          class="px-2 py-1 rounded-lg text-[11px] font-medium border transition flex items-center space-x-1 cursor-pointer bg-slate-50 border-slate-200 text-slate-600 hover:text-blue-700 hover:border-blue-300"
          title="切换至纯黑大字全屏考场时钟看板"
        >
          <i class="fa-solid fa-expand text-[10px]"></i>
          <span>全屏大钟</span>
        </button>

        <!-- 补录纸质用时展开按钮 -->
        <button
          type="button"
          @click="omrStore.isManualTimeOpen = !omrStore.isManualTimeOpen"
          class="px-2 py-1 rounded-lg text-[11px] font-medium border transition flex items-center space-x-1 cursor-pointer"
          :class="omrStore.isManualTimeOpen
            ? 'bg-blue-50 border-blue-300 text-blue-700 font-bold'
            : 'bg-slate-50 border-slate-200 text-slate-500 hover:text-slate-800'"
          title="使用机械手表计时的考生，可在此直接补录各模块用时"
        >
          <i class="fa-solid fa-pen-clip text-[10px]"></i>
          <span>补录用时</span>
        </button>
      </div>
    </div>

    <!-- ⏱️ 考场核心数码时钟看板 (大字液晶视觉) -->
    <div
      :class="[
        'rounded-2xl p-4 sm:p-5 border transition-all duration-300 text-center relative overflow-hidden',
        omrStore.isTimeCritical
          ? 'bg-gradient-to-br from-rose-50 via-red-50 to-amber-50 border-rose-300 ring-2 ring-rose-400/40 text-rose-900 shadow-sm'
          : (omrStore.isTimeWarning
            ? 'bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 border-amber-300 text-amber-950 shadow-sm'
            : (omrStore.examTimerStatus === 'running'
              ? 'bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white border-slate-700 shadow-md'
              : 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-950 text-white border-slate-700 shadow-xs'))
      ]"
    >
      <!-- 顶部考场预警语 -->
      <div
        class="text-[11px] font-bold tracking-wide flex items-center justify-center space-x-1.5 mb-1"
        :class="omrStore.isTimeCritical ? 'text-rose-600' : (omrStore.isTimeWarning ? 'text-amber-700' : 'text-slate-300')"
      >
        <i class="fa-regular fa-clock text-xs"></i>
        <span v-if="omrStore.paperTimerMode === 'stopwatch'">纸质做题正向累计用时秒表</span>
        <span v-else-if="omrStore.isTimeCritical">🚨 考场紧急提醒：最后冲刺阶段，请检查并完成涂卡！</span>
        <span v-else-if="omrStore.isTimeWarning">⚠️ 考场提示：离考试结束还有不到 15 分钟</span>
        <span v-else>公考行测实战纸质作答倒计时看板</span>
      </div>

      <!-- 超大数码时钟 -->
      <div
        :class="[
          'font-mono font-black text-4xl sm:text-5xl tracking-wider my-1 select-none',
          omrStore.isTimeCritical ? 'text-rose-600 animate-pulse' : (omrStore.isTimeWarning ? 'text-amber-800' : 'text-white')
        ]"
      >
        <span v-if="omrStore.paperTimerMode === 'stopwatch'">{{ omrStore.formattedTimeElapsed }}</span>
        <span v-else>{{ omrStore.formattedTimeRemaining }}</span>
      </div>

      <!-- 快速切换模考时长 (仅在未开始时显示) -->
      <div
        v-if="omrStore.examTimerStatus === 'idle'"
        class="flex items-center justify-center space-x-1 mt-2.5 flex-wrap gap-y-1 text-xs"
      >
        <span class="text-[11px] text-slate-300 mr-1">模考模式:</span>
        <button
          v-for="preset in durationOptions"
          :key="preset.min"
          type="button"
          @click="selectDuration(preset.min, 'countdown')"
          :class="[
            'px-2.5 py-1 rounded-lg text-xs font-semibold transition cursor-pointer',
            selectedDurationMin === preset.min && omrStore.paperTimerMode === 'countdown'
              ? 'bg-blue-600 text-white font-bold shadow-xs'
              : 'bg-white/10 hover:bg-white/20 text-slate-200'
          ]"
        >
          {{ preset.label }}
        </button>
        <button
          type="button"
          @click="selectDuration(0, 'stopwatch')"
          :class="[
            'px-2.5 py-1 rounded-lg text-xs font-semibold transition cursor-pointer',
            omrStore.paperTimerMode === 'stopwatch'
              ? 'bg-indigo-600 text-white font-bold shadow-xs'
              : 'bg-white/10 hover:bg-white/20 text-slate-200'
          ]"
        >
          自由秒表
        </button>
      </div>

      <!-- 倒计时进度指示条 (倒计时模式) -->
      <div v-if="omrStore.paperTimerMode === 'countdown' && omrStore.examTimerStatus !== 'idle'" class="mt-2.5 max-w-md mx-auto">
        <div class="w-full bg-white/20 h-1.5 rounded-full overflow-hidden">
          <div
            class="h-full transition-all duration-300"
            :class="omrStore.isTimeCritical ? 'bg-rose-500' : (omrStore.isTimeWarning ? 'bg-amber-400' : 'bg-blue-400')"
            :style="{ width: `${totalTimeElapsedPct}%` }"
          ></div>
        </div>
        <div class="flex justify-between text-[10px] mt-1 opacity-70" :class="omrStore.isTimeCritical || omrStore.isTimeWarning ? 'text-slate-700' : 'text-slate-300'">
          <span>已作答: {{ omrStore.formattedTimeElapsed }}</span>
          <span>目标时长: {{ omrStore.examDurationMinutes }}分钟</span>
        </div>
      </div>

      <!-- 控制器大按钮区 -->
      <div class="flex items-center justify-center space-x-2.5 mt-3.5 flex-wrap gap-y-2">
        <!-- 未开始状态 -->
        <template v-if="omrStore.examTimerStatus === 'idle'">
          <button
            type="button"
            @click="handleStartPaperExam"
            class="px-6 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs sm:text-sm shadow-md transition flex items-center space-x-2 active:scale-95 cursor-pointer"
          >
            <i class="fa-solid fa-play text-xs"></i>
            <span>开始纸质做题计时</span>
          </button>
        </template>

        <!-- 进行中状态 -->
        <template v-else-if="omrStore.examTimerStatus === 'running'">
          <button
            type="button"
            @click="omrStore.pauseMockExam"
            :class="[
              'px-4 py-2 rounded-xl font-bold text-xs transition flex items-center space-x-1.5 active:scale-95 cursor-pointer',
              omrStore.isTimeCritical || omrStore.isTimeWarning
                ? 'bg-amber-600 hover:bg-amber-700 text-white'
                : 'bg-white/20 hover:bg-white/30 text-white'
            ]"
          >
            <i class="fa-solid fa-pause text-xs"></i>
            <span>暂停</span>
          </button>
          <button
            type="button"
            @click="handleFinishAndGrade"
            class="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs sm:text-sm shadow-md transition flex items-center space-x-1.5 active:scale-95 cursor-pointer"
          >
            <i class="fa-solid fa-camera text-xs"></i>
            <span>📸 作答完毕，立即拍照批改</span>
          </button>
        </template>

        <!-- 暂停状态 -->
        <template v-else-if="omrStore.examTimerStatus === 'paused'">
          <button
            type="button"
            @click="omrStore.resumeMockExam"
            class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow transition flex items-center space-x-1.5 active:scale-95 cursor-pointer"
          >
            <i class="fa-solid fa-play text-xs"></i>
            <span>继续做题</span>
          </button>
          <button
            type="button"
            @click="handleFinishAndGrade"
            class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow transition flex items-center space-x-1.5 active:scale-95 cursor-pointer"
          >
            <i class="fa-solid fa-camera text-xs"></i>
            <span>拍照批改</span>
          </button>
          <button
            type="button"
            @click="handleResetExam"
            :class="[
              'px-3 py-2 rounded-xl font-medium text-xs transition flex items-center space-x-1 cursor-pointer',
              omrStore.isTimeCritical || omrStore.isTimeWarning
                ? 'bg-slate-200 hover:bg-slate-300 text-slate-700'
                : 'bg-white/10 hover:bg-white/20 text-slate-200'
            ]"
          >
            <i class="fa-solid fa-arrows-rotate text-[10px]"></i>
            <span>重置</span>
          </button>
        </template>

        <!-- 已结束状态 -->
        <template v-else-if="omrStore.examTimerStatus === 'finished'">
          <button
            type="button"
            @click="handleFinishAndGrade"
            class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs sm:text-sm shadow-md transition flex items-center space-x-2 active:scale-95 cursor-pointer"
          >
            <i class="fa-solid fa-camera text-sm"></i>
            <span>📸 对准答题卡拍照批改 (用时已自动绑定)</span>
          </button>
          <button
            type="button"
            @click="handleResetExam"
            class="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition cursor-pointer"
          >
            重新开始模考
          </button>
        </template>
      </div>
    </div>

    <!-- 📌 行测灵魂战术：【模块路标与一键打卡控制台】 -->
    <div class="bg-slate-50/90 rounded-2xl p-3.5 sm:p-4 border border-slate-200/90 space-y-3">
      <!-- 正在进行的模块与配速状态 -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/70 pb-2.5">
        <div class="flex items-center space-x-2 min-w-0">
          <span class="w-2.5 h-2.5 rounded-full bg-blue-600 animate-ping"></span>
          <div>
            <div class="flex items-center space-x-1.5 flex-wrap">
              <span class="text-[11px] text-slate-400 font-medium">当前做题模块:</span>
              <span class="font-extrabold text-sm text-slate-900">
                {{ omrStore.effectiveActivePaperSec?.name || '综合模块' }}
              </span>
              <span class="text-[10px] px-1.5 py-0.2 rounded bg-blue-100 text-blue-700 font-semibold">
                {{ omrStore.effectiveActivePaperSec?.start_q }}~{{ omrStore.effectiveActivePaperSec?.end_q }}题 (共 {{ currentSecQCount }} 题)
              </span>
            </div>
            <div class="text-[11px] text-slate-500 mt-0.5">
              建议单题: <b>{{ omrStore.activePaperBenchmark?.perQSec || 50 }}秒/题</b> ·
              建议该模块总用时: <b>{{ Math.round(omrStore.activePaperTargetSeconds / 60) }}分钟</b> ·
              <span :class="omrStore.activePaperIsOvertime ? 'text-rose-600 font-bold' : 'text-slate-600'">
                实际已耗时: <b>{{ currentSecElapsedStr }}</b>
              </span>
            </div>
          </div>
        </div>

        <!-- 超大打卡按钮 (轻触记录模块耗时并跳下一模块) -->
        <div class="shrink-0 flex items-center space-x-2">
          <button
            type="button"
            @click="handleLapSection"
            :disabled="omrStore.examTimerStatus !== 'running'"
            class="w-full sm:w-auto px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-xs shadow-xs transition flex items-center justify-center space-x-1.5 active:scale-95 cursor-pointer"
            title="做完当前模块纸质题目时点击打卡，自动进入下一模块计时"
          >
            <i class="fa-solid fa-flag-checkered text-xs"></i>
            <span>完成本模块 (打卡并切下一模块)</span>
          </button>
        </div>
      </div>

      <!-- 模块用时进度条对比 -->
      <div class="space-y-1">
        <div class="flex justify-between text-[11px] font-medium">
          <span class="text-slate-500">
            模块耗时进度: {{ omrStore.activePaperProgressPct }}%
            <span v-if="omrStore.activePaperIsOvertime" class="text-rose-600 font-bold ml-1">
              (⚠️ 已超出建议时间 {{ overtimeSecondsStr }})
            </span>
          </span>
          <span class="text-slate-400">
            {{ currentSecElapsedStr }} / {{ Math.round(omrStore.activePaperTargetSeconds / 60) }}分
          </span>
        </div>
        <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
          <div
            class="h-full transition-all duration-300"
            :class="omrStore.activePaperIsOvertime ? 'bg-rose-500' : (omrStore.activePaperProgressPct > 80 ? 'bg-amber-400' : 'bg-emerald-500')"
            :style="{ width: `${Math.min(100, omrStore.activePaperProgressPct)}%` }"
          ></div>
        </div>
      </div>

      <!-- 模块跳序选择器 (实战支持任意顺序做题) -->
      <div class="space-y-1.5 pt-1">
        <div class="flex items-center justify-between text-[11px]">
          <span class="text-slate-500 font-medium">实战做题顺序（点击可随时切换做题焦点，如先做资料分析）:</span>
          <span class="text-blue-600 text-[10px]">点击任意模块快速切换</span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-5 gap-1.5">
          <button
            v-for="sec in omrStore.currentSections"
            :key="sec.id || sec.name"
            type="button"
            @click="omrStore.switchPaperSection(sec.id || sec.name)"
            :class="[
              'p-2 rounded-xl border text-left transition cursor-pointer text-xs relative overflow-hidden',
              (sec.id || sec.name) === omrStore.effectivePaperSecKey
                ? 'bg-blue-50/90 border-blue-500 text-blue-800 shadow-2xs font-bold ring-1 ring-blue-400/40'
                : 'bg-white border-slate-200/90 text-slate-700 hover:bg-slate-100/80 font-medium'
            ]"
          >
            <div class="flex items-center justify-between">
              <span class="truncate">{{ sec.name }}</span>
              <span
                v-if="(sec.id || sec.name) === omrStore.effectivePaperSecKey"
                class="w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0"
              ></span>
            </div>
            <div class="text-[10px] text-slate-400 font-normal mt-0.5 flex items-center justify-between">
              <span>{{ sec.end_q - sec.start_q + 1 }}题</span>
              <span class="font-mono font-bold" :class="getSecSpentColor(sec)">
                {{ formatSecSpent(sec) }}
              </span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- 📝 手工补录纸质用时抽屉 (针对使用手表的考生) -->
    <div v-show="omrStore.isManualTimeOpen" class="bg-blue-50/60 rounded-2xl p-4 border border-blue-200/80 space-y-3 transition">
      <div class="flex items-center justify-between border-b border-blue-100 pb-2">
        <div>
          <h4 class="font-bold text-xs text-blue-950 flex items-center space-x-1.5">
            <i class="fa-solid fa-calculator text-blue-600"></i>
            <span>手工快速录入纸质各模块耗时 (免手机计时)</span>
          </h4>
          <p class="text-[10px] text-slate-500">
            若做题时是用机械表或手环计时的，在此输入各模块实际分钟数，同样生成四象限诊断
          </p>
        </div>
        <button
          type="button"
          @click="autoFillBenchmarkTimes"
          class="text-[11px] text-blue-600 hover:text-blue-800 font-semibold bg-white px-2 py-0.5 rounded-lg border border-blue-200 shadow-2xs cursor-pointer"
        >
          一键填入建议比例
        </button>
      </div>

      <!-- 各模块分钟数输入行 -->
      <div class="grid grid-cols-2 sm:grid-cols-5 gap-2">
        <div
          v-for="sec in omrStore.currentSections"
          :key="sec.id || sec.name"
          class="bg-white p-2 rounded-xl border border-blue-100 space-y-1 shadow-2xs"
        >
          <div class="font-bold text-[11px] text-slate-800 truncate">{{ sec.name }}</div>
          <div class="flex items-center space-x-1">
            <input
              type="number"
              min="0"
              max="120"
              step="1"
              v-model.number="tempManualMinutes[sec.id || sec.name]"
              class="w-full bg-slate-50 border border-slate-300 rounded px-1.5 py-0.5 text-center text-xs font-mono font-bold text-blue-700 focus:outline-none focus:border-blue-500"
              placeholder="0"
            >
            <span class="text-[10px] text-slate-400 shrink-0">分</span>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-between pt-1">
        <span class="text-xs text-slate-600">
          合计全卷总用时: <b class="text-blue-700 font-mono">{{ calcManualTotalMinutes }}</b> 分钟
        </span>
        <button
          type="button"
          @click="saveManualTimes"
          class="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-xs transition cursor-pointer"
        >
          应用并保存用时
        </button>
      </div>
    </div>

    <!-- ⛶ 沉浸全屏时钟弹窗 (Fullscreen Modal) -->
    <div
      v-if="omrStore.isFullscreenPaperTimer"
      class="fixed inset-0 z-50 bg-black text-white flex flex-col justify-between p-6 sm:p-12 select-none"
    >
      <!-- 全屏顶部状态栏 -->
      <div class="flex items-center justify-between border-b border-white/10 pb-4">
        <div class="flex items-center space-x-3">
          <span class="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></span>
          <span class="font-bold text-base sm:text-lg tracking-wider text-slate-200">
            公考行测全真模考伴考看板
          </span>
          <span class="text-xs px-2 py-0.5 bg-white/10 rounded-full text-slate-300">
            常亮防息屏
          </span>
        </div>
        <button
          type="button"
          @click="omrStore.isFullscreenPaperTimer = false"
          class="px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-slate-300 hover:text-white text-xs font-semibold transition cursor-pointer"
        >
          <i class="fa-solid fa-compress mr-1"></i>
          <span>退出全屏</span>
        </button>
      </div>

      <!-- 居中超大倒计时 -->
      <div class="text-center my-auto space-y-4">
        <div class="text-sm font-semibold tracking-widest text-slate-400 uppercase">
          {{ omrStore.isTimeCritical ? '🚨 考场最后冲刺提醒' : '全卷实战做题剩余时间' }}
        </div>
        <div
          class="font-mono font-black text-6xl sm:text-8xl md:text-9xl tracking-widest"
          :class="omrStore.isTimeCritical ? 'text-rose-500 animate-pulse' : (omrStore.isTimeWarning ? 'text-amber-400' : 'text-white')"
        >
          {{ omrStore.paperTimerMode === 'stopwatch' ? omrStore.formattedTimeElapsed : omrStore.formattedTimeRemaining }}
        </div>
        <div class="text-base text-slate-300">
          当前模块: <b class="text-amber-400 font-bold">{{ omrStore.effectiveActivePaperSec?.name }}</b> ·
          本模块用时: <b>{{ currentSecElapsedStr }}</b>
        </div>
      </div>

      <!-- 底部控制栏 -->
      <div class="flex items-center justify-between border-t border-white/10 pt-6 flex-wrap gap-4">
        <div class="flex items-center space-x-2">
          <button
            type="button"
            @click="omrStore.pauseMockExam"
            v-if="omrStore.examTimerStatus === 'running'"
            class="px-6 py-3 rounded-2xl bg-white/15 hover:bg-white/25 text-white font-bold text-sm cursor-pointer"
          >
            <i class="fa-solid fa-pause mr-1.5"></i> 暂停
          </button>
          <button
            type="button"
            @click="omrStore.resumeMockExam"
            v-else
            class="px-6 py-3 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm cursor-pointer"
          >
            <i class="fa-solid fa-play mr-1.5"></i> 继续
          </button>
        </div>

        <button
          type="button"
          @click="handleLapSection"
          class="px-8 py-3.5 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-black text-base shadow-lg cursor-pointer"
        >
          <i class="fa-solid fa-flag-checkered mr-2"></i> 完成当前模块打卡
        </button>

        <button
          type="button"
          @click="handleFinishAndGradeFullscreen"
          class="px-6 py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm cursor-pointer"
        >
          <i class="fa-solid fa-camera mr-1.5"></i> 作答完毕，去拍照
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useOmrStore } from '../../stores/omr';
import { EXAM_DURATION_PRESETS, formatSecondsToChinese, getSectionBenchmark } from '../../constants/examTiming';

const omrStore = useOmrStore();
const emit = defineEmits(['trigger-camera']);

const selectedDurationMin = ref(120);
const durationOptions = EXAM_DURATION_PRESETS;

const tempManualMinutes = ref({});

onMounted(() => {
  initManualTimes();
});

onBeforeUnmount(() => {
  omrStore.releaseScreenWakeLock();
});

function initManualTimes() {
  if (omrStore.currentSections) {
    omrStore.currentSections.forEach(sec => {
      const k = sec.id || sec.name;
      const curSec = omrStore.sectionTimes[k] || 0;
      tempManualMinutes.value[k] = curSec > 0 ? Math.round(curSec / 60) : Math.round((getSectionBenchmark(sec.id, sec.name).targetMin || 20));
    });
  }
}

const currentSecQCount = computed(() => {
  const sec = omrStore.effectiveActivePaperSec;
  if (!sec) return 0;
  return Math.max(1, sec.end_q - sec.start_q + 1);
});

const currentSecElapsedStr = computed(() => {
  return formatSecondsToChinese(omrStore.activePaperSecElapsed);
});

const overtimeSecondsStr = computed(() => {
  const diff = omrStore.activePaperSecElapsed - omrStore.activePaperTargetSeconds;
  return formatSecondsToChinese(Math.max(0, diff));
});

const totalTimeElapsedPct = computed(() => {
  const totalTargetSec = (omrStore.examDurationMinutes || 120) * 60;
  if (!totalTargetSec) return 0;
  const pct = Math.round((omrStore.examTimeElapsed / totalTargetSec) * 100);
  return Math.min(100, Math.max(0, pct));
});

const calcManualTotalMinutes = computed(() => {
  let s = 0;
  Object.values(tempManualMinutes.value).forEach(v => {
    s += parseFloat(v) || 0;
  });
  return s;
});

// 声音模式切换
function cycleSoundMode() {
  if (omrStore.soundAlertMode === 'voice') {
    omrStore.soundAlertMode = 'beep';
  } else if (omrStore.soundAlertMode === 'beep') {
    omrStore.soundAlertMode = 'mute';
  } else {
    omrStore.soundAlertMode = 'voice';
  }
}

const soundModeLabel = computed(() => {
  if (omrStore.soundAlertMode === 'voice') return '语音广播';
  if (omrStore.soundAlertMode === 'beep') return '提示音';
  return '静音';
});

const soundModeIcon = computed(() => {
  if (omrStore.soundAlertMode === 'voice') return 'fa-solid fa-volume-high text-blue-600 text-[10px]';
  if (omrStore.soundAlertMode === 'beep') return 'fa-solid fa-bell text-amber-600 text-[10px]';
  return 'fa-solid fa-volume-xmark text-slate-400 text-[10px]';
});

const soundModeTitle = computed(() => {
  if (omrStore.soundAlertMode === 'voice') return '当前：考场语音播报广播（开考、涂卡预警、切题语音）';
  if (omrStore.soundAlertMode === 'beep') return '当前：柔和钟声提示音';
  return '当前：静音（图书馆/自习室模式）';
});

// 常亮切换
function toggleWakeLock() {
  if (omrStore.isScreenWakeLocked) {
    omrStore.releaseScreenWakeLock();
  } else {
    omrStore.requestScreenWakeLock();
  }
}

function selectDuration(min, mode) {
  selectedDurationMin.value = min;
  omrStore.paperTimerMode = mode;
  if (mode === 'countdown') {
    omrStore.examDurationMinutes = min;
    omrStore.examTimeRemaining = min * 60;
  }
}

function handleStartPaperExam() {
  omrStore.startMockExam(selectedDurationMin.value, omrStore.paperTimerMode);
}

function handleResetExam() {
  omrStore.resetMockExam();
}

function handleLapSection() {
  omrStore.lapPaperSection();
}

function handleFinishAndGrade() {
  omrStore.finishPaperExam();
  emit('trigger-camera');
}

function handleFinishAndGradeFullscreen() {
  omrStore.isFullscreenPaperTimer = false;
  handleFinishAndGrade();
}

function autoFillBenchmarkTimes() {
  if (omrStore.currentSections) {
    omrStore.currentSections.forEach(sec => {
      const k = sec.id || sec.name;
      const bench = getSectionBenchmark(sec.id, sec.name);
      tempManualMinutes.value[k] = bench.targetMin || 20;
    });
  }
}

function saveManualTimes() {
  omrStore.applyManualSectionTimes(tempManualMinutes.value);
  omrStore.isManualTimeOpen = false;
}

function formatSecSpent(sec) {
  const k = sec.id || sec.name;
  const s = omrStore.sectionTimes[k] || 0;
  if (s === 0) return '--';
  return formatSecondsToChinese(s);
}

function getSecSpentColor(sec) {
  const k = sec.id || sec.name;
  const s = omrStore.sectionTimes[k] || 0;
  if (s === 0) return 'text-slate-400';
  const bench = getSectionBenchmark(sec.id, sec.name);
  const targetSec = (bench.perQSec || 50) * (sec.end_q - sec.start_q + 1);
  if (s > targetSec) return 'text-rose-600 font-extrabold';
  return 'text-emerald-600';
}
</script>
