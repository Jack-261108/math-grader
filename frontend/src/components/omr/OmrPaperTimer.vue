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

    <!-- ⛶ 沉浸全屏时钟看板 (Teleport 到 body 彻底杜绝漏底，支持横竖屏自由旋转与切换) -->
    <Teleport to="body">
      <div
        v-if="omrStore.isFullscreenPaperTimer"
        class="fixed inset-0 z-[9999] bg-black text-white flex flex-col justify-between select-none overflow-hidden"
        :style="fullscreenContainerStyle"
      >
        <!-- 全屏顶部状态栏 -->
        <div class="flex items-center justify-between border-b border-white/10 pb-2.5 shrink-0">
          <div class="flex items-center space-x-2.5 min-w-0">
            <span
              class="w-2.5 h-2.5 rounded-full shrink-0"
              :class="omrStore.examTimerStatus === 'running' ? 'bg-emerald-500 animate-pulse' : (omrStore.examTimerStatus === 'paused' ? 'bg-amber-500' : 'bg-blue-500')"
            ></span>
            <div class="min-w-0">
              <h4 class="font-bold text-sm sm:text-base tracking-wide text-slate-100 truncate">
                公考行测全真模考伴考中控
              </h4>
              <div class="text-[10px] text-slate-400 font-mono mt-0.5">
                {{ omrStore.paperTimerMode === 'stopwatch' ? '正向秒表计时' : `${omrStore.examDurationMinutes}分钟标准限时` }} · 常亮防息屏
              </div>
            </div>
          </div>

          <!-- 右侧：电脑快捷键提示 + 移动端横竖屏切换 + 声音切换 + 退出全屏 -->
          <div class="flex items-center space-x-2 shrink-0">
            <!-- 电脑端专属快捷键温馨提示 -->
            <div v-if="isDesktop" class="hidden lg:flex items-center space-x-2 text-[11px] text-slate-400 bg-white/5 border border-white/10 px-3 py-1 rounded-xl">
              <span>按 <kbd class="bg-white/20 px-1.5 py-0.5 rounded text-[10px] font-mono text-white font-bold">Space</kbd> 打卡</span>
              <span>·</span>
              <span>按 <kbd class="bg-white/20 px-1.5 py-0.5 rounded text-[10px] font-mono text-white font-bold">P</kbd> 暂停/继续</span>
              <span>·</span>
              <span>按 <kbd class="bg-white/20 px-1.5 py-0.5 rounded text-[10px] font-mono text-white font-bold">Esc</kbd> 退出</span>
            </div>

            <!-- 手机端旋转横竖屏切换按钮 (电脑端自动隐藏) -->
            <button
              v-if="!isDesktop"
              type="button"
              @click="toggleOrientation"
              class="px-2.5 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 active:bg-white/30 text-slate-200 text-xs font-semibold flex items-center space-x-1 transition cursor-pointer"
              :title="effectiveIsLandscape ? '点击切换为竖屏模式' : '点击切换为横屏桌面时钟模式'"
            >
              <i :class="orientationToggleIcon"></i>
              <span>{{ orientationToggleText }}</span>
            </button>

            <!-- 声音控制按钮 -->
            <button
              type="button"
              @click="cycleSoundMode"
              class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 active:bg-white/30 text-slate-300 hover:text-white flex items-center justify-center text-xs transition cursor-pointer"
              :title="soundModeTitle"
            >
              <i :class="soundModeIcon"></i>
            </button>

            <!-- 退出全屏按钮 -->
            <button
              type="button"
              @click="exitFullscreenView"
              class="px-3 py-1.5 rounded-xl bg-white/15 hover:bg-white/25 active:bg-white/30 text-slate-200 hover:text-white text-xs font-semibold flex items-center space-x-1 transition cursor-pointer"
            >
              <i class="fa-solid fa-compress text-[11px]"></i>
              <span>退出</span>
            </button>
          </div>
        </div>

        <!-- 🖥️ 1. 电脑宽屏专属布局 (Desktop Mode)：宽屏双翼中控台，左侧超大时钟，右侧五大模块全景路标卡 -->
        <div v-if="isDesktop" class="flex-1 min-h-0 grid grid-cols-12 gap-6 py-4 items-center w-full max-w-7xl mx-auto px-4">
          <!-- 左翼 (7列)：考场状态 + 超大数码时钟 + 底部大按钮 -->
          <div class="col-span-7 flex flex-col justify-center items-center text-center space-y-5 pr-4 border-r border-white/10 h-full">
            <span
              class="text-xs sm:text-sm font-bold tracking-widest px-4 py-1 rounded-full border uppercase shadow-2xs"
              :class="omrStore.isTimeCritical
                ? 'bg-rose-950/80 border-rose-500 text-rose-400 animate-pulse'
                : (omrStore.isTimeWarning
                  ? 'bg-amber-950/80 border-amber-500 text-amber-300'
                  : 'bg-white/5 border-white/15 text-slate-300')"
            >
              {{ omrStore.isTimeCritical ? '🚨 考场最后冲刺阶段 · 注意填涂答题卡' : (omrStore.isTimeWarning ? '⚠️ 剩余不到15分钟 · 请合理分配各模块时间' : (omrStore.paperTimerMode === 'stopwatch' ? '全卷累计做题用时' : '全卷剩余答题时间')) }}
            </span>

            <!-- 超大液晶数码管时钟 (电脑桌面冲击力拉满) -->
            <div
              class="font-mono tabular-nums font-black text-8xl xl:text-9xl 2xl:text-[10rem] tracking-tight select-none leading-none drop-shadow-lg my-2"
              :class="omrStore.isTimeCritical ? 'text-rose-500 animate-pulse' : (omrStore.isTimeWarning ? 'text-amber-400' : 'text-white')"
            >
              {{ omrStore.paperTimerMode === 'stopwatch' ? omrStore.formattedTimeElapsed : omrStore.formattedTimeRemaining }}
            </div>

            <!-- 当前模块核心卡片 -->
            <div class="w-full max-w-lg bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/15 space-y-2 text-left shadow-lg">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                  <span class="w-2.5 h-2.5 rounded-full bg-blue-400 animate-ping"></span>
                  <span class="text-xs text-slate-300">正在作答模块:</span>
                  <b class="text-base text-white">{{ omrStore.effectiveActivePaperSec?.name }}</b>
                  <span class="text-xs px-2 py-0.5 rounded bg-blue-500/30 text-blue-200 font-semibold">
                    第 {{ omrStore.effectiveActivePaperSec?.start_q }}~{{ omrStore.effectiveActivePaperSec?.end_q }} 题 (共 {{ currentSecQCount }} 题)
                  </span>
                </div>
                <span class="text-sm font-mono font-bold" :class="omrStore.activePaperIsOvertime ? 'text-rose-400' : 'text-emerald-400'">
                  实耗: {{ currentSecElapsedStr }}
                </span>
              </div>
              <div class="w-full bg-white/15 h-2 rounded-full overflow-hidden">
                <div
                  class="h-full transition-all duration-300"
                  :class="omrStore.activePaperIsOvertime ? 'bg-rose-500' : (omrStore.activePaperProgressPct > 80 ? 'bg-amber-400' : 'bg-blue-400')"
                  :style="{ width: `${Math.min(100, omrStore.activePaperProgressPct)}%` }"
                ></div>
              </div>
              <div class="flex justify-between text-xs text-slate-400 font-medium">
                <span>公考实战建议: {{ omrStore.activePaperBenchmark?.perQSec || 50 }} 秒/题</span>
                <span>建议模块总耗时: {{ Math.round(omrStore.activePaperTargetSeconds / 60) }} 分钟</span>
              </div>
            </div>

            <!-- 电脑端控制按钮栏 -->
            <div class="w-full max-w-lg grid grid-cols-12 gap-3 pt-2">
              <button
                type="button"
                @click="omrStore.pauseMockExam"
                v-if="omrStore.examTimerStatus === 'running'"
                class="col-span-4 py-3 rounded-xl bg-white/15 hover:bg-white/25 active:scale-98 text-white font-bold text-xs sm:text-sm flex items-center justify-center space-x-1.5 transition cursor-pointer"
              >
                <i class="fa-solid fa-pause text-xs"></i>
                <span>暂停 (P)</span>
              </button>
              <button
                type="button"
                @click="omrStore.resumeMockExam"
                v-else
                class="col-span-4 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-98 text-white font-bold text-xs sm:text-sm flex items-center justify-center space-x-1.5 transition cursor-pointer"
              >
                <i class="fa-solid fa-play text-xs"></i>
                <span>继续 (P)</span>
              </button>

              <button
                type="button"
                @click="handleLapSection"
                class="col-span-8 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 active:scale-98 text-white font-black text-xs sm:text-sm shadow-md flex items-center justify-center space-x-2 transition cursor-pointer"
              >
                <i class="fa-solid fa-flag-checkered text-sm text-blue-200"></i>
                <span>完成本模块打卡 (Space)</span>
              </button>

              <button
                type="button"
                @click="handleFinishAndGradeFullscreen"
                class="col-span-12 py-3.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 active:scale-98 text-white font-black text-sm shadow-lg flex items-center justify-center space-x-2 transition cursor-pointer"
              >
                <i class="fa-solid fa-camera text-base text-emerald-200"></i>
                <span>📸 纸质作答完毕，去拍照批改 (Enter)</span>
              </button>
            </div>
          </div>

          <!-- 右翼 (5列)：行测五大模块全景路标卡中控面板 -->
          <div class="col-span-5 flex flex-col justify-center space-y-3 h-full pl-2">
            <div class="flex items-center justify-between pb-1 border-b border-white/10">
              <span class="text-xs font-bold text-slate-300 flex items-center space-x-1.5">
                <i class="fa-solid fa-list-check text-blue-400"></i>
                <span>全卷五大模块时间分配中控 (点击随时切换)</span>
              </span>
              <span class="text-[10px] text-slate-400">实时分段配速监控</span>
            </div>

            <!-- 5个模块卡片垂直排列 -->
            <div class="space-y-2.5 overflow-y-auto max-h-[65vh] pr-1">
              <div
                v-for="sec in omrStore.currentSections"
                :key="sec.id || sec.name"
                @click="omrStore.switchPaperSection(sec.id || sec.name)"
                :class="[
                  'p-3 rounded-2xl border transition-all cursor-pointer space-y-1.5 relative overflow-hidden',
                  (sec.id || sec.name) === omrStore.effectivePaperSecKey
                    ? 'bg-blue-600/30 border-blue-400 ring-2 ring-blue-500/40 shadow-md'
                    : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                ]"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-2">
                    <span
                      class="w-2 h-2 rounded-full shrink-0"
                      :class="(sec.id || sec.name) === omrStore.effectivePaperSecKey ? 'bg-blue-400 animate-ping' : 'bg-slate-500'"
                    ></span>
                    <span class="font-bold text-sm text-white">{{ sec.name }}</span>
                    <span class="text-[11px] text-slate-400">({{ sec.start_q }}~{{ sec.end_q }}题)</span>
                  </div>

                  <!-- 状态徽章 -->
                  <div class="flex items-center space-x-2">
                    <span
                      v-if="(sec.id || sec.name) === omrStore.effectivePaperSecKey"
                      class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-blue-500 text-white"
                    >
                      进行中
                    </span>
                    <span
                      v-else-if="omrStore.sectionTimes[sec.id || sec.name] > 0"
                      class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    >
                      已打卡 ✓
                    </span>
                    <span v-else class="text-[10px] px-2 py-0.5 rounded-full text-slate-400 bg-white/5">
                      待作答
                    </span>
                  </div>
                </div>

                <!-- 模块建议耗时与实际耗时对比条 -->
                <div class="flex items-center justify-between text-[11px]">
                  <span class="text-slate-400">
                    建议: {{ Math.round(((getSectionBenchmark(sec.id, sec.name).perQSec || 50) * (sec.end_q - sec.start_q + 1)) / 60) }}分钟
                  </span>
                  <span class="font-mono font-bold" :class="getSecSpentColor(sec)">
                    实测耗时: {{ formatSecSpent(sec) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 📱 2. 手机横屏模式 (Mobile Landscape)：左右双栏紧凑布局 -->
        <div v-else-if="effectiveIsLandscape" class="flex-1 min-h-0 flex items-center justify-between gap-4 py-2">
          <!-- 左侧：超大液晶数码管时钟与模块配速卡片 -->
          <div class="flex-1 flex flex-col justify-center items-center text-center space-y-2 min-w-0 pr-2">
            <span
              class="text-xs font-bold tracking-widest px-3 py-0.5 rounded-full border uppercase shrink-0 shadow-2xs"
              :class="omrStore.isTimeCritical
                ? 'bg-rose-950/80 border-rose-500 text-rose-400 animate-pulse'
                : (omrStore.isTimeWarning
                  ? 'bg-amber-950/80 border-amber-500 text-amber-300'
                  : 'bg-white/5 border-white/15 text-slate-300')"
            >
              {{ omrStore.isTimeCritical ? '🚨 考场最后冲刺 · 注意涂卡' : (omrStore.isTimeWarning ? '⚠️ 剩余不到15分钟 · 注意填涂答题卡' : (omrStore.paperTimerMode === 'stopwatch' ? '累计做题用时' : '全卷剩余答题时间')) }}
            </span>

            <!-- 超大等宽数码液晶时钟 -->
            <div
              class="font-mono tabular-nums font-black text-6xl sm:text-7xl md:text-8xl lg:text-9xl tracking-tight select-none leading-none drop-shadow-md my-1"
              :class="omrStore.isTimeCritical ? 'text-rose-500 animate-pulse' : (omrStore.isTimeWarning ? 'text-amber-400' : 'text-white')"
            >
              {{ omrStore.paperTimerMode === 'stopwatch' ? omrStore.formattedTimeElapsed : omrStore.formattedTimeRemaining }}
            </div>

            <!-- 当前模块信息条 -->
            <div class="w-full max-w-lg bg-white/10 backdrop-blur-md rounded-xl px-3.5 py-1.5 border border-white/15 space-y-1 text-left">
              <div class="flex items-center justify-between text-xs">
                <div class="flex items-center space-x-1.5 truncate">
                  <span class="w-2 h-2 rounded-full bg-blue-400 shrink-0"></span>
                  <span class="text-slate-300">当前模块:</span>
                  <b class="text-white truncate">{{ omrStore.effectiveActivePaperSec?.name }}</b>
                  <span class="text-[10px] text-blue-200">({{ currentSecQCount }}题)</span>
                </div>
                <span class="font-mono font-bold" :class="omrStore.activePaperIsOvertime ? 'text-rose-400' : 'text-emerald-400'">
                  已用: {{ currentSecElapsedStr }} / {{ Math.round(omrStore.activePaperTargetSeconds / 60) }}分
                </span>
              </div>
              <div class="w-full bg-white/15 h-1.5 rounded-full overflow-hidden">
                <div
                  class="h-full transition-all duration-300"
                  :class="omrStore.activePaperIsOvertime ? 'bg-rose-500' : (omrStore.activePaperProgressPct > 80 ? 'bg-amber-400' : 'bg-blue-400')"
                  :style="{ width: `${Math.min(100, omrStore.activePaperProgressPct)}%` }"
                ></div>
              </div>
            </div>
          </div>

          <!-- 右侧：垂直排列大按钮 (适合桌面立放盲点) -->
          <div class="w-64 sm:w-72 shrink-0 flex flex-col justify-center space-y-2.5 pl-3 border-l border-white/10 h-full py-1">
            <!-- 核心战术：打卡 -->
            <button
              type="button"
              @click="handleLapSection"
              class="w-full py-3.5 sm:py-4 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 active:scale-98 text-white font-black text-xs sm:text-sm shadow-md flex items-center justify-center space-x-2 transition cursor-pointer"
            >
              <i class="fa-solid fa-flag-checkered text-xs text-blue-200"></i>
              <span>完成本模块打卡 (切下一模块)</span>
            </button>

            <!-- 暂停 / 继续 -->
            <button
              type="button"
              @click="omrStore.pauseMockExam"
              v-if="omrStore.examTimerStatus === 'running'"
              class="w-full py-2.5 rounded-xl bg-white/15 hover:bg-white/25 active:scale-98 text-white font-bold text-xs flex items-center justify-center space-x-1.5 transition cursor-pointer"
            >
              <i class="fa-solid fa-pause text-xs"></i>
              <span>暂停模考</span>
            </button>
            <button
              type="button"
              @click="omrStore.resumeMockExam"
              v-else
              class="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-98 text-white font-bold text-xs flex items-center justify-center space-x-1.5 transition cursor-pointer"
            >
              <i class="fa-solid fa-play text-xs"></i>
              <span>继续模考</span>
            </button>

            <!-- 作答完毕拍照批改 -->
            <button
              type="button"
              @click="handleFinishAndGradeFullscreen"
              class="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 active:scale-98 text-white font-bold text-xs sm:text-sm shadow-md flex items-center justify-center space-x-1.5 transition cursor-pointer"
            >
              <i class="fa-solid fa-camera text-sm text-emerald-200"></i>
              <span>作答完毕，去拍照</span>
            </button>
          </div>
        </div>

        <!-- 📱 3. 手机竖屏模式 (Mobile Portrait)：经典居中超大时钟 + 底部双排大拇指操作区 -->
        <template v-else>
          <!-- 居中核心时钟与当前模块卡片 -->
          <div class="my-auto py-2 flex flex-col items-center justify-center space-y-3 sm:space-y-5 text-center w-full max-w-xl mx-auto px-1">
            <!-- 考场节奏状态提示 -->
            <div class="flex items-center space-x-2">
              <span
                class="text-xs sm:text-sm font-bold tracking-widest px-3 py-1 rounded-full border uppercase shadow-2xs"
                :class="omrStore.isTimeCritical
                  ? 'bg-rose-950/80 border-rose-500 text-rose-400 animate-pulse'
                  : (omrStore.isTimeWarning
                    ? 'bg-amber-950/80 border-amber-500 text-amber-300'
                    : 'bg-white/5 border-white/15 text-slate-300')"
              >
                {{ omrStore.isTimeCritical ? '🚨 考场最后冲刺阶段 · 注意涂卡' : (omrStore.isTimeWarning ? '⚠️ 剩余不到15分钟 · 注意填涂答题卡' : (omrStore.paperTimerMode === 'stopwatch' ? '刷题累计用时' : '全卷剩余答题时间')) }}
              </span>
            </div>

            <!-- ⏱️ 超大等宽数码管液晶时钟 -->
            <div
              class="font-mono tabular-nums font-black text-6xl sm:text-8xl md:text-9xl tracking-tight sm:tracking-wider select-none leading-none drop-shadow-md my-1"
              :class="omrStore.isTimeCritical ? 'text-rose-500 animate-pulse' : (omrStore.isTimeWarning ? 'text-amber-400' : 'text-white')"
            >
              {{ omrStore.paperTimerMode === 'stopwatch' ? omrStore.formattedTimeElapsed : omrStore.formattedTimeRemaining }}
            </div>

            <!-- 当前做题模块路标卡片 -->
            <div class="w-full bg-white/10 backdrop-blur-md rounded-2xl p-3 sm:p-4 border border-white/15 space-y-2 text-left shadow-lg">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2 min-w-0">
                  <span class="w-2 h-2 rounded-full bg-blue-400 shrink-0"></span>
                  <span class="text-xs text-slate-300 font-medium">当前模块:</span>
                  <span class="text-sm sm:text-base font-extrabold text-white truncate">
                    {{ omrStore.effectiveActivePaperSec?.name }}
                  </span>
                  <span class="text-[10px] px-1.5 py-0.2 rounded bg-blue-500/30 text-blue-200 font-semibold shrink-0">
                    共 {{ currentSecQCount }} 题
                  </span>
                </div>
                <span class="text-xs font-mono font-bold shrink-0" :class="omrStore.activePaperIsOvertime ? 'text-rose-400' : 'text-emerald-400'">
                  已耗时: {{ currentSecElapsedStr }}
                </span>
              </div>

              <!-- 模块建议用时对比进度条 -->
              <div class="space-y-1">
                <div class="w-full bg-white/15 h-2 rounded-full overflow-hidden">
                  <div
                    class="h-full transition-all duration-300"
                    :class="omrStore.activePaperIsOvertime ? 'bg-rose-500' : (omrStore.activePaperProgressPct > 80 ? 'bg-amber-400' : 'bg-blue-400')"
                    :style="{ width: `${Math.min(100, omrStore.activePaperProgressPct)}%` }"
                  ></div>
                </div>
                <div class="flex justify-between text-[10px] text-slate-400 font-medium">
                  <span>建议单题 {{ omrStore.activePaperBenchmark?.perQSec || 50 }}s</span>
                  <span>建议模块总时 {{ Math.round(omrStore.activePaperTargetSeconds / 60) }}分钟</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 底部控制栏：专为手机单手大拇指优化 (上排双按钮+下排全宽大按钮) -->
          <div class="shrink-0 pt-3 border-t border-white/10 space-y-2.5 w-full max-w-xl mx-auto">
            <!-- 上排双按钮：暂停/继续 (4列) + 完成当前模块打卡 (8列) -->
            <div class="grid grid-cols-12 gap-2.5">
              <button
                type="button"
                @click="omrStore.pauseMockExam"
                v-if="omrStore.examTimerStatus === 'running'"
                class="col-span-4 py-3 sm:py-3.5 rounded-2xl bg-white/15 hover:bg-white/25 active:scale-98 text-white font-bold text-xs sm:text-sm flex items-center justify-center space-x-1.5 transition cursor-pointer"
              >
                <i class="fa-solid fa-pause text-xs"></i>
                <span>暂停</span>
              </button>
              <button
                type="button"
                @click="omrStore.resumeMockExam"
                v-else
                class="col-span-4 py-3 sm:py-3.5 rounded-2xl bg-blue-600 hover:bg-blue-500 active:scale-98 text-white font-bold text-xs sm:text-sm flex items-center justify-center space-x-1.5 transition cursor-pointer"
              >
                <i class="fa-solid fa-play text-xs"></i>
                <span>继续</span>
              </button>

              <button
                type="button"
                @click="handleLapSection"
                class="col-span-8 py-3 sm:py-3.5 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 active:scale-98 text-white font-black text-xs sm:text-sm shadow-md flex items-center justify-center space-x-2 transition cursor-pointer"
              >
                <i class="fa-solid fa-flag-checkered text-xs sm:text-sm text-blue-200"></i>
                <span>完成本模块打卡 (切下一模块)</span>
              </button>
            </div>

            <!-- 下排通栏大按钮：作答完毕，去拍照批改 -->
            <button
              type="button"
              @click="handleFinishAndGradeFullscreen"
              class="w-full py-3.5 sm:py-4 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 active:scale-98 text-white font-black text-sm sm:text-base shadow-lg flex items-center justify-center space-x-2 transition cursor-pointer"
            >
              <i class="fa-solid fa-camera text-base text-emerald-200"></i>
              <span>📸 纸质作答完毕，去拍照批改</span>
            </button>
          </div>
        </template>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { useOmrStore } from '../../stores/omr';
import { EXAM_DURATION_PRESETS, formatSecondsToChinese, getSectionBenchmark } from '../../constants/examTiming';
import { requestFullscreenSafe, exitFullscreenSafe, lockBodyScroll, lockOrientationSafe, unlockOrientationSafe } from '../../utils/fullscreenHelper';

const omrStore = useOmrStore();
const emit = defineEmits(['trigger-camera']);

const selectedDurationMin = ref(120);
const durationOptions = EXAM_DURATION_PRESETS;

const tempManualMinutes = ref({});

// 横竖屏自适应与强制切换状态
const forcedOrientation = ref('auto'); // 'auto' | 'landscape' | 'portrait'
const deviceIsLandscape = ref(false);
const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024);
const isDesktop = computed(() => windowWidth.value >= 1024);

function updateDeviceOrientation() {
  if (typeof window !== 'undefined') {
    windowWidth.value = window.innerWidth;
    deviceIsLandscape.value = window.innerWidth > window.innerHeight;
  }
}

// 电脑端全屏键盘快捷键监听
function handleKeydown(e) {
  if (!omrStore.isFullscreenPaperTimer) return;
  // 忽略输入框或文本域内触发的按键
  if (['INPUT', 'TEXTAREA'].includes(e.target?.tagName)) return;

  if (e.code === 'Space') {
    e.preventDefault();
    handleLapSection();
  } else if (e.code === 'KeyP') {
    e.preventDefault();
    if (omrStore.examTimerStatus === 'running') {
      omrStore.pauseMockExam();
    } else if (omrStore.examTimerStatus === 'paused') {
      omrStore.resumeMockExam();
    }
  } else if (e.code === 'Enter') {
    e.preventDefault();
    handleFinishAndGradeFullscreen();
  } else if (e.code === 'Escape') {
    exitFullscreenView();
  }
}

const effectiveIsLandscape = computed(() => {
  if (forcedOrientation.value === 'landscape') return true;
  if (forcedOrientation.value === 'portrait') return false;
  return deviceIsLandscape.value;
});

const needsCssRotation = computed(() => {
  // 物理上为竖屏，但用户主动点击了切换为横屏
  return forcedOrientation.value === 'landscape' && !deviceIsLandscape.value;
});

const fullscreenContainerStyle = computed(() => {
  const basePadding = {
    paddingTop: 'max(12px, env(safe-area-inset-top))',
    paddingBottom: 'max(16px, env(safe-area-inset-bottom))',
    paddingLeft: 'max(16px, env(safe-area-inset-left))',
    paddingRight: 'max(16px, env(safe-area-inset-right))',
  };

  if (needsCssRotation.value) {
    // 强制 90 度旋转居中填充全屏，用户横放手机即为正立横屏
    return {
      ...basePadding,
      position: 'fixed',
      top: 'calc((100dvh - 100dvw) / 2)',
      left: 'calc((100dvw - 100dvh) / 2)',
      width: '100dvh',
      height: '100dvw',
      transform: 'rotate(90deg)',
      transformOrigin: 'center center',
      zIndex: 9999,
    };
  }

  return {
    ...basePadding,
    position: 'fixed',
    top: '0px',
    left: '0px',
    right: '0px',
    bottom: '0px',
    width: '100vw',
    height: '100dvh',
    zIndex: 9999,
  };
});

async function toggleOrientation() {
  if (effectiveIsLandscape.value) {
    forcedOrientation.value = 'portrait';
    unlockOrientationSafe();
  } else {
    forcedOrientation.value = 'landscape';
    await lockOrientationSafe('landscape');
  }
}

const orientationToggleText = computed(() => {
  return effectiveIsLandscape.value ? '竖屏' : '横屏';
});

const orientationToggleIcon = computed(() => {
  return effectiveIsLandscape.value ? 'fa-solid fa-mobile text-[11px]' : 'fa-solid fa-mobile-screen-button rotate-90 text-[11px]';
});

onMounted(() => {
  initManualTimes();
  updateDeviceOrientation();
  window.addEventListener('resize', updateDeviceOrientation);
  window.addEventListener('orientationchange', updateDeviceOrientation);
  window.addEventListener('keydown', handleKeydown);
});

onBeforeUnmount(() => {
  omrStore.releaseScreenWakeLock();
  lockBodyScroll(false);
  unlockOrientationSafe();
  window.removeEventListener('resize', updateDeviceOrientation);
  window.removeEventListener('orientationchange', updateDeviceOrientation);
  window.removeEventListener('keydown', handleKeydown);
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
  exitFullscreenView();
  handleFinishAndGrade();
}

function exitFullscreenView() {
  omrStore.isFullscreenPaperTimer = false;
  lockBodyScroll(false);
  exitFullscreenSafe();
}

watch(() => omrStore.isFullscreenPaperTimer, (val) => {
  if (val) {
    lockBodyScroll(true);
    requestFullscreenSafe();
  } else {
    lockBodyScroll(false);
    exitFullscreenSafe();
  }
});

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
