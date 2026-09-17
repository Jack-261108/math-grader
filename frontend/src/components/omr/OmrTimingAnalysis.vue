<template>
  <div v-if="timingData" class="space-y-4">
    <!-- 顶部全真考场做题配速与节奏总览卡片 -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-sm space-y-4">
      <div class="flex items-start justify-between">
        <div>
          <div class="text-[11px] text-blue-600 font-semibold uppercase tracking-wider flex items-center space-x-1.5">
            <i class="fa-solid fa-stopwatch text-blue-600"></i>
            <span>全真模考配速与考后性价比诊断</span>
          </div>
          <h2 class="text-base sm:text-lg font-bold text-slate-900 mt-0.5">做题节奏监控与四象限性价比画像</h2>
          <p class="text-xs text-slate-500 mt-0.5">
            交卷总耗时: <b class="text-slate-800">{{ timingData.total_time_str }}</b> · 全卷平均配速: <b class="text-blue-700">{{ timingData.avg_time_per_q }}秒/题</b> (建议标准: {{ timingData.recommended_avg_time }}秒/题)
          </p>
        </div>

        <div class="text-right shrink-0">
          <span
            :class="[
              'px-2.5 py-1 rounded-xl text-xs font-bold border inline-flex items-center space-x-1 shadow-2xs',
              timingData.pace_status === 'optimal'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : (timingData.pace_status === 'fast'
                  ? 'bg-blue-50 text-blue-700 border-blue-200'
                  : 'bg-rose-50 text-rose-700 border-rose-200')
            ]"
          >
            <span>{{ timingData.pace_status === 'optimal' ? '🎯' : (timingData.pace_status === 'fast' ? '⚡' : '⏳') }}</span>
            <span>{{ timingData.pace_status_label }}</span>
          </span>
        </div>
      </div>

      <!-- 4 列配速关键核心指标 -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-xs">
        <div class="bg-slate-50 rounded-xl p-3 border border-slate-200/70">
          <div class="text-[11px] text-slate-400 font-medium">全卷总耗时</div>
          <div class="text-base font-bold text-slate-800 mt-0.5 font-mono">{{ timingData.total_time_str }}</div>
          <div class="text-[10px] text-slate-400 mt-0.5">折合约 {{ Math.round(timingData.total_elapsed_seconds / 60) }} 分钟</div>
        </div>

        <div class="bg-emerald-50/70 rounded-xl p-3 border border-emerald-200/70">
          <div class="text-[11px] text-emerald-600 font-medium flex items-center space-x-1">
            <i class="fa-solid fa-bolt"></i>
            <span>高效得分区</span>
          </div>
          <div class="text-base font-bold text-emerald-700 mt-0.5">
            {{ timingData.quadrants?.high_efficiency?.count || 0 }} 题
          </div>
          <div class="text-[10px] text-emerald-600 mt-0.5">
            贡献 {{ timingData.quadrants?.high_efficiency?.score_amount || 0 }} 分 ({{ timingData.quadrants?.high_efficiency?.pct_of_total || 0 }}%)
          </div>
        </div>

        <div class="bg-rose-50/70 rounded-xl p-3 border border-rose-200/70 ring-1 ring-rose-200/60">
          <div class="text-[11px] text-rose-600 font-medium flex items-center space-x-1">
            <i class="fa-solid fa-triangle-exclamation"></i>
            <span>高危陷阱雷区</span>
          </div>
          <div class="text-base font-bold text-rose-700 mt-0.5">
            {{ timingData.quadrants?.time_sink?.count || 0 }} 题
          </div>
          <div class="text-[10px] text-rose-600 mt-0.5">
            耗时超标且痛失 {{ timingData.quadrants?.time_sink?.score_amount || 0 }} 分
          </div>
        </div>

        <div class="bg-amber-50/70 rounded-xl p-3 border border-amber-200/70">
          <div class="text-[11px] text-amber-600 font-medium flex items-center space-x-1">
            <i class="fa-solid fa-clock-rotate-left"></i>
            <span>可惜消耗区</span>
          </div>
          <div class="text-base font-bold text-amber-700 mt-0.5">
            {{ timingData.quadrants?.costly_win?.count || 0 }} 题
          </div>
          <div class="text-[10px] text-amber-600 mt-0.5">
            虽得分但耗时过长需提速
          </div>
        </div>
      </div>
    </div>

    <!-- 📊 交互式 SVG 用时-得分 4 象限分布散点图 -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-sm space-y-3.5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1 border-b border-slate-100 pb-2.5">
        <div>
          <h3 class="font-bold text-sm text-slate-800 flex items-center space-x-1.5">
            <i class="fa-solid fa-chart-line text-blue-600"></i>
            <span>行测做题用时与得分 4 象限分布图</span>
          </h3>
          <p class="text-[11px] text-slate-400 mt-0.5">
            点击任意题目圆点直接唤起原题复盘与【💡 问名师】秒杀点拨
          </p>
        </div>

        <!-- 图例 -->
        <div class="flex items-center space-x-3 text-[11px] flex-wrap gap-y-1">
          <span class="flex items-center space-x-1">
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            <span class="text-slate-600">高效区 (快且对)</span>
          </span>
          <span class="flex items-center space-x-1">
            <span class="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
            <span class="text-slate-600">雷区 (慢且错)</span>
          </span>
          <span class="flex items-center space-x-1">
            <span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
            <span class="text-slate-600">可惜区 (慢但对)</span>
          </span>
          <span class="flex items-center space-x-1">
            <span class="w-2.5 h-2.5 rounded-full bg-slate-400"></span>
            <span class="text-slate-600">盲区 (快但错)</span>
          </span>
        </div>
      </div>

      <!-- 散点图 SVG 画布容器 -->
      <div class="relative w-full bg-slate-50/60 rounded-xl border border-slate-200/80 p-2 overflow-x-auto">
        <svg
          :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
          class="w-full h-auto min-w-[580px] select-none font-sans"
        >
          <!-- 4 象限背景色底纹 -->
          <!-- 左上：高效核心区 (耗时短、答对) -->
          <rect
            :x="padLeft"
            :y="padTop"
            :width="splitX - padLeft"
            :height="midY - padTop"
            fill="#10b981"
            fill-opacity="0.08"
            rx="8"
          />
          <!-- 右上：可惜消耗区 (耗时长、答对) -->
          <rect
            :x="splitX"
            :y="padTop"
            :width="plotWidth - splitX"
            :height="midY - padTop"
            fill="#f59e0b"
            fill-opacity="0.08"
            rx="8"
          />
          <!-- 左下：急躁盲区 (耗时短、做错) -->
          <rect
            :x="padLeft"
            :y="midY"
            :width="splitX - padLeft"
            :height="plotHeight - midY"
            fill="#64748b"
            fill-opacity="0.06"
            rx="8"
          />
          <!-- 右下：高危陷阱区 (耗时长、做错) -->
          <rect
            :x="splitX"
            :y="midY"
            :width="plotWidth - splitX"
            :height="plotHeight - midY"
            fill="#f43f5e"
            fill-opacity="0.10"
            rx="8"
          />

          <!-- 象限文字大水印 -->
          <text
            :x="padLeft + 12"
            :y="padTop + 24"
            fill="#059669"
            font-size="12"
            font-weight="bold"
            opacity="0.75"
          >
            🟢 高效核心区 (拿分主力)
          </text>
          <text
            :x="plotWidth - 12"
            :y="padTop + 24"
            text-anchor="end"
            fill="#d97706"
            font-size="12"
            font-weight="bold"
            opacity="0.75"
          >
            🟡 可惜消耗区 (高成本得分)
          </text>
          <text
            :x="padLeft + 12"
            :y="plotHeight - 14"
            fill="#64748b"
            font-size="12"
            font-weight="bold"
            opacity="0.75"
          >
            ⚪ 急躁盲区 (看错/秒蒙)
          </text>
          <text
            :x="plotWidth - 12"
            :y="plotHeight - 14"
            text-anchor="end"
            fill="#e11d48"
            font-size="12"
            font-weight="bold"
            opacity="0.85"
          >
            🔴 高危陷阱区 (实战坚决止损)
          </text>

          <!-- 坐标轴线 -->
          <!-- 中位水平分割线 (区分正误) -->
          <line
            :x1="padLeft"
            :y1="midY"
            :x2="plotWidth"
            :y2="midY"
            stroke="#cbd5e1"
            stroke-width="1.5"
            stroke-dasharray="4,3"
          />

          <!-- 中位垂直分割线 (平均单题用时线) -->
          <line
            :x1="splitX"
            :y1="padTop"
            :x2="splitX"
            :y2="plotHeight"
            stroke="#3b82f6"
            stroke-width="1.5"
            stroke-dasharray="5,4"
          />
          <text
            :x="splitX"
            :y="padTop - 8"
            text-anchor="middle"
            fill="#2563eb"
            font-size="10"
            font-weight="bold"
          >
            基准用时线: {{ timingData.recommended_avg_time }}s
          </text>

          <!-- Y 轴标签 -->
          <text
            :x="padLeft - 8"
            :y="padTop + (midY - padTop) / 2"
            text-anchor="end"
            fill="#059669"
            font-size="11"
            font-weight="bold"
          >
            ✓ 作答正确
          </text>
          <text
            :x="padLeft - 8"
            :y="midY + (plotHeight - midY) / 2"
            text-anchor="end"
            fill="#e11d48"
            font-size="11"
            font-weight="bold"
          >
            ✗ 作答做错
          </text>

          <!-- X 轴刻度线与文字 -->
          <line
            :x1="padLeft"
            :y1="plotHeight"
            :x2="plotWidth"
            :y2="plotHeight"
            stroke="#94a3b8"
            stroke-width="1"
          />
          <g v-for="tick in xTicks" :key="tick.sec">
            <line
              :x1="tick.x"
              :y1="plotHeight"
              :x2="tick.x"
              :y2="plotHeight + 4"
              stroke="#94a3b8"
              stroke-width="1"
            />
            <text
              :x="tick.x"
              :y="plotHeight + 16"
              text-anchor="middle"
              fill="#64748b"
              font-size="10"
            >
              {{ tick.sec }}s
            </text>
          </g>
          <text
            :x="plotWidth"
            :y="plotHeight + 16"
            text-anchor="end"
            fill="#64748b"
            font-size="10"
            font-weight="semibold"
          >
            单题耗时 ➔
          </text>

          <!-- 题目散点圆圈渲染 -->
          <g
            v-for="item in scatterItems"
            :key="item.q_num"
            class="cursor-pointer transition-transform duration-150 hover:scale-125"
            @mouseenter="hoveredItem = item"
            @mouseleave="hoveredItem = null"
            @click="modalStore.openQuestion(item.q_num)"
          >
            <!-- 散点圆点 -->
            <circle
              :cx="item.cx"
              :cy="item.cy"
              :r="item.r"
              :fill="item.fill"
              :stroke="item.stroke"
              stroke-width="1.5"
              class="drop-shadow-2xs"
            />
            <!-- 圆点内题号文字 -->
            <text
              :x="item.cx"
              :y="item.cy + 3.5"
              text-anchor="middle"
              :fill="item.textColor"
              font-size="9"
              font-weight="bold"
              class="pointer-events-none"
            >
              {{ item.q_num }}
            </text>
          </g>
        </svg>

        <!-- 悬停 Hover Tooltip 浮窗 -->
        <div
          v-if="hoveredItem"
          class="absolute z-20 bg-slate-900/90 backdrop-blur-md text-white px-3 py-2 rounded-xl text-xs shadow-xl border border-slate-700 pointer-events-none transition-all"
          :style="{
            left: `${Math.min(75, Math.max(10, (hoveredItem.cx / svgWidth) * 100))}%`,
            top: hoveredItem.cy > midY ? '15%' : '55%'
          }"
        >
          <div class="font-bold flex items-center space-x-1.5">
            <span class="px-1.5 py-0.2 rounded bg-blue-600 text-white font-mono text-[10px]">第 {{ hoveredItem.q_num }} 题</span>
            <span>{{ hoveredItem.sec_name }}</span>
            <span :class="hoveredItem.is_correct ? 'text-emerald-400' : 'text-rose-400'">
              {{ hoveredItem.is_correct ? '✓ 答对' : '✗ 做错' }}
            </span>
          </div>
          <div class="text-[11px] text-slate-300 mt-1 space-y-0.5">
            <div>作答用时: <b class="text-white">{{ hoveredItem.time_spent }} 秒</b> (建议: {{ hoveredItem.split_threshold }}s)</div>
            <div>
              归属象限:
              <b :class="getQuadrantTextColor(hoveredItem.quadrant)">{{ getQuadrantName(hoveredItem.quadrant) }}</b>
            </div>
            <div class="text-[10px] text-blue-300 pt-0.5">👉 点击查看原题、官方解析与名师点拨</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 🎯 四象限错题诊断卡片与靶向刷题清单 -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-sm space-y-3.5">
      <div class="flex items-center justify-between border-b border-slate-100 pb-2.5">
        <h3 class="font-bold text-sm text-slate-800 flex items-center space-x-1.5">
          <i class="fa-solid fa-bullseye text-blue-600"></i>
          <span>四象限靶向深度归因与实战策略</span>
        </h3>
        <span class="text-[11px] text-slate-400">点击卡片筛选查看对应题目</span>
      </div>

      <!-- 四象限选择筛选卡片 -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        <!-- 1. 高效区 -->
        <div
          :class="[
            'p-3.5 rounded-xl border transition cursor-pointer',
            activeQuadrantFilter === 'high_efficiency'
              ? 'bg-emerald-50 border-emerald-500 ring-2 ring-emerald-400/50 shadow-xs'
              : 'bg-emerald-50/40 border-emerald-200/70 hover:bg-emerald-50/80'
          ]"
          @click="activeQuadrantFilter = (activeQuadrantFilter === 'high_efficiency' ? 'all' : 'high_efficiency')"
        >
          <div class="flex items-center justify-between">
            <div class="font-bold text-xs text-emerald-900 flex items-center space-x-1.5">
              <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>🟢 高效核心区</span>
            </div>
            <span class="text-xs font-bold text-emerald-700">
              {{ timingData.quadrants?.high_efficiency?.count || 0 }} 题 ({{ timingData.quadrants?.high_efficiency?.pct_of_total || 0 }}%)
            </span>
          </div>
          <p class="text-[11px] text-emerald-800/90 mt-1 leading-relaxed">
            {{ timingData.quadrants?.high_efficiency?.advice }}
          </p>
        </div>

        <!-- 2. 高危雷区 -->
        <div
          :class="[
            'p-3.5 rounded-xl border transition cursor-pointer',
            activeQuadrantFilter === 'time_sink'
              ? 'bg-rose-50 border-rose-500 ring-2 ring-rose-400/50 shadow-xs'
              : 'bg-rose-50/40 border-rose-200/70 hover:bg-rose-50/80'
          ]"
          @click="activeQuadrantFilter = (activeQuadrantFilter === 'time_sink' ? 'all' : 'time_sink')"
        >
          <div class="flex items-center justify-between">
            <div class="font-bold text-xs text-rose-900 flex items-center space-x-1.5">
              <span class="w-2 h-2 rounded-full bg-rose-500"></span>
              <span>🔴 高危陷阱区 (雷区)</span>
            </div>
            <span class="text-xs font-bold text-rose-700">
              {{ timingData.quadrants?.time_sink?.count || 0 }} 题 ({{ timingData.quadrants?.time_sink?.pct_of_total || 0 }}%)
            </span>
          </div>
          <p class="text-[11px] text-rose-800/90 mt-1 leading-relaxed">
            {{ timingData.quadrants?.time_sink?.advice }}
          </p>
        </div>

        <!-- 3. 可惜区 -->
        <div
          :class="[
            'p-3.5 rounded-xl border transition cursor-pointer',
            activeQuadrantFilter === 'costly_win'
              ? 'bg-amber-50 border-amber-500 ring-2 ring-amber-400/50 shadow-xs'
              : 'bg-amber-50/40 border-amber-200/70 hover:bg-amber-50/80'
          ]"
          @click="activeQuadrantFilter = (activeQuadrantFilter === 'costly_win' ? 'all' : 'costly_win')"
        >
          <div class="flex items-center justify-between">
            <div class="font-bold text-xs text-amber-900 flex items-center space-x-1.5">
              <span class="w-2 h-2 rounded-full bg-amber-500"></span>
              <span>🟡 可惜消耗区 (高成本得分)</span>
            </div>
            <span class="text-xs font-bold text-amber-700">
              {{ timingData.quadrants?.costly_win?.count || 0 }} 题 ({{ timingData.quadrants?.costly_win?.pct_of_total || 0 }}%)
            </span>
          </div>
          <p class="text-[11px] text-amber-800/90 mt-1 leading-relaxed">
            {{ timingData.quadrants?.costly_win?.advice }}
          </p>
        </div>

        <!-- 4. 盲区 -->
        <div
          :class="[
            'p-3.5 rounded-xl border transition cursor-pointer',
            activeQuadrantFilter === 'fast_loss'
              ? 'bg-slate-100 border-slate-500 ring-2 ring-slate-400/50 shadow-xs'
              : 'bg-slate-50 border-slate-200/70 hover:bg-slate-100/80'
          ]"
          @click="activeQuadrantFilter = (activeQuadrantFilter === 'fast_loss' ? 'all' : 'fast_loss')"
        >
          <div class="flex items-center justify-between">
            <div class="font-bold text-xs text-slate-800 flex items-center space-x-1.5">
              <span class="w-2 h-2 rounded-full bg-slate-500"></span>
              <span>⚪ 急躁盲区 (快速失分)</span>
            </div>
            <span class="text-xs font-bold text-slate-700">
              {{ timingData.quadrants?.fast_loss?.count || 0 }} 题 ({{ timingData.quadrants?.fast_loss?.pct_of_total || 0 }}%)
            </span>
          </div>
          <p class="text-[11px] text-slate-600 mt-1 leading-relaxed">
            {{ timingData.quadrants?.fast_loss?.advice }}
          </p>
        </div>
      </div>

      <!-- 选中的象限题目列表 -->
      <div v-if="filteredItems.length > 0" class="space-y-2 pt-1">
        <div class="flex items-center justify-between text-xs text-slate-500 pb-1">
          <span>当前筛选题目 ({{ filteredItems.length }} 题):</span>
          <button
            v-if="activeQuadrantFilter !== 'all'"
            type="button"
            @click="activeQuadrantFilter = 'all'"
            class="text-blue-600 hover:text-blue-800 font-semibold"
          >
            显示全卷全部题目
          </button>
        </div>

        <div class="max-h-64 overflow-y-auto space-y-1.5 pr-1">
          <div
            v-for="it in filteredItems"
            :key="it.q_num"
            class="flex items-center justify-between p-2 rounded-xl bg-slate-50 border border-slate-200/80 text-xs hover:bg-slate-100/80 transition"
          >
            <div class="flex items-center space-x-2 min-w-0">
              <button
                type="button"
                @click="modalStore.openQuestion(it.q_num)"
                class="px-2 py-0.5 rounded-lg bg-white border border-slate-300 font-bold text-slate-700 hover:text-blue-600 hover:border-blue-400 transition cursor-pointer"
              >
                第 {{ it.q_num }} 题
              </button>
              <span class="text-slate-600 font-medium truncate">{{ it.sec_name }}</span>
              <span :class="it.is_correct ? 'text-emerald-600 font-bold' : 'text-rose-600 font-bold'">
                {{ it.is_correct ? '✓ 答对' : '✗ 做错' }}
              </span>
            </div>

            <div class="flex items-center space-x-2 shrink-0">
              <span class="font-mono text-[11px] text-slate-500 font-medium bg-white px-2 py-0.5 rounded-lg border border-slate-200">
                用时: {{ it.time_spent }}s
              </span>
              <button
                type="button"
                @click="modalStore.openQuestion(it.q_num)"
                class="text-[11px] text-blue-600 hover:text-blue-800 font-semibold px-2 py-0.5 rounded-lg hover:bg-blue-50 transition"
              >
                原题
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 🏆 各模块抢分性价比 ROI 排行榜 (分/分钟) -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-sm space-y-3.5">
      <div class="flex items-center justify-between border-b border-slate-100 pb-2.5">
        <div>
          <h3 class="font-bold text-sm text-slate-800 flex items-center space-x-1.5">
            <i class="fa-solid fa-trophy text-amber-500"></i>
            <span>行测各模块抢分性价比 ROI 排行榜</span>
          </h3>
          <p class="text-[11px] text-slate-400 mt-0.5">单位时间得分产出效率 (分/分钟)，指引考场答题先后顺序</p>
        </div>
      </div>

      <div class="space-y-2.5">
        <div
          v-for="s in timingData.section_pace"
          :key="s.sec_id"
          class="p-3 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5 text-xs hover:border-blue-300 transition"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span
                :class="[
                  'w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px] text-white',
                  s.roi_rank === 1 ? 'bg-amber-500' : (s.roi_rank === 2 ? 'bg-slate-400' : (s.roi_rank === 3 ? 'bg-amber-700' : 'bg-slate-300 text-slate-700'))
                ]"
              >
                {{ s.roi_rank }}
              </span>
              <span class="font-bold text-slate-800">{{ s.name }}</span>
              <span class="text-[10px] text-slate-400 font-normal">({{ s.total_q }}题 · 实得 {{ s.earned_score }}分)</span>
            </div>

            <div class="flex items-center space-x-2">
              <span class="font-mono font-black text-blue-700 text-xs">
                {{ s.score_rate_per_min }} <span class="font-normal text-[10px] text-slate-400">分/min</span>
              </span>
              <span
                :class="[
                  'px-1.5 py-0.2 rounded font-bold text-[10px] border',
                  s.pace_status === 'good'
                    ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
                    : (s.pace_status === 'warning'
                      ? 'text-amber-700 bg-amber-50 border-amber-200'
                      : 'text-rose-700 bg-rose-50 border-rose-200')
                ]"
              >
                {{ s.pace_label }}
              </span>
            </div>
          </div>

          <!-- 用时进度与条形展示 -->
          <div class="flex items-center space-x-2 text-[10px] text-slate-500">
            <span>实耗: <b>{{ s.actual_time_str }}</b></span>
            <span class="text-slate-300">/</span>
            <span>建议: {{ s.recommended_time_str }}</span>
            <span class="text-slate-300">·</span>
            <span>平均 {{ s.avg_time_per_q }}秒/题</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 💡 名师考场控时突破洞察清单 -->
    <div v-if="timingData.key_insights && timingData.key_insights.length > 0" class="bg-gradient-to-br from-amber-50/80 via-white to-blue-50/50 rounded-2xl p-4 border border-amber-200/80 shadow-sm space-y-2.5 text-xs">
      <div class="flex items-center space-x-2 border-b border-amber-200/60 pb-2">
        <div class="w-6 h-6 rounded-lg bg-amber-500 text-white flex items-center justify-center text-xs">
          <i class="fa-solid fa-lightbulb"></i>
        </div>
        <h3 class="font-bold text-amber-950 text-sm">考场控速实战锦囊</h3>
      </div>

      <ul class="space-y-1.5 text-[11px] text-amber-900 list-disc list-inside">
        <li v-for="(ins, idx) in timingData.key_insights" :key="idx" class="leading-relaxed">
          {{ ins }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useOmrStore } from '../../stores/omr';
