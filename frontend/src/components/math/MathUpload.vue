<template>
  <section class="space-y-4">
    <!-- ⏱️ 速算沉浸式竞速计时控制台卡片 -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200/90 shadow-2xs space-y-3.5">
      <!-- 顶部中控台：模式切换与辅助工具开关 -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-1 border-b border-slate-100">
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
            <span>⏱️ 速算实战竞速计时器</span>
            <span
              v-if="mathStore.timerStatus === 'running'"
              class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-700 flex items-center space-x-1 animate-pulse"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <span>极速挑战中</span>
            </span>
            <span
              v-else-if="mathStore.timerStatus === 'paused'"
              class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-amber-100 text-amber-700"
            >
              已暂停
            </span>
            <span
              v-else-if="mathStore.timerStatus === 'finished'"
              class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-blue-100 text-blue-700"
            >
              挑战完成
            </span>
          </h3>
        </div>

        <!-- 模式与工具控制胶囊 -->
        <div class="flex items-center space-x-1.5 flex-wrap gap-y-1">
          <!-- 计时模式切换 (秒表 vs 极速倒计时) -->
          <div class="flex bg-slate-100 p-0.5 rounded-xl text-xs font-semibold">
            <button
              type="button"
              @click="switchTimerMode('stopwatch')"
              :class="mathStore.timerMode === 'stopwatch' ? 'py-1 px-2.5 rounded-lg bg-white shadow-xs text-slate-800 transition font-bold' : 'py-1 px-2.5 rounded-lg text-slate-500 hover:text-slate-800 transition cursor-pointer'"
            >
              正向秒表
            </button>
            <button
              type="button"
              @click="switchTimerMode('countdown')"
              :class="mathStore.timerMode === 'countdown' ? 'py-1 px-2.5 rounded-lg bg-white shadow-xs text-slate-800 transition font-bold' : 'py-1 px-2.5 rounded-lg text-slate-500 hover:text-slate-800 transition cursor-pointer'"
            >
              极速挑战
            </button>
          </div>

          <!-- 屏幕防休眠常亮开关 -->
          <button
            type="button"
            @click="toggleWakeLock"
            class="px-2 py-1 rounded-lg text-[11px] font-medium border transition flex items-center space-x-1 cursor-pointer"
            :class="mathStore.isScreenWakeLocked
              ? 'bg-amber-50 border-amber-300 text-amber-800 font-bold shadow-2xs'
              : 'bg-slate-50 border-slate-200 text-slate-500 hover:text-slate-800'"
            title="保持屏幕常亮不黑屏，方便草稿计算时看时间"
          >
            <i class="fa-solid fa-sun text-[10px]" :class="mathStore.isScreenWakeLocked ? 'text-amber-500' : ''"></i>
            <span>{{ mathStore.isScreenWakeLocked ? '常亮已开' : '常亮' }}</span>
          </button>

          <!-- 声音提示切换 -->
          <button
            type="button"
            @click="cycleSoundMode"
            class="px-2 py-1 rounded-lg text-[11px] font-medium border transition flex items-center space-x-1 cursor-pointer bg-slate-50 border-slate-200 text-slate-600 hover:text-slate-900"
            :title="soundModeTitle"
          >
            <i :class="soundModeIcon"></i>
            <span>{{ soundModeLabel }}</span>
          </button>

          <!-- 全屏竞速大钟 -->
          <button
            type="button"
            @click="mathStore.isFullscreenTimer = true"
            class="px-2 py-1 rounded-lg text-[11px] font-medium border transition flex items-center space-x-1 cursor-pointer bg-slate-50 border-slate-200 text-slate-600 hover:text-emerald-700 hover:border-emerald-300"
            title="进入纯黑沉浸全屏竞速大钟"
          >
            <i class="fa-solid fa-expand text-[10px]"></i>
            <span>全屏</span>
          </button>
        </div>
      </div>

      <!-- ⏱️ 大字数码时钟与实时配速画像显示区 -->
      <div
        :class="[
          'rounded-2xl p-4 sm:p-5 border transition-all duration-300 text-center relative overflow-hidden',
          mathStore.isCountdownCritical
            ? 'bg-gradient-to-br from-rose-50 via-red-50 to-amber-50 border-rose-300 ring-2 ring-rose-400/50 text-rose-900 shadow-md'
            : (mathStore.isCountdownWarning
              ? 'bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 border-amber-300 text-amber-950 shadow-sm'
              : (mathStore.timerStatus === 'running'
                ? 'bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 text-white border-emerald-700 shadow-md'
                : 'bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 text-white border-slate-700 shadow-sm'))
        ]"
      >
        <!-- 顶部冲刺提醒 -->
        <div
          class="text-[11px] font-bold tracking-wide flex items-center justify-center space-x-1.5 mb-1"
          :class="mathStore.isCountdownCritical ? 'text-rose-600 animate-bounce' : (mathStore.isCountdownWarning ? 'text-amber-700' : 'text-slate-300')"
        >
          <i class="fa-regular fa-clock text-xs"></i>
          <span v-if="mathStore.timerMode === 'countdown'">
            {{ mathStore.isCountdownCritical ? '🚨 极限最后冲刺！立即完成收尾' : (mathStore.isCountdownWarning ? '⚠️ 挑战进入最后 1 分钟倒数' : `限时挑战目标: ${mathStore.countdownTargetMinutes} 分钟`) }}
          </span>
          <span v-else>速算刷题累计用时秒表 (自由做题)</span>
        </div>

        <!-- 数码时间 -->
        <div
          :class="[
            'font-mono font-black text-5xl sm:text-6xl tracking-wider my-1 select-none',
            mathStore.isCountdownCritical ? 'text-rose-600 animate-pulse' : (mathStore.isCountdownWarning ? 'text-amber-800' : 'text-white')
          ]"
        >
          {{ mathStore.formattedTimer }}
        </div>

        <!-- 🏆 实时单题配速与段位动态仪表条 -->
        <div
          v-if="mathStore.timerStatus !== 'idle'"
          class="mt-2.5 pt-2 border-t max-w-lg mx-auto flex items-center justify-between text-xs px-2"
          :class="mathStore.isCountdownCritical || mathStore.isCountdownWarning ? 'border-amber-200 text-slate-800' : 'border-white/10 text-slate-200'"
        >
          <div class="flex items-center space-x-1.5">
            <span class="text-[11px] opacity-75">实时配速:</span>
            <span class="font-mono font-bold text-sm" :class="mathStore.isCountdownCritical || mathStore.isCountdownWarning ? 'text-slate-900' : 'text-emerald-400'">
              {{ mathStore.realtimePace > 0 ? `${mathStore.realtimePace} 秒/题` : '--' }}
            </span>
            <span class="text-[10px] opacity-60">({{ mathStore.targetItemCount }}题)</span>
          </div>

          <div class="flex items-center space-x-1">
            <span class="text-[11px] opacity-75">当前段位:</span>
            <span class="px-2 py-0.5 rounded-full text-[11px] border font-bold flex items-center space-x-1" :class="mathStore.speedRank.badgeClass">
              <span>{{ mathStore.speedRank.icon }}</span>
              <span>{{ mathStore.speedRank.level }}</span>
            </span>
          </div>
        </div>

        <!-- 预设时长与题量配置栏 (未开始时显示) -->
        <div v-if="mathStore.timerStatus === 'idle'" class="space-y-2 mt-3 pt-2.5 border-t border-white/10">
          <!-- 预设计划题量 -->
          <div class="flex items-center justify-center space-x-1.5 flex-wrap gap-y-1 text-xs">
            <span class="text-[11px] text-slate-400 mr-0.5">计划练习题量:</span>
            <button
              v-for="cnt in [10, 20, 30, 50, 100]"
              :key="cnt"
              type="button"
              @click="mathStore.targetItemCount = cnt"
              :class="[
                'px-2 py-0.5 rounded-lg text-xs font-semibold transition cursor-pointer',
                mathStore.targetItemCount === cnt
                  ? 'bg-emerald-500 text-white font-bold shadow-xs'
                  : 'bg-white/10 hover:bg-white/20 text-slate-200'
              ]"
            >
              {{ cnt }}题
            </button>
          </div>

          <!-- 倒计时极速时长 -->
          <div v-if="mathStore.timerMode === 'countdown'" class="flex items-center justify-center space-x-1 flex-wrap gap-y-1 text-xs">
            <span class="text-[11px] text-slate-400 mr-0.5">挑战时长:</span>
            <button
              v-for="mins in [1, 2, 3, 5, 8, 10, 15, 20]"
              :key="mins"
              type="button"
              @click="mathStore.setCountdownMinutes(mins)"
              :class="[
                'px-2 py-0.5 rounded-lg text-xs font-semibold transition cursor-pointer',
                mathStore.countdownTargetMinutes === mins
                  ? 'bg-blue-600 text-white font-bold shadow-xs'
                  : 'bg-white/10 hover:bg-white/20 text-slate-200'
              ]"
            >
              {{ mins }}分钟
            </button>
          </div>
        </div>

        <!-- 控制器按钮区 -->
        <div class="flex items-center justify-center space-x-2 mt-3.5 flex-wrap gap-y-1.5">
          <!-- 未开始状态 -->
          <template v-if="mathStore.timerStatus === 'idle'">
            <button
              type="button"
              @click="mathStore.startTimer"
              class="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold text-xs sm:text-sm shadow-md transition flex items-center space-x-2 active:scale-95 cursor-pointer"
            >
              <i class="fa-solid fa-play text-xs"></i>
              <span>开始速算挑战</span>
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
              @click="handleLap"
              class="px-3.5 py-2 rounded-xl bg-white/20 hover:bg-white/30 text-white font-bold text-xs transition flex items-center space-x-1.5 active:scale-95 cursor-pointer"
              title="记录分段耗时"
            >
              <i class="fa-solid fa-flag-checkered text-xs"></i>
              <span>打卡</span>
            </button>
            <button
              type="button"
              @click="handleFinishPractice"
              class="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-bold text-xs shadow-md transition flex items-center space-x-1.5 active:scale-95 cursor-pointer"
            >
              <i class="fa-solid fa-check text-xs"></i>
              <span>⏹ 完成，准备批改</span>
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
              <span>继续挑战</span>
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
              class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold text-xs sm:text-sm shadow-md transition flex items-center space-x-2 active:scale-95 cursor-pointer"
            >
              <i class="fa-solid fa-camera text-sm"></i>
              <span>📸 立即拍照批改练习册</span>
            </button>
            <button
              type="button"
              @click="mathStore.resetTimer"
              class="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-xs transition flex items-center space-x-1 cursor-pointer"
            >
              <i class="fa-solid fa-arrows-rotate text-[10px]"></i>
              <span>再练一次</span>
            </button>
          </template>
        </div>
      </div>

      <!-- 分段打卡记录 (Lap List) -->
      <div v-if="mathStore.laps.length > 0" class="bg-slate-50 p-2.5 rounded-xl border border-slate-200/80 space-y-1.5 text-xs">
        <div class="flex items-center justify-between text-slate-400 text-[10px] pb-1 border-b border-slate-200">
          <span>分段打卡记录 (共 {{ mathStore.laps.length }} 阶段)</span>
          <button type="button" @click="mathStore.laps = []" class="hover:text-rose-600">清空打卡</button>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
          <div
            v-for="lap in mathStore.laps"
            :key="lap.id"
            class="bg-white p-1.5 rounded-lg border border-slate-200 text-[11px] flex items-center justify-between"
          >
            <span class="text-slate-600 font-medium">{{ lap.label }}</span>
            <span class="font-mono font-bold text-emerald-700">{{ lap.lapTimeStr }}</span>
          </div>
        </div>
      </div>

      <!-- 用时微调与常用快捷胶囊 -->
      <div class="bg-slate-50/80 p-3 rounded-xl border border-slate-200/80 space-y-2 text-xs">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div class="flex items-center space-x-1.5">
            <i class="fa-regular fa-clock text-emerald-600"></i>
            <span class="text-slate-500">当前记录用时:</span>
            <b class="text-slate-800 font-mono text-sm">{{ mathStore.timeStr }}</b>
            <span v-if="mathStore.realtimePace > 0" class="text-[11px] text-slate-400">
              (折合 {{ mathStore.realtimePace }} 秒/题)
            </span>
          </div>

          <!-- 加减秒微调快捷键 -->
          <div class="flex items-center space-x-1">
            <span class="text-[10px] text-slate-400 mr-0.5">微调:</span>
            <button
              type="button"
              @click="mathStore.adjustTimeSeconds(-30)"
              class="px-1.5 py-0.5 rounded bg-white hover:bg-slate-100 border border-slate-200 text-[10px] font-mono font-bold text-slate-700 cursor-pointer"
            >
              -30s
            </button>
            <button
              type="button"
              @click="mathStore.adjustTimeSeconds(-10)"
              class="px-1.5 py-0.5 rounded bg-white hover:bg-slate-100 border border-slate-200 text-[10px] font-mono font-bold text-slate-700 cursor-pointer"
            >
              -10s
            </button>
            <button
              type="button"
              @click="mathStore.adjustTimeSeconds(10)"
              class="px-1.5 py-0.5 rounded bg-white hover:bg-slate-100 border border-slate-200 text-[10px] font-mono font-bold text-slate-700 cursor-pointer"
            >
              +10s
            </button>
            <button
              type="button"
              @click="mathStore.adjustTimeSeconds(30)"
              class="px-1.5 py-0.5 rounded bg-white hover:bg-slate-100 border border-slate-200 text-[10px] font-mono font-bold text-slate-700 cursor-pointer"
            >
              +30s
            </button>
            <input
              type="text"
              v-model="mathStore.timeStr"
              placeholder="如 4分20秒"
              class="border border-slate-200 rounded px-1.5 py-0.5 w-20 text-center text-xs font-mono text-slate-700 focus:outline-none focus:border-emerald-500 bg-white ml-1"
            >
          </div>
        </div>

        <!-- 常用速算完成用时一键选 -->
        <div class="flex items-center space-x-1 text-[11px] text-slate-400 flex-wrap gap-y-1">
          <span>快捷填入:</span>
          <button
            v-for="quick in ['1分30秒', '2分45秒', '4分20秒', '6分00秒', '8分30秒', '12分00秒']"
            :key="quick"
            type="button"
            @click="setQuickTime(quick)"
            class="px-2 py-0.5 rounded-md bg-white hover:bg-slate-100 border border-slate-200 text-slate-600 text-[10px] font-mono transition cursor-pointer"
          >
            {{ quick }}
          </button>
        </div>
      </div>
    </div>

    <!-- 📸 拍照与上传交互横幅卡片 -->
    <div class="bg-gradient-to-br from-emerald-600 to-teal-700 rounded-2xl p-5 text-white shadow-md relative overflow-hidden space-y-4">
      <div class="relative z-10 space-y-3">
        <div>
          <h2 class="text-xl font-bold mb-1">对准练习册，一键拍照批改</h2>
          <p class="text-emerald-100 text-xs leading-relaxed">
            自动校正拍摄倾斜与透视，智能辨识手写笔迹并红绿勾叉标注，自动核算单题平均耗时与段位评价。
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
          <div class="text-[9px] text-slate-400 mt-0.5">王者级直加直减</div>
        </div>
        <div class="p-2 rounded-xl bg-slate-50 border border-slate-200/70">
          <div class="text-slate-400 text-[10px]">两位数乘法</div>
          <div class="font-bold text-blue-700 mt-0.5">≤ 12 秒/题</div>
          <div class="text-[9px] text-slate-400 mt-0.5">拆分乘与尾数法</div>
        </div>
        <div class="p-2 rounded-xl bg-slate-50 border border-slate-200/70">
          <div class="text-slate-400 text-[10px]">多位数截位除</div>
          <div class="font-bold text-amber-700 mt-0.5">≤ 15~18 秒/题</div>
          <div class="text-[9px] text-slate-400 mt-0.5">保留三位直除</div>
        </div>
      </div>
    </div>

    <!-- ⛶ 沉浸全屏大字竞速看板 (Teleport 到 body 彻底杜绝漏底，支持横竖屏自由旋转与切换) -->
    <Teleport to="body">
      <div
        v-if="mathStore.isFullscreenTimer"
        class="fixed inset-0 z-[9999] bg-black text-white flex flex-col justify-between select-none overflow-hidden"
        :style="fullscreenContainerStyle"
      >
        <!-- 全屏顶部状态栏 (适配刘海与安全区) -->
        <div class="flex items-center justify-between border-b border-white/10 pb-2.5 shrink-0">
          <div class="flex items-center space-x-2 min-w-0">
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse shrink-0"></span>
            <div class="min-w-0">
              <h4 class="font-bold text-sm sm:text-base tracking-wide text-slate-100 truncate">
                速算竞速伴考看板
              </h4>
              <div class="flex items-center space-x-2 text-[10px] text-slate-400 font-mono mt-0.5">
                <span>计划 {{ mathStore.targetItemCount }} 题 · {{ mathStore.timerMode === 'countdown' ? `${mathStore.countdownTargetMinutes}m挑战` : '秒表' }}</span>
                <span>·</span>
                <button
                  type="button"
                  @click="toggleWakeLock"
                  class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold border transition cursor-pointer"
                  :class="mathStore.isScreenWakeLocked
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30 shadow-2xs'
                    : 'bg-white/10 text-slate-300 border-white/15 hover:bg-white/20'"
                  title="点击可手动切换屏幕常亮防息屏"
                >
                  <i class="fa-solid fa-sun text-[9px]" :class="mathStore.isScreenWakeLocked ? 'text-amber-300' : ''"></i>
                  <span>{{ mathStore.isScreenWakeLocked ? '常亮防息屏中' : '常亮已关' }}</span>
                </button>
              </div>
            </div>
          </div>

          <!-- 右侧：快捷键提示 + 横竖屏切换 + 段位胶囊 + 声音开关 + 退出全屏 -->
          <div class="flex items-center space-x-2 shrink-0">
            <!-- 电脑端专属快捷键提示 -->
            <div v-if="isDesktop" class="hidden lg:flex items-center space-x-2 text-[11px] text-slate-400 bg-white/5 border border-white/10 px-3 py-1 rounded-xl">
              <span>按 <kbd class="bg-white/20 px-1.5 py-0.5 rounded text-[10px] font-mono text-white font-bold">Space</kbd> 打卡</span>
              <span>·</span>
              <span>按 <kbd class="bg-white/20 px-1.5 py-0.5 rounded text-[10px] font-mono text-white font-bold">P</kbd> 暂停/继续</span>
              <span>·</span>
              <span>按 <kbd class="bg-white/20 px-1.5 py-0.5 rounded text-[10px] font-mono text-white font-bold">Esc</kbd> 退出</span>
            </div>

            <!-- 手机端横竖屏切换按钮 (电脑端自动隐藏) -->
            <button
              v-if="!isDesktop"
              type="button"
              @click="toggleOrientation"
              class="px-2.5 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 active:bg-white/30 text-slate-200 text-xs font-semibold flex items-center space-x-1 transition cursor-pointer"
              :title="effectiveIsLandscape ? '点击切换为竖屏模式' : '点击切换为横屏桌面竞速模式'"
            >
              <i :class="orientationToggleIcon"></i>
              <span>{{ orientationToggleText }}</span>
            </button>

            <span class="text-[11px] px-2.5 py-0.5 rounded-full border font-bold flex items-center space-x-1" :class="mathStore.speedRank.badgeClass">
              <span>{{ mathStore.speedRank.icon }}</span>
              <span>{{ mathStore.speedRank.level }}</span>
            </span>

            <button
              type="button"
              @click="cycleSoundMode"
              class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 active:bg-white/30 text-slate-300 hover:text-white flex items-center justify-center text-xs transition cursor-pointer"
              :title="soundModeTitle"
            >
              <i :class="soundModeIcon"></i>
            </button>

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

        <!-- 🖥️ 1. 电脑宽屏专属布局 (Desktop Mode)：宽屏双翼中控台，左侧超大时钟，右侧配速段位与打卡记录 -->
        <div v-if="isDesktop" class="flex-1 min-h-0 grid grid-cols-12 gap-6 py-4 items-center w-full max-w-7xl mx-auto px-4">
          <!-- 左翼 (7列)：时钟 + 配速 + 大按钮 -->
          <div class="col-span-7 flex flex-col justify-center items-center text-center space-y-5 pr-4 border-r border-white/10 h-full">
            <span
              class="text-xs sm:text-sm font-bold tracking-widest px-4 py-1 rounded-full border uppercase shadow-2xs"
              :class="mathStore.isCountdownCritical
                ? 'bg-rose-950/80 border-rose-500 text-rose-400 animate-pulse'
                : (mathStore.isCountdownWarning
                  ? 'bg-amber-950/80 border-amber-500 text-amber-300'
                  : 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300')"
            >
              {{ mathStore.timerMode === 'countdown' ? (mathStore.isCountdownCritical ? '🚨 极限最后冲刺' : (mathStore.isCountdownWarning ? '⚠️ 挑战进入最后 1 分钟' : `极速限时挑战剩余 (目标 ${mathStore.countdownTargetMinutes} 分钟)`)) : '速算刷题累计用时秒表' }}
            </span>

            <!-- 超大等宽数码管液晶时钟 -->
            <div
              class="font-mono tabular-nums font-black text-8xl xl:text-9xl 2xl:text-[10rem] tracking-tight select-none leading-none drop-shadow-lg my-2"
              :class="mathStore.isCountdownCritical ? 'text-rose-500 animate-pulse' : (mathStore.isCountdownWarning ? 'text-amber-400' : 'text-emerald-400')"
            >
              {{ mathStore.formattedTimer }}
            </div>

            <!-- 实时单题配速与段位卡片 -->
            <div class="w-full max-w-lg bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/15 space-y-2 text-center shadow-lg">
              <div class="flex items-center justify-center space-x-3 text-base text-slate-200">
                <span class="text-xs text-slate-400">实测配速:</span>
                <b class="text-emerald-400 font-mono font-black text-2xl">
                  {{ mathStore.realtimePace > 0 ? `${mathStore.realtimePace} 秒/题` : '--' }}
                </b>
                <span class="text-xs text-slate-400">(计划 {{ mathStore.targetItemCount }} 题)</span>
              </div>
              <div class="text-sm text-slate-300 font-medium">
                评价: <span class="font-bold text-white">{{ mathStore.speedRank.text }}</span>
              </div>
            </div>

            <!-- 控制按钮栏 -->
            <div class="w-full max-w-lg grid grid-cols-12 gap-3 pt-2">
              <button
                type="button"
                @click="mathStore.pauseTimer"
                v-if="mathStore.timerStatus === 'running'"
                class="col-span-4 py-3 rounded-xl bg-white/15 hover:bg-white/25 active:scale-98 text-white font-bold text-xs sm:text-sm flex items-center justify-center space-x-1.5 transition cursor-pointer"
              >
                <i class="fa-solid fa-pause text-xs"></i>
                <span>暂停 (P)</span>
              </button>
              <button
                type="button"
                @click="mathStore.resumeTimer"
                v-else
                class="col-span-4 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-98 text-white font-bold text-xs sm:text-sm flex items-center justify-center space-x-1.5 transition cursor-pointer"
              >
                <i class="fa-solid fa-play text-xs"></i>
                <span>继续 (P)</span>
              </button>

              <button
                type="button"
                @click="handleLap"
                class="col-span-8 py-3 rounded-xl bg-white/15 hover:bg-white/25 active:scale-98 text-white font-black text-xs sm:text-sm shadow-md flex items-center justify-center space-x-2 transition cursor-pointer"
              >
                <i class="fa-solid fa-flag-checkered text-xs text-emerald-300"></i>
                <span>分段打卡 (Space) {{ mathStore.laps.length > 0 ? `(${mathStore.laps.length})` : '' }}</span>
              </button>

              <button
                type="button"
                @click="handleFullscreenFinishAndGrade"
                class="col-span-12 py-3.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 active:scale-98 text-white font-black text-sm shadow-lg flex items-center justify-center space-x-2 transition cursor-pointer"
              >
                <i class="fa-solid fa-camera text-base text-emerald-200"></i>
                <span>📸 完成做题，立即拍照批改 (Enter)</span>
              </button>
            </div>
          </div>

          <!-- 右翼 (5列)：黄金配速标尺与分段打卡表格 -->
          <div class="col-span-5 flex flex-col justify-center space-y-3 h-full pl-2">
            <!-- 标尺卡片 -->
            <div class="bg-white/5 rounded-2xl p-4 border border-white/10 space-y-2">
              <div class="flex items-center justify-between pb-1 border-b border-white/10 text-xs text-slate-300 font-bold">
                <span>公考行测速算黄金标尺</span>
                <span class="text-[10px] text-emerald-400">资料分析实战基准</span>
              </div>
              <div class="grid grid-cols-3 gap-2 text-center text-xs">
                <div class="p-2 rounded-xl bg-white/5 border border-white/10">
                  <div class="text-[10px] text-slate-400">加减心算</div>
                  <div class="font-bold text-emerald-400 mt-0.5">≤ 8s/题</div>
                </div>
                <div class="p-2 rounded-xl bg-white/5 border border-white/10">
                  <div class="text-[10px] text-slate-400">乘法拆分</div>
                  <div class="font-bold text-blue-400 mt-0.5">≤ 12s/题</div>
                </div>
                <div class="p-2 rounded-xl bg-white/5 border border-white/10">
                  <div class="text-[10px] text-slate-400">截位直除</div>
                  <div class="font-bold text-amber-400 mt-0.5">≤ 18s/题</div>
                </div>
              </div>
            </div>

            <!-- 分段打卡历史表格 -->
            <div class="bg-white/5 rounded-2xl p-4 border border-white/10 space-y-2 flex-1 max-h-[48vh] flex flex-col">
              <div class="flex items-center justify-between text-xs pb-1 border-b border-white/10">
                <span class="font-bold text-slate-300">分段打卡记录 (按空格键打卡)</span>
                <span class="text-[10px] text-slate-400">共 {{ mathStore.laps.length }} 阶段</span>
              </div>
              <div v-if="mathStore.laps.length === 0" class="my-auto text-center text-xs text-slate-500 py-6">
                暂无打卡记录，做题中按【Space】打卡记录每阶段用时
              </div>
              <div v-else class="overflow-y-auto space-y-1.5 flex-1 pr-1">
                <div
                  v-for="lap in mathStore.laps"
                  :key="lap.id"
                  class="p-2 rounded-xl bg-white/5 border border-white/10 text-xs flex items-center justify-between"
                >
                  <span class="text-slate-300 font-medium">{{ lap.label }}</span>
                  <div class="flex items-center space-x-2">
                    <span class="font-mono font-bold text-emerald-400">{{ lap.lapTimeStr }}</span>
                    <span class="text-[10px] text-slate-500">(总计 {{ lap.totalTimeStr }})</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 📱 2. 手机横屏模式 (Mobile Landscape)：左右双栏布局 -->
        <div v-else-if="effectiveIsLandscape" class="flex-1 min-h-0 flex items-center justify-between gap-4 py-2">
          <!-- 左侧：超大液晶数码管时钟与配速卡片 -->
          <div class="flex-1 flex flex-col justify-center items-center text-center space-y-2 min-w-0 pr-2">
            <span
              class="text-xs font-bold tracking-widest px-3.5 py-0.5 rounded-full border uppercase shrink-0 shadow-2xs"
              :class="mathStore.isCountdownCritical
                ? 'bg-rose-950/80 border-rose-500 text-rose-400 animate-pulse'
                : (mathStore.isCountdownWarning
                  ? 'bg-amber-950/80 border-amber-500 text-amber-300'
                  : 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300')"
            >
              {{ mathStore.timerMode === 'countdown' ? (mathStore.isCountdownCritical ? '🚨 极限最后冲刺' : (mathStore.isCountdownWarning ? '⚠️ 挑战进入最后 1 分钟' : '极速限时挑战剩余')) : '刷题累计用时秒表' }}
            </span>

            <!-- 超大液晶时钟 -->
            <div
              class="font-mono tabular-nums font-black text-6xl sm:text-7xl md:text-8xl lg:text-9xl tracking-tight select-none leading-none drop-shadow-md my-1"
              :class="mathStore.isCountdownCritical ? 'text-rose-500 animate-pulse' : (mathStore.isCountdownWarning ? 'text-amber-400' : 'text-emerald-400')"
            >
              {{ mathStore.formattedTimer }}
            </div>

            <!-- 实时单题配速与段位卡片 -->
            <div class="w-full max-w-lg bg-white/10 backdrop-blur-md rounded-xl px-4 py-2 border border-white/15 space-y-1 text-center shadow-lg">
              <div class="flex items-center justify-center space-x-2 text-sm sm:text-base text-slate-200">
                <span class="text-xs text-slate-400">实测配速:</span>
                <b class="text-emerald-400 font-mono font-black text-base sm:text-lg">
                  {{ mathStore.realtimePace > 0 ? `${mathStore.realtimePace} 秒/题` : '--' }}
                </b>
                <span class="text-xs text-slate-400">({{ mathStore.targetItemCount }}题)</span>
                <span class="text-slate-500">·</span>
                <span class="text-xs font-bold text-white">{{ mathStore.speedRank.text }}</span>
              </div>
            </div>
          </div>

          <!-- 右侧：垂直排列大按钮 (适合桌面横放盲点) -->
          <div class="w-64 sm:w-72 shrink-0 flex flex-col justify-center space-y-2.5 pl-3 border-l border-white/10 h-full py-1">
            <!-- 分段打卡 -->
            <button
              type="button"
              @click="handleLap"
              class="w-full py-3.5 sm:py-4 rounded-2xl bg-white/15 hover:bg-white/25 active:scale-98 text-white font-black text-xs sm:text-sm shadow-md flex items-center justify-center space-x-2 transition cursor-pointer"
            >
              <i class="fa-solid fa-flag-checkered text-xs text-emerald-300"></i>
              <span>分段打卡 {{ mathStore.laps.length > 0 ? `(${mathStore.laps.length})` : '' }}</span>
            </button>

            <!-- 暂停 / 继续 -->
            <button
              type="button"
              @click="mathStore.pauseTimer"
              v-if="mathStore.timerStatus === 'running'"
              class="w-full py-2.5 rounded-xl bg-white/15 hover:bg-white/25 active:scale-98 text-white font-bold text-xs flex items-center justify-center space-x-1.5 transition cursor-pointer"
            >
              <i class="fa-solid fa-pause text-xs"></i>
              <span>暂停挑战</span>
            </button>
            <button
              type="button"
              @click="mathStore.resumeTimer"
              v-else
              class="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-98 text-white font-bold text-xs flex items-center justify-center space-x-1.5 transition cursor-pointer"
            >
              <i class="fa-solid fa-play text-xs"></i>
              <span>继续挑战</span>
            </button>

            <!-- 完成做题拍照批改 -->
            <button
              type="button"
              @click="handleFullscreenFinishAndGrade"
              class="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 active:scale-98 text-white font-bold text-xs sm:text-sm shadow-md flex items-center justify-center space-x-1.5 transition cursor-pointer"
            >
              <i class="fa-solid fa-camera text-sm text-emerald-200"></i>
              <span>完成做题，去拍照</span>
            </button>
          </div>
        </div>

        <!-- 📱 2. 竖屏模式 (Portrait)：居中时钟 + 底部双排大拇指操作区 -->
        <template v-else>
          <!-- 居中核心时钟与实时配速卡片 -->
          <div class="my-auto py-2 flex flex-col items-center justify-center space-y-3 sm:space-y-5 text-center w-full max-w-xl mx-auto px-1">
            <!-- 挑战提示胶囊 -->
            <div class="flex items-center space-x-2">
              <span
                class="text-xs sm:text-sm font-bold tracking-widest px-3.5 py-1 rounded-full border uppercase shadow-2xs"
                :class="mathStore.isCountdownCritical
                  ? 'bg-rose-950/80 border-rose-500 text-rose-400 animate-pulse'
                  : (mathStore.isCountdownWarning
                    ? 'bg-amber-950/80 border-amber-500 text-amber-300'
                    : 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300')"
              >
                {{ mathStore.timerMode === 'countdown' ? (mathStore.isCountdownCritical ? '🚨 极限最后冲刺' : (mathStore.isCountdownWarning ? '⚠️ 挑战进入最后 1 分钟' : '极速限时挑战剩余')) : '刷题累计用时秒表' }}
              </span>
            </div>

            <!-- ⏱️ 超大等宽数码管液晶时钟 -->
            <div
              class="font-mono tabular-nums font-black text-6xl sm:text-8xl md:text-9xl tracking-tight sm:tracking-wider select-none leading-none drop-shadow-md my-1"
              :class="mathStore.isCountdownCritical ? 'text-rose-500 animate-pulse' : (mathStore.isCountdownWarning ? 'text-amber-400' : 'text-emerald-400')"
            >
              {{ mathStore.formattedTimer }}
            </div>

            <!-- 实时单题配速与段位评价卡片 -->
            <div class="w-full bg-white/10 backdrop-blur-md rounded-2xl p-3.5 sm:p-4 border border-white/15 space-y-1.5 text-center shadow-lg">
              <div class="flex items-center justify-center space-x-2 text-sm sm:text-base text-slate-200">
                <span class="text-xs text-slate-400">实测配速:</span>
                <b class="text-emerald-400 font-mono font-black text-lg sm:text-xl">
                  {{ mathStore.realtimePace > 0 ? `${mathStore.realtimePace} 秒/题` : '--' }}
                </b>
                <span class="text-xs text-slate-400">({{ mathStore.targetItemCount }}题)</span>
              </div>
              <div class="text-xs text-slate-300 font-medium">
                评价: <span class="font-bold text-white">{{ mathStore.speedRank.text }}</span>
              </div>
              <div class="text-[10px] text-slate-400 pt-0.5 border-t border-white/10 flex items-center justify-around">
                <span>王者 ≤8s/题</span>
                <span>黄金 ≤15s/题</span>
                <span>钻石 ≤25s/题</span>
              </div>
            </div>
          </div>

          <!-- 底部控制栏：专为手机单手大拇指优化 (上排双按钮+下排全宽大按钮) -->
          <div class="shrink-0 pt-3 border-t border-white/10 space-y-2.5 w-full max-w-xl mx-auto">
            <!-- 上排双按钮：暂停/继续 (6列) + 分段打卡 (6列) -->
            <div class="grid grid-cols-2 gap-2.5">
              <button
                type="button"
                @click="mathStore.pauseTimer"
                v-if="mathStore.timerStatus === 'running'"
                class="py-3 sm:py-3.5 rounded-2xl bg-white/15 hover:bg-white/25 active:scale-98 text-white font-bold text-xs sm:text-sm flex items-center justify-center space-x-1.5 transition cursor-pointer"
              >
                <i class="fa-solid fa-pause text-xs"></i>
                <span>暂停</span>
              </button>
              <button
                type="button"
                @click="mathStore.resumeTimer"
                v-else
                class="py-3 sm:py-3.5 rounded-2xl bg-emerald-600 hover:bg-emerald-500 active:scale-98 text-white font-bold text-xs sm:text-sm flex items-center justify-center space-x-1.5 transition cursor-pointer"
              >
                <i class="fa-solid fa-play text-xs"></i>
                <span>继续</span>
              </button>

              <button
                type="button"
                @click="handleLap"
                class="py-3 sm:py-3.5 rounded-2xl bg-white/15 hover:bg-white/25 active:scale-98 text-white font-bold text-xs sm:text-sm flex items-center justify-center space-x-1.5 transition cursor-pointer"
              >
                <i class="fa-solid fa-flag-checkered text-xs text-emerald-300"></i>
                <span>分段打卡 {{ mathStore.laps.length > 0 ? `(${mathStore.laps.length})` : '' }}</span>
              </button>
            </div>

            <!-- 下排通栏大按钮：完成做题，立即拍照批改 -->
            <button
              type="button"
              @click="handleFullscreenFinishAndGrade"
              class="w-full py-3.5 sm:py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 active:scale-98 text-white font-black text-sm sm:text-base shadow-lg flex items-center justify-center space-x-2 transition cursor-pointer"
            >
              <i class="fa-solid fa-camera text-base text-emerald-200"></i>
              <span>📸 完成做题，立即拍照批改</span>
            </button>
          </div>
        </template>
      </div>
    </Teleport>
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { useMathStore } from '../../stores/math';
import { useRouter } from 'vue-router';
import { requestFullscreenSafe, exitFullscreenSafe, lockBodyScroll, lockOrientationSafe, unlockOrientationSafe } from '../../utils/fullscreenHelper';

const mathStore = useMathStore();
const router = useRouter();

const cameraInput = ref(null);
const albumInput = ref(null);

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
  if (!mathStore.isFullscreenTimer) return;
  if (['INPUT', 'TEXTAREA'].includes(e.target?.tagName)) return;

  if (e.code === 'Space') {
    e.preventDefault();
    handleLap();
  } else if (e.code === 'KeyP') {
    e.preventDefault();
    if (mathStore.timerStatus === 'running') {
      mathStore.pauseTimer();
    } else if (mathStore.timerStatus === 'paused') {
      mathStore.resumeTimer();
    }
  } else if (e.code === 'Enter') {
    e.preventDefault();
    handleFullscreenFinishAndGrade();
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
  updateDeviceOrientation();
  window.addEventListener('resize', updateDeviceOrientation);
  window.addEventListener('orientationchange', updateDeviceOrientation);
  window.addEventListener('keydown', handleKeydown);
});

onBeforeUnmount(() => {
  mathStore.releaseScreenWakeLock();
  lockBodyScroll(false);
  unlockOrientationSafe();
  window.removeEventListener('resize', updateDeviceOrientation);
  window.removeEventListener('orientationchange', updateDeviceOrientation);
  window.removeEventListener('keydown', handleKeydown);
});

function exitFullscreenView() {
  mathStore.isFullscreenTimer = false;
  lockBodyScroll(false);
  exitFullscreenSafe();
}

watch(() => mathStore.isFullscreenTimer, (val) => {
  if (val) {
    lockBodyScroll(true);
    requestFullscreenSafe();
  } else {
    lockBodyScroll(false);
    exitFullscreenSafe();
  }
});

// 模式切换
function switchTimerMode(mode) {
  if (mathStore.timerStatus === 'running') {
    if (!confirm('计时正在进行中，切换模式将重置当前计时，确定要切换吗？')) return;
  }
  mathStore.resetTimer();
  mathStore.timerMode = mode;
}

// 屏幕常亮切换
function toggleWakeLock() {
  if (mathStore.isScreenWakeLocked) {
    mathStore.releaseScreenWakeLock();
  } else {
    mathStore.requestScreenWakeLock();
  }
}

// 声音模式切换
function cycleSoundMode() {
  if (mathStore.soundMode === 'beep') {
    mathStore.soundMode = 'voice';
  } else if (mathStore.soundMode === 'voice') {
    mathStore.soundMode = 'mute';
  } else {
    mathStore.soundMode = 'beep';
  }
}

const soundModeLabel = computed(() => {
  if (mathStore.soundMode === 'voice') return '语音';
  if (mathStore.soundMode === 'beep') return '提示音';
  return '静音';
});

const soundModeIcon = computed(() => {
  if (mathStore.soundMode === 'voice') return 'fa-solid fa-volume-high text-emerald-600 text-[10px]';
  if (mathStore.soundMode === 'beep') return 'fa-solid fa-bell text-amber-600 text-[10px]';
  return 'fa-solid fa-volume-xmark text-slate-400 text-[10px]';
});

const soundModeTitle = computed(() => {
  if (mathStore.soundMode === 'voice') return '当前：语音提示（开跑、最后1分钟提醒）';
  if (mathStore.soundMode === 'beep') return '当前：倒数提示音';
  return '当前：静音模式';
});

function handleLap() {
  mathStore.recordLap();
}

function handleFinishPractice() {
  mathStore.stopTimer();
}

function handleFullscreenFinishAndGrade() {
  exitFullscreenView();
  mathStore.stopTimer();
  triggerCamera();
}

function triggerCamera() {
  cameraInput.value?.click();
}

function triggerAlbum() {
  albumInput.value?.click();
}

function setQuickTime(str) {
  mathStore.timeStr = str;
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
