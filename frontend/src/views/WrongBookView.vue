<template>
  <div class="space-y-4 pb-12">
    <!-- 顶部宏观统计看板卡片 -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200/90 shadow-2xs space-y-3.5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-center space-x-2.5">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 text-white flex items-center justify-center font-bold text-base shadow-xs">
            <i class="fa-solid fa-book-bookmark"></i>
          </div>
          <div>
            <div class="flex items-center space-x-2">
              <h2 class="font-extrabold text-slate-800 text-base sm:text-lg">错题知识库 & 艾宾浩斯复习流</h2>
              <span class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-purple-50 text-purple-700 border border-purple-200">
                科学抗遗忘
              </span>
            </div>
            <p class="text-xs text-slate-400 mt-0.5">
              自动沉淀历次速算与行测错题 · 艾宾浩斯遗忘曲线精准调度 · 专项弱项一键组卷重刷
            </p>
          </div>
        </div>

        <div class="flex items-center space-x-2 shrink-0">
          <button
            type="button"
            @click="store.syncHistory"
            :disabled="store.isSyncing"
            class="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 active:scale-95 text-slate-700 font-semibold text-xs transition flex items-center space-x-1.5 cursor-pointer disabled:opacity-60"
            title="从以往的历史批改报告中一键扫描导入错题"
          >
            <i :class="store.isSyncing ? 'fa-solid fa-spinner fa-spin text-purple-600' : 'fa-solid fa-arrows-rotate text-purple-600'"></i>
            <span>{{ store.isSyncing ? '正在同步历史错题...' : '同步历史批改错题' }}</span>
          </button>
        </div>
      </div>

      <!-- 4 列数据指标胶囊 -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-center text-xs">
        <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200/70">
          <div class="text-[11px] text-slate-400 font-medium">累计收录错题</div>
          <div class="text-xl font-extrabold text-slate-800 font-mono mt-0.5">{{ store.stats.total_count }}</div>
          <div class="text-[10px] text-slate-400 mt-0.5">真题与练习册错题库</div>
        </div>

        <div class="bg-rose-50/80 p-2.5 rounded-xl border border-rose-200/80 ring-1 ring-rose-300/40">
          <div class="text-[11px] text-rose-600 font-bold flex items-center justify-center space-x-1">
            <i class="fa-solid fa-clock-rotate-left text-xs"></i>
            <span>今日待复习 (艾宾浩斯)</span>
          </div>
          <div class="text-xl font-black text-rose-600 font-mono mt-0.5">{{ store.stats.today_due_count }}</div>
          <div class="text-[10px] text-rose-500 mt-0.5">到达记忆临界点需巩固</div>
        </div>

        <div class="bg-amber-50/80 p-2.5 rounded-xl border border-amber-200/80">
          <div class="text-[11px] text-amber-700 font-medium flex items-center justify-center space-x-1">
            <i class="fa-solid fa-fire text-xs"></i>
            <span>攻坚学习中</span>
          </div>
          <div class="text-xl font-bold text-amber-700 font-mono mt-0.5">{{ store.stats.learning_count }}</div>
          <div class="text-[10px] text-amber-600 mt-0.5">循环递延复习中</div>
        </div>

        <div class="bg-emerald-50/80 p-2.5 rounded-xl border border-emerald-200/80">
          <div class="text-[11px] text-emerald-700 font-medium flex items-center justify-center space-x-1">
            <i class="fa-solid fa-circle-check text-xs"></i>
            <span>已彻底攻克</span>
          </div>
          <div class="text-xl font-bold text-emerald-700 font-mono mt-0.5">{{ store.stats.mastered_count }}</div>
          <div class="text-[10px] text-emerald-600 mt-0.5">连续答对2次已消灭</div>
        </div>
      </div>
    </div>

    <!-- 三大核心 Tab 切换栏 -->
    <div class="bg-slate-200/80 p-1 rounded-2xl flex text-xs font-bold gap-1 shadow-2xs">
      <button
        type="button"
        @click="switchTab('ebbinghaus')"
        :class="store.activeTab === 'ebbinghaus'
          ? 'flex-1 py-2.5 px-3 rounded-xl bg-white text-purple-700 shadow-xs transition flex items-center justify-center space-x-1.5 cursor-pointer'
          : 'flex-1 py-2.5 px-3 rounded-xl text-slate-600 hover:text-slate-900 transition flex items-center justify-center space-x-1.5 cursor-pointer'"
      >
        <i class="fa-solid fa-brain text-xs"></i>
        <span>艾宾浩斯抗遗忘复习</span>
        <span
          v-if="store.stats.today_due_count > 0"
          class="px-1.5 py-0.2 rounded-full text-[10px] font-black bg-rose-500 text-white"
        >
          {{ store.stats.today_due_count }}
        </span>
      </button>

      <button
        type="button"
        @click="switchTab('all')"
        :class="store.activeTab === 'all'
          ? 'flex-1 py-2.5 px-3 rounded-xl bg-white text-purple-700 shadow-xs transition flex items-center justify-center space-x-1.5 cursor-pointer'
          : 'flex-1 py-2.5 px-3 rounded-xl text-slate-600 hover:text-slate-900 transition flex items-center justify-center space-x-1.5 cursor-pointer'"
      >
        <i class="fa-solid fa-layer-group text-xs"></i>
        <span>考点错题知识库</span>
        <span class="text-[10px] opacity-60 font-normal">({{ store.stats.total_count }})</span>
      </button>

      <button
        type="button"
        @click="switchTab('sheet')"
        :class="store.activeTab === 'sheet'
          ? 'flex-1 py-2.5 px-3 rounded-xl bg-white text-purple-700 shadow-xs transition flex items-center justify-center space-x-1.5 cursor-pointer'
          : 'flex-1 py-2.5 px-3 rounded-xl text-slate-600 hover:text-slate-900 transition flex items-center justify-center space-x-1.5 cursor-pointer'"
      >
        <i class="fa-solid fa-file-pen text-xs"></i>
        <span>15题专项弱项组卷</span>
      </button>
    </div>

    <!-- ============================================================ -->
    <!-- Tab 1: 📋 艾宾浩斯抗遗忘复习流 -->
    <!-- ============================================================ -->
    <div v-if="store.activeTab === 'ebbinghaus'" class="space-y-4">
      <!-- 无待复习题状态卡片 -->
      <div
        v-if="store.dueQuestions.length === 0"
        class="bg-white rounded-2xl p-8 border border-slate-200/90 text-center space-y-3 shadow-2xs"
      >
        <div class="w-14 h-14 mx-auto rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-2xl shadow-xs">
          <i class="fa-solid fa-circle-check"></i>
        </div>
        <h3 class="font-extrabold text-base text-slate-800">今日待复习错题已全部清空！</h3>
        <p class="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
          您已按照艾宾浩斯记忆遗忘曲线完成了今天的抗遗忘任务。已掌握题目已自动递延至下个复习周期。
        </p>
        <div class="pt-2 flex justify-center space-x-3">
          <button
            type="button"
            @click="switchTab('all')"
            class="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition cursor-pointer"
          >
            浏览错题库全部题目
          </button>
          <button
            type="button"
            @click="switchTab('sheet')"
            class="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold transition shadow-xs cursor-pointer"
          >
            组装一份针对性重练卷
          </button>
        </div>
      </div>

      <!-- 待复习列表卡片流 -->
      <div v-else class="space-y-3">
        <div class="flex items-center justify-between text-xs text-slate-500 px-1">
          <span>今日共有 <b class="text-rose-600 font-bold">{{ store.dueQuestions.length }}</b> 道错题到达复习临界点：</span>
          <span class="text-[11px] text-slate-400">做对推进间隔，连续答对2次移入已攻克</span>
        </div>

        <div
          v-for="(q, idx) in store.dueQuestions"
          :key="q.id"
          class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-xs space-y-3.5 transition"
        >
          <!-- 卡片头部标签 -->
          <div class="flex items-center justify-between border-b border-slate-100 pb-2.5">
            <div class="flex items-center space-x-2 min-w-0">
              <span class="w-6 h-6 rounded-lg bg-purple-100 text-purple-800 flex items-center justify-center font-black text-xs shrink-0 font-mono">
                {{ idx + 1 }}
              </span>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold" :class="q.source_type === 'math' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-blue-50 text-blue-700 border border-blue-200'">
                {{ q.source_type === 'math' ? '速算技巧' : '行测考点' }}
              </span>
              <span class="font-bold text-xs sm:text-sm text-slate-900 truncate">
                {{ q.topic_category }}
              </span>
            </div>

            <!-- 艾宾浩斯复习阶梯徽章 -->
            <div class="flex items-center space-x-1.5 shrink-0">
              <span class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-amber-50 text-amber-800 border border-amber-200">
                艾宾浩斯 Stage {{ q.review_stage }}
              </span>
              <span class="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono">
                错 {{ q.wrong_count }} 次 / 连对 {{ q.mastery_streak }} 次
              </span>
            </div>
          </div>

          <!-- 题目内容区 -->
          <div class="space-y-2 text-xs">
            <!-- 资料分析材料 (如有) -->
            <div
              v-if="q.content?.material"
              class="bg-slate-50 border-l-2 border-purple-500 p-2 text-[11px] text-slate-600 leading-relaxed max-h-48 overflow-y-auto"
              v-html="renderStructuredMaterialHtml(q.content.material)"
            ></div>

            <!-- 题干或算式 -->
            <div v-if="q.source_type === 'math'" class="p-3 bg-slate-50 rounded-xl font-mono text-lg font-bold text-slate-900 flex items-center space-x-2">
              <span>{{ q.content?.expression }} = </span>
              <input
                type="text"
                v-model="userReviewInputs[q.id]"
                placeholder="在此心算输入答案"
                class="bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-sm font-bold text-purple-700 w-32 focus:outline-none focus:border-purple-500"
              >
            </div>

            <div v-else class="text-xs sm:text-sm font-bold text-slate-900 leading-relaxed whitespace-pre-wrap">
              {{ q.content?.stem || q.title }}
            </div>

            <!-- 行测选项列表 (如为选择题) -->
            <div v-if="q.content?.options && Object.keys(q.content.options).length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
              <button
                v-for="(optText, optKey) in q.content.options"
                :key="optKey"
                type="button"
                @click="userReviewInputs[q.id] = optKey"
                :class="[
                  'p-2 rounded-xl text-left border text-xs transition cursor-pointer flex items-start space-x-2',
                  userReviewInputs[q.id] === optKey
                    ? 'bg-purple-50 border-purple-500 text-purple-900 font-bold shadow-2xs'
                    : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                ]"
              >
                <b class="w-5 shrink-0">{{ optKey }}.</b>
                <span>{{ optText }}</span>
              </button>
            </div>
          </div>

          <!-- 解析与参考答案抽屉 (点击展开核验) -->
          <div v-if="revealedKeys[q.id]" class="bg-purple-50/60 rounded-xl p-3 border border-purple-200/80 space-y-2 text-xs">
            <div class="flex items-center justify-between border-b border-purple-100 pb-1.5">
              <div class="flex items-center space-x-2">
                <span class="text-slate-500">上次错误选择: <b class="text-rose-600 line-through">{{ q.user_answer || '未填' }}</b></span>
                <span class="text-slate-300">|</span>
                <span class="text-emerald-700 font-bold">标准正解: <b class="text-base font-black text-emerald-600">{{ q.expected_answer }}</b></span>
              </div>
              <span class="text-[10px] text-purple-700 font-medium">{{ q.error_tag ? getErrorTagLabel(q.error_tag) : '' }}</span>
            </div>

            <div v-if="q.content?.advice || q.content?.tip" class="text-[11px] text-slate-700 leading-relaxed">
              <b class="text-purple-700">【名师秒杀解题技巧】:</b> {{ q.content?.advice || q.content?.tip }}
            </div>
            <div v-if="q.content?.diagnosis" class="text-[11px] text-slate-500">
              <b>【错因诊断】:</b> {{ q.content.diagnosis }}
            </div>
          </div>

          <!-- 底部复习评判与核销按钮栏 -->
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              @click="toggleReveal(q.id)"
              class="text-xs text-purple-600 hover:text-purple-800 font-semibold flex items-center space-x-1 cursor-pointer"
            >
              <i :class="revealedKeys[q.id] ? 'fa-solid fa-eye-slash text-xs' : 'fa-solid fa-eye text-xs'"></i>
              <span>{{ revealedKeys[q.id] ? '收起答案解析' : '核对标准答案与名师技巧' }}</span>
            </button>

            <!-- 对/错两键提交艾宾浩斯复习结果 -->
            <div class="flex items-center space-x-2">
              <button
                type="button"
                @click="handleReview(q.id, false)"
                class="flex-1 sm:flex-none px-3.5 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold text-xs transition flex items-center justify-center space-x-1 active:scale-95 cursor-pointer"
                title="本次依然做错，重置回第1阶段，次日重新复习"
              >
                <i class="fa-solid fa-xmark text-xs"></i>
                <span>我又做错了 (重置复习)</span>
              </button>

              <button
                type="button"
                @click="handleReview(q.id, true)"
                class="flex-1 sm:flex-none px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-xs transition flex items-center justify-center space-x-1 active:scale-95 cursor-pointer"
                title="本次做对，推进艾宾浩斯复习周期，连对2次移入已攻克"
              >
                <i class="fa-solid fa-check text-xs"></i>
                <span>我做对了 (推进周期)</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- Tab 2: 📚 考点错题知识库 (全局多维筛选与归因管理) -->
    <!-- ============================================================ -->
    <div v-else-if="store.activeTab === 'all'" class="space-y-3.5">
      <!-- 多维筛选控制台卡片 -->
      <div class="bg-white rounded-2xl p-4 border border-slate-200/90 shadow-2xs space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <!-- 题源筛选 -->
          <div class="flex bg-slate-100 p-0.5 rounded-xl text-xs font-semibold">
            <button
              type="button"
              @click="setFilterSource('all')"
              :class="store.filterSourceType === 'all' ? 'px-2.5 py-1 rounded-lg bg-white shadow-xs text-slate-900 font-bold' : 'px-2.5 py-1 rounded-lg text-slate-500 hover:text-slate-900'"
            >
              全部题源
            </button>
            <button
              type="button"
              @click="setFilterSource('omr')"
              :class="store.filterSourceType === 'omr' ? 'px-2.5 py-1 rounded-lg bg-white shadow-xs text-blue-700 font-bold' : 'px-2.5 py-1 rounded-lg text-slate-500 hover:text-slate-900'"
            >
              行测题目
            </button>
            <button
              type="button"
              @click="setFilterSource('math')"
              :class="store.filterSourceType === 'math' ? 'px-2.5 py-1 rounded-lg bg-white shadow-xs text-emerald-700 font-bold' : 'px-2.5 py-1 rounded-lg text-slate-500 hover:text-slate-900'"
            >
              速算练习
            </button>
          </div>

          <!-- 状态筛选 -->
          <div class="flex items-center space-x-1.5 text-xs">
            <button
              type="button"
              @click="setFilterStatus('all')"
              :class="store.filterStatus === 'all' ? 'px-2 py-0.5 rounded-lg bg-purple-100 text-purple-800 font-bold' : 'px-2 py-0.5 rounded-lg text-slate-500 hover:bg-slate-100'"
            >
              全部状态
            </button>
            <button
              type="button"
              @click="setFilterStatus('reviewing')"
              :class="store.filterStatus === 'reviewing' ? 'px-2 py-0.5 rounded-lg bg-amber-100 text-amber-800 font-bold' : 'px-2 py-0.5 rounded-lg text-slate-500 hover:bg-slate-100'"
            >
              学习中
            </button>
            <button
              type="button"
              @click="setFilterStatus('mastered')"
              :class="store.filterStatus === 'mastered' ? 'px-2 py-0.5 rounded-lg bg-emerald-100 text-emerald-800 font-bold' : 'px-2 py-0.5 rounded-lg text-slate-500 hover:bg-slate-100'"
            >
              已攻克
            </button>
          </div>

          <!-- 错因筛选 -->
          <div class="flex items-center space-x-1 text-xs">
            <span class="text-slate-400 text-[11px]">错因:</span>
            <select
              v-model="store.filterErrorTag"
              @change="store.fetchQuestions"
              class="bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs text-slate-700 focus:outline-none focus:border-purple-500"
            >
              <option value="all">全部错因标签</option>
              <option value="careless">粗心看错/急躁审题</option>
              <option value="confused">概念混淆/定式偏差</option>
              <option value="guessing">时间不足蒙题漏填</option>
              <option value="calculation">计算退位偏差</option>
              <option value="unfamiliar">考点生疏盲区</option>
            </select>
          </div>
        </div>

        <!-- 考点聚类快速过滤胶囊 (TOP 考点) -->
        <div v-if="store.stats.topic_ranking && store.stats.topic_ranking.length > 0" class="flex items-center space-x-1.5 flex-wrap gap-y-1 text-xs pt-1 border-t border-slate-100">
          <span class="text-[11px] text-slate-400">薄弱考点聚类:</span>
          <button
            type="button"
            @click="setFilterTopic('all')"
            :class="store.filterTopic === 'all' ? 'px-2 py-0.5 rounded-md bg-purple-600 text-white font-bold' : 'px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 hover:bg-slate-200'"
          >
            全部
          </button>
          <button
            v-for="top in store.stats.topic_ranking"
            :key="top.topic"
            type="button"
            @click="setFilterTopic(top.topic)"
            :class="store.filterTopic === top.topic ? 'px-2 py-0.5 rounded-md bg-purple-600 text-white font-bold shadow-2xs' : 'px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 hover:bg-slate-200'"
          >
            {{ top.topic }} ({{ top.count }}题)
          </button>
        </div>
      </div>

      <!-- 错题库列表展现 -->
      <div v-if="store.isLoading" class="p-8 text-center text-slate-400 text-xs">
        <i class="fa-solid fa-spinner fa-spin text-base text-purple-600 mr-2"></i>
        <span>正在检索错题知识库...</span>
      </div>

      <div v-else-if="store.questions.length === 0" class="bg-white rounded-2xl p-8 border border-slate-200/90 text-center text-slate-400 text-xs space-y-2">
        <i class="fa-solid fa-box-open text-2xl text-slate-300"></i>
        <div>当前筛选条件下暂无错题记录。</div>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="q in store.questions"
          :key="q.id"
          class="bg-white rounded-2xl p-4 border border-slate-200 shadow-2xs space-y-2.5 text-xs transition hover:border-purple-300"
        >
          <div class="flex items-center justify-between border-b border-slate-100 pb-2">
            <div class="flex items-center space-x-2 truncate">
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold" :class="q.source_type === 'math' ? 'bg-emerald-50 text-emerald-700' : 'bg-blue-50 text-blue-700'">
                {{ q.module_name }}
              </span>
              <span class="font-bold text-slate-800 truncate">{{ q.topic_category }}</span>
              <span class="text-[10px] text-slate-400">错 {{ q.wrong_count }} 次</span>
            </div>

            <!-- 状态与错因标签修改 -->
            <div class="flex items-center space-x-1.5 shrink-0">
              <span
                class="px-2 py-0.5 rounded-full text-[10px] font-bold"
                :class="q.status === 'mastered' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'"
              >
                {{ q.status === 'mastered' ? '已攻克 ✓' : `复习Stage ${q.review_stage}` }}
              </span>

              <!-- 下拉调整错因分类 -->
              <select
                :value="q.error_tag"
                @change="handleTagChange(q.id, $event.target.value)"
                class="bg-slate-50 border border-slate-200 rounded px-1.5 py-0.5 text-[10px] text-slate-600 focus:outline-none"
                title="点击修改错因标签"
              >
                <option value="careless">粗心看错</option>
                <option value="confused">概念混淆</option>
                <option value="guessing">蒙题漏涂</option>
                <option value="calculation">计算失误</option>
                <option value="unfamiliar">考点生疏</option>
              </select>
            </div>
          </div>

          <!-- 题目题干 -->
          <div class="font-medium text-slate-900 leading-relaxed">
            <span v-if="q.source_type === 'math'" class="font-mono font-bold text-base text-purple-900">
              {{ q.content?.expression }} = ?
            </span>
            <span v-else>{{ q.content?.stem || q.title }}</span>
          </div>

          <!-- 正误对比 -->
          <div class="bg-slate-50 rounded-xl p-2.5 flex items-center justify-between text-[11px] text-slate-600">
            <div>
              <span>你的作答: </span>
              <b class="text-rose-600 line-through mr-3">{{ q.user_answer || '未作答' }}</b>
              <span>正确标准答案: </span>
              <b class="text-emerald-700 font-bold">{{ q.expected_answer }}</b>
            </div>
            <span class="text-[10px] text-slate-400">下次复习: {{ q.next_review_at }}</span>
          </div>

          <!-- 用户笔记/复盘口诀备忘 -->
          <div v-if="q.content?.advice || q.content?.tip" class="text-[11px] text-purple-900 bg-purple-50/50 p-2 rounded-lg leading-relaxed">
            <b>【口诀秒杀法】:</b> {{ q.content?.advice || q.content?.tip }}
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- Tab 3: 🎯 针对性弱项重练组卷中心 -->
    <!-- ============================================================ -->
    <div v-else-if="store.activeTab === 'sheet'" class="space-y-4">
      <!-- 组卷配置面板卡片 -->
      <div class="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-2xs space-y-4">
        <div>
          <h3 class="font-extrabold text-base text-slate-800 flex items-center space-x-1.5">
            <i class="fa-solid fa-wand-magic-sparkles text-purple-600"></i>
            <span>针对性薄弱考点自测组卷</span>
          </h3>
          <p class="text-xs text-slate-400 mt-0.5">
            挑选个人做错频次最高、最薄弱的考点，一键生成 15 题专项提分试卷，支持在线自测或导出 A4 空白重做卷
          </p>
        </div>

        <!-- 快捷组卷方案 -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
          <button
            type="button"
            @click="quickGenerate('due')"
            class="p-3 rounded-xl border border-rose-200 bg-rose-50/60 hover:bg-rose-100/80 text-left transition cursor-pointer space-y-1 shadow-2xs"
          >
            <div class="font-bold text-rose-800 flex items-center space-x-1">
              <i class="fa-solid fa-clock-rotate-left"></i>
              <span>艾宾浩斯今日待复习卷</span>
            </div>
            <p class="text-[10px] text-rose-600">集中复习今天到达遗忘临界点的错题</p>
          </button>

          <button
            type="button"
            @click="quickGenerate('recent')"
            class="p-3 rounded-xl border border-purple-200 bg-purple-50/60 hover:bg-purple-100/80 text-left transition cursor-pointer space-y-1 shadow-2xs"
          >
            <div class="font-bold text-purple-800 flex items-center space-x-1">
              <i class="fa-solid fa-calendar-week"></i>
              <span>近 7 天高频错题提分卷</span>
            </div>
            <p class="text-[10px] text-purple-600">抽取近一周反复做错的核心薄弱题型</p>
          </button>

          <button
            type="button"
            @click="quickGenerate('all')"
            class="p-3 rounded-xl border border-blue-200 bg-blue-50/60 hover:bg-blue-100/80 text-left transition cursor-pointer space-y-1 shadow-2xs"
          >
            <div class="font-bold text-blue-800 flex items-center space-x-1">
              <i class="fa-solid fa-shuffle"></i>
              <span>全题库随机抽查 15 题</span>
            </div>
            <p class="text-[10px] text-blue-600">从存量错题中随机抽取题目巩固</p>
          </button>
        </div>

        <!-- 考点多选自选 -->
        <div v-if="store.stats.topic_ranking && store.stats.topic_ranking.length > 0" class="space-y-2 pt-2 border-t border-slate-100 text-xs">
          <div class="flex items-center justify-between">
            <span class="font-bold text-slate-700">或者手动勾选薄弱考点专项组卷:</span>
            <span class="text-[11px] text-slate-400">已选 {{ store.selectedTopicsForSheet.length }} 个考点</span>
          </div>

          <div class="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
            <label
              v-for="top in store.stats.topic_ranking"
              :key="top.topic"
              class="p-2 rounded-xl border flex items-center space-x-2 text-xs transition cursor-pointer"
              :class="store.selectedTopicsForSheet.includes(top.topic) ? 'bg-purple-50 border-purple-500 font-bold text-purple-900' : 'bg-slate-50 border-slate-200 text-slate-700'"
            >
              <input
                type="checkbox"
                :value="top.topic"
                v-model="store.selectedTopicsForSheet"
                class="rounded text-purple-600 focus:ring-purple-500"
              >
              <span class="truncate">{{ top.topic }} ({{ top.count }}题)</span>
            </label>
          </div>

          <div class="flex justify-end pt-2">
            <button
              type="button"
              @click="handleCustomGenerate"
              :disabled="store.isSheetLoading"
              class="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-md transition flex items-center space-x-1.5 cursor-pointer disabled:opacity-60"
            >
              <i class="fa-solid fa-wand-magic-sparkles"></i>
              <span>{{ store.isSheetLoading ? '正在组卷中...' : '生成 15 题专项提分卷' }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 生成的试卷展现区 -->
      <div v-if="store.generatedSheet" class="bg-white rounded-2xl p-5 border border-purple-300 shadow-md space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-purple-100 pb-3">
          <div>
            <div class="text-[10px] text-purple-600 font-bold uppercase tracking-wider">专属针对性自测卷</div>
            <h3 class="font-extrabold text-base sm:text-lg text-slate-900 mt-0.5">
              {{ store.generatedSheet.title }}
            </h3>
            <p class="text-xs text-slate-500">
              共精选 {{ store.generatedSheet.total_items }} 道错题 · 生成日期: {{ store.generatedSheet.created_date }}
            </p>
          </div>

          <!-- 双练习模式大按钮 -->
          <div class="flex items-center space-x-2 shrink-0">
            <button
              type="button"
              @click="startOnlinePractice"
              class="px-4 py-2 bg-purple-600 hover:bg-purple-500 active:scale-95 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center space-x-1.5 cursor-pointer"
            >
              <i class="fa-solid fa-play"></i>
              <span>立即在线作答重刷</span>
            </button>

            <button
              type="button"
              @click="openPrintGeneratedSheet"
              class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center space-x-1.5 cursor-pointer"
            >
              <i class="fa-solid fa-print"></i>
              <span>🖨️ 导出 A4 打印卷</span>
            </button>
          </div>
        </div>

        <!-- 题目列表预览 -->
        <div class="space-y-3">
          <div
            v-for="(it, idx) in store.generatedSheet.items"
            :key="it.db_question_id"
            class="bg-slate-50/70 rounded-xl p-3.5 border border-slate-200 text-xs space-y-2"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-1.5">
                <span class="w-5 h-5 rounded-full bg-purple-600 text-white font-bold flex items-center justify-center text-[10px]">
                  {{ idx + 1 }}
                </span>
                <span class="font-bold text-slate-800">{{ it.topic_category }}</span>
              </div>
              <span class="text-[10px] text-slate-400">正解: {{ it.expected_answer }}</span>
            </div>

            <!-- 题干 -->
            <div class="text-slate-900 font-medium leading-relaxed">
              <span v-if="it.expression" class="font-mono font-bold text-sm">{{ it.expression }} = ?</span>
              <span v-else>{{ it.stem }}</span>
            </div>

            <!-- 选项 -->
            <div v-if="it.options && Object.keys(it.options).length > 0" class="grid grid-cols-2 gap-2 text-[11px] text-slate-700">
              <div v-for="(v, k) in it.options" :key="k">
                <b>{{ k }}.</b> {{ v }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useWrongBookStore } from '../stores/wrongbook';
import { useModalStore } from '../stores/modal';
import { renderStructuredMaterialHtml } from '../utils/materialFormatter';

const store = useWrongBookStore();
const modalStore = useModalStore();

const userReviewInputs = ref({});
const revealedKeys = ref({});

onMounted(async () => {
  await store.fetchStats();
  await store.fetchDueQuestions();
  await store.fetchQuestions();
});

function switchTab(tab) {
  store.activeTab = tab;
  if (tab === 'ebbinghaus') {
    store.fetchDueQuestions();
  } else if (tab === 'all') {
    store.fetchQuestions();
  }
}

function setFilterSource(type) {
  store.filterSourceType = type;
  store.fetchQuestions();
}

function setFilterStatus(st) {
  store.filterStatus = st;
  store.fetchQuestions();
}

function setFilterTopic(tp) {
  store.filterTopic = tp;
  store.fetchQuestions();
}

function toggleReveal(id) {
  revealedKeys.value[id] = !revealedKeys.value[id];
}

async function handleReview(id, isCorrect) {
  const userInput = userReviewInputs.value[id] || '';
  await store.submitReviewResult(id, isCorrect, userInput);
}

async function handleTagChange(id, tag) {
  await store.updateTagAndNotes(id, tag, null);
}

function getErrorTagLabel(tag) {
  const map = {
    careless: '粗心看错',
    confused: '概念混淆',
    guessing: '时间不足蒙题',
    calculation: '计算失误',
    unfamiliar: '考点生疏'
  };
  return map[tag] || '概念混淆';
}

async function quickGenerate(mode) {
  if (mode === 'due') {
    await store.generateCustomSheet({ onlyDue: true, count: 15 });
  } else if (mode === 'recent') {
    await store.generateCustomSheet({ recentDays: 7, count: 15 });
  } else {
    await store.generateCustomSheet({ count: 15 });
  }
}

async function handleCustomGenerate() {
  await store.generateCustomSheet({ count: 15 });
}

function startOnlinePractice() {
  // 切换到艾宾浩斯 Tab 进行刷题
  store.activeTab = 'ebbinghaus';
}

function openPrintGeneratedSheet() {
  // 打开现有 A4 打印模态框
  modalStore.openPrint('wrong_sheet');
}
</script>