import { useModalStore } from '../../stores/modal';

const omrStore = useOmrStore();
const modalStore = useModalStore();

const timingData = computed(() => omrStore.resultData?.timing_analysis || null);
const activeQuadrantFilter = ref('all'); // 'all' | 'high_efficiency' | 'time_sink' | 'costly_win' | 'fast_loss'
const hoveredItem = ref(null);

// SVG 散点图几何尺寸
const svgWidth = 680;
const svgHeight = 360;
const padLeft = 90;
const padRight = 30;
const padTop = 35;
const padBottom = 35;

const plotWidth = svgWidth - padRight;
const plotHeight = svgHeight - padBottom;
const midY = padTop + (plotHeight - padTop) / 2;

// 计算 X 轴最大秒数与比例尺
const maxTimeSec = computed(() => {
  const items = timingData.value?.timing_items || [];
  let m = 0;
  items.forEach(it => {
    if (it.time_spent > m) m = it.time_spent;
  });
  return Math.max(90, Math.ceil(m / 30) * 30);
});

// 基准分割线 X 位置
const splitX = computed(() => {
  const rec = timingData.value?.recommended_avg_time || 50;
  const ratio = rec / maxTimeSec.value;
  return padLeft + (plotWidth - padLeft) * Math.min(0.85, Math.max(0.15, ratio));
});

// X 轴刻度
const xTicks = computed(() => {
  const max = maxTimeSec.value;
  const step = max <= 120 ? 30 : 60;
  const ticks = [];
  for (let s = step; s <= max; s += step) {
    const x = padLeft + ((s / max) * (plotWidth - padLeft));
    ticks.push({ sec: s, x });
  }
  return ticks;
});

// 转换散点数据
const scatterItems = computed(() => {
  const items = timingData.value?.timing_items || [];
  const maxT = maxTimeSec.value;
  const widthSpan = plotWidth - padLeft;

  return items.map((it, idx) => {
    // X: 基于 time_spent 比例映射
    const ratioX = Math.min(1.0, Math.max(0.02, it.time_spent / maxT));
    const cx = padLeft + (ratioX * widthSpan);

    // Y: 上半部为答对，下半部为做错；加入轻微错开微扰避免圆点完全重叠
    const jitter = ((idx % 7) - 3) * 3.5;
    let cy;
    if (it.is_correct) {
      cy = padTop + 25 + ((midY - padTop - 50) * (0.3 + 0.4 * ((idx % 5) / 5))) + jitter;
    } else {
      cy = midY + 25 + ((plotHeight - midY - 50) * (0.3 + 0.4 * ((idx % 5) / 5))) + jitter;
    }

    // 颜色配置
    let fill = '#10b981';
    let stroke = '#059669';
    let textColor = '#ffffff';

    if (it.quadrant === 'high_efficiency') {
      fill = '#10b981';
      stroke = '#047857';
    } else if (it.quadrant === 'time_sink') {
      fill = '#f43f5e';
      stroke = '#be123c';
    } else if (it.quadrant === 'costly_win') {
      fill = '#f59e0b';
      stroke = '#b45309';
    } else {
      fill = '#94a3b8';
      stroke = '#475569';
    }

    return {
      ...it,
      cx: Math.round(cx),
      cy: Math.round(cy),
      r: 9,
      fill,
      stroke,
      textColor
    };
  });
});

const filteredItems = computed(() => {
  const items = timingData.value?.timing_items || [];
  if (activeQuadrantFilter.value === 'all') return items;
  return items.filter(it => it.quadrant === activeQuadrantFilter.value);
});

function getQuadrantTextColor(qKey) {
  if (qKey === 'high_efficiency') return 'text-emerald-400';
  if (qKey === 'time_sink') return 'text-rose-400';
  if (qKey === 'costly_win') return 'text-amber-400';
  return 'text-slate-300';
}

function getQuadrantName(qKey) {
  if (qKey === 'high_efficiency') return '🟢 高效核心区';
  if (qKey === 'time_sink') return '🔴 高危陷阱区';
  if (qKey === 'costly_win') return '🟡 可惜消耗区';
  return '⚪ 急躁盲区';
}
</script>
