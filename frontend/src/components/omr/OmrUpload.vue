<template>
  <section class="space-y-4">
    <!-- 顶部大卡片：双模切换 (拍照识别 vs 在线涂卡) -->
    <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200/90 shadow-sm space-y-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-sm shadow-2xs">
            <i class="fa-solid fa-table-cells-large"></i>
          </div>
          <div>
            <h3 class="font-bold text-slate-800 text-sm">行测实战答题卡批改</h3>
            <p class="text-[11px] text-slate-400">支持手机拍照原卷识别 · 支持大屏极速在线涂卡</p>
          </div>
        </div>
      </div>

      <!-- 子模式切换 Tab -->
      <div class="flex bg-slate-100 p-1 rounded-2xl gap-1">
        <button
          type="button"
          @click="omrStore.activeSubMode = 'scan'"
          :class="omrStore.activeSubMode === 'scan' ? 'flex-1 py-2.5 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5 bg-white text-blue-700 shadow-xs' : 'flex-1 py-2.5 px-3 rounded-xl text-xs font-semibold transition flex items-center justify-center space-x-1.5 text-slate-600 hover:text-slate-900'"
        >
          <i class="fa-solid fa-camera text-xs"></i>
          <span>📸 拍照识别批改</span>
        </button>
        <button
          type="button"
          @click="omrStore.activeSubMode = 'online'"
          :class="omrStore.activeSubMode === 'online' ? 'flex-1 py-2.5 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5 bg-white text-blue-700 shadow-xs' : 'flex-1 py-2.5 px-3 rounded-xl text-xs font-semibold transition flex items-center justify-center space-x-1.5 text-slate-600 hover:text-slate-900'"
        >
          <i class="fa-solid fa-pen-to-square text-xs"></i>
          <span>✏️ 极速在线涂卡纸</span>
        </button>
      </div>

      <!-- 考试预设规则选择 -->
      <div class="space-y-2">
        <div class="flex items-center justify-between text-xs">
          <label class="font-bold text-slate-700 flex items-center space-x-1">
            <i class="fa-solid fa-file-signature text-blue-600"></i>
            <span>选择试卷/模考预设</span>
          </label>
          <button
            type="button"
            @click="omrStore.isSectionDrawerOpen = !omrStore.isSectionDrawerOpen"
            class="text-[11px] text-blue-600 hover:text-blue-700 font-semibold flex items-center space-x-1 transition"
          >
            <span>{{ omrStore.isSectionDrawerOpen ? '收起配置' : '展开自定义分值' }}</span>
            <i :class="omrStore.isSectionDrawerOpen ? 'fa-solid fa-chevron-up text-[10px]' : 'fa-solid fa-chevron-down text-[10px]'"></i>
          </button>
        </div>

        <div class="grid grid-cols-2 gap-2">
          <button
            v-for="(pData, pId) in omrStore.presets"
            :key="pId"
            type="button"
            @click="omrStore.selectPreset(pId)"
            :class="omrStore.currentPresetId === pId ? 'px-2.5 py-2 rounded-xl text-xs font-bold border transition text-left bg-blue-50 border-blue-500 text-blue-700 shadow-2xs' : 'px-2.5 py-2 rounded-xl text-xs font-medium border transition text-left bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'"
          >
            <div class="truncate">{{ pData.name }}</div>
            <div class="text-[10px] text-slate-400 font-normal mt-0.5">{{ pData.total_questions }}题 / {{ pData.full_score }}分</div>
          </button>
        </div>

        <!-- 自定义分值抽屉 -->
        <div v-show="omrStore.isSectionDrawerOpen" class="mt-2 p-3 bg-slate-50/90 rounded-xl border border-slate-200/90 space-y-2.5 text-xs">
          <div class="flex items-center justify-between text-slate-500 text-[11px] pb-1 border-b border-slate-200">
            <span>五大模块分值微调 (实时联动计算)</span>
            <button
              type="button"
              @click="omrStore.selectPreset(omrStore.currentPresetId)"
              class="text-blue-600 hover:text-blue-800 font-semibold"
            >
              恢复默认
            </button>
          </div>

          <div class="space-y-1.5">
            <div
              v-for="(sec, sIdx) in omrStore.currentSections"
              :key="sIdx"
              class="bg-white p-2 rounded-xl border border-slate-200 flex items-center justify-between text-xs w-full min-w-0"
            >
              <div class="font-bold text-slate-800 w-20 sm:w-24 truncate shrink-0">{{ sec.name }}</div>
              <div class="flex items-center space-x-1 shrink-0">
                <span class="text-slate-400 text-[10px]">题:</span>
                <input type="number" v-model.number="sec.start_q" class="w-10 bg-slate-50 border border-slate-300 rounded px-1 text-center text-xs">
                <span class="text-slate-400 text-[10px]">~</span>
                <input type="number" v-model.number="sec.end_q" class="w-10 bg-slate-50 border border-slate-300 rounded px-1 text-center text-xs">
              </div>
              <div class="flex items-center space-x-1 shrink-0">
                <span class="text-slate-400 text-[10px]">分:</span>
                <input type="number" step="0.05" v-model.number="sec.score_per_q" class="w-12 bg-slate-50 border border-slate-300 rounded px-0.5 text-center text-xs font-bold text-blue-700">
              </div>
            </div>
          </div>

          <div class="flex justify-between text-[11px] text-slate-500 font-medium pt-1">
            <span>总题数: <b class="text-slate-800">{{ omrStore.totalQuestions }}</b> 题</span>
            <span>核算满分: <b class="text-blue-700">{{ omrStore.fullScore }}</b> 分</span>
          </div>
        </div>
      </div>

      <!-- 标准参考答案录入 -->
      <div class="space-y-2">
        <div class="flex items-center justify-between text-xs">
          <label class="font-bold text-slate-700 flex items-center space-x-1">
            <i class="fa-solid fa-key text-blue-600"></i>
            <span>试卷标准参考答案</span>
            <span class="text-rose-500 font-extrabold">*必填</span>
          </label>
          <div class="flex items-center space-x-2">
            <button
              type="button"
              @click="triggerAnswerImage"
              :disabled="isParsingAns"
              class="text-[11px] text-blue-600 hover:text-blue-800 font-semibold flex items-center space-x-1 bg-blue-50 hover:bg-blue-100 px-2 py-0.5 rounded-md transition disabled:opacity-60"
            >
              <i :class="isParsingAns ? 'fa-solid fa-spinner fa-spin text-[10px]' : 'fa-solid fa-camera text-[10px]'"></i>
              <span>{{ isParsingAns ? '识别中...' : '答案截图识别' }}</span>
            </button>
            <button
              type="button"
              @click="fillDemoAnswers"
              class="text-[11px] text-slate-500 hover:text-slate-800 transition"
            >
              一键范例
            </button>
            <button
              type="button"
              @click="omrStore.answerKey = ''"
              class="text-[11px] text-slate-400 hover:text-rose-600 transition"
            >
              清空
            </button>
          </div>
        </div>

        <input ref="ansImgInput" type="file" accept="image/*" class="hidden" @change="handleAnswerImgChange">

        <textarea
          v-model="omrStore.answerKey"
          rows="3"
          placeholder="输入标准答案（支持连续字母如 BACDDAC...，或分模块格式: 1-5 BACDD 6-10 ...）"
          class="w-full border border-slate-200 rounded-xl p-2.5 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition leading-relaxed"
        ></textarea>

        <div class="flex items-center justify-between text-[11px] text-slate-400">
          <div class="flex items-center space-x-1.5 flex-wrap gap-y-1">
            <span>已录入标准答案: <b class="text-blue-600">{{ parsedAnswerCount }}</b> 题</span>
            <span v-if="parsedMaxQ > 0 && isSheetSyncedWithAnswers" class="text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded text-[10px] font-semibold flex items-center space-x-1">
              <i class="fa-solid fa-circle-check text-[9px]"></i>
              <span>答题卡已自适应 ({{ omrStore.totalQuestions }}题)</span>
            </span>
            <button
              v-else-if="parsedMaxQ > 0 && !isSheetSyncedWithAnswers"
              type="button"
              @click="handleSyncToAnswerCount"
              class="text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 px-2 py-0.5 rounded text-[10px] font-bold flex items-center space-x-1 transition cursor-pointer"
              title="点击将下方答题卡同步为答案题数"
            >
              <i class="fa-solid fa-arrows-rotate text-[9px]"></i>
              <span>答题卡当前{{ omrStore.totalQuestions }}题 · 点击同步为{{ parsedMaxQ }}题</span>
            </button>
          </div>
          <span class="shrink-0">用时: <input type="text" v-model="omrStore.timeStr" class="border border-slate-200 rounded px-1.5 py-0.5 w-20 text-center text-xs font-mono text-slate-700"></span>
        </div>
      </div>
    </div>

    <!-- 拍照批改交互横幅 (当 activeSubMode === 'scan') -->
    <div v-if="omrStore.activeSubMode === 'scan'" class="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl p-5 text-white shadow-md relative overflow-hidden space-y-4">
      <div class="relative z-10 space-y-3">
        <div>
          <h2 class="text-xl font-bold mb-1">对准行测答题卡，一键拍照批改</h2>
          <p class="text-blue-100 text-xs leading-relaxed">
            自动匹配填涂卡ABCD点位，分模块核算分值与正确率，生成原卷红绿批注与学情诊断报告。
          </p>
        </div>

        <div class="grid grid-cols-2 gap-2.5">
          <button
            type="button"
            @click="triggerOmrCamera"
            class="flex items-center justify-center space-x-2 bg-white text-blue-700 hover:bg-blue-50 active:scale-98 transition font-bold py-3 px-3 rounded-xl shadow text-sm cursor-pointer"
          >
            <i class="fa-solid fa-camera text-base"></i>
            <span>拍照批改</span>
          </button>
          <button
            type="button"
            @click="triggerOmrAlbum"
            class="flex items-center justify-center space-x-2 bg-blue-800/40 hover:bg-blue-800/60 active:scale-98 transition font-medium text-white border border-white/20 py-3 px-3 rounded-xl text-sm cursor-pointer"
          >
            <i class="fa-solid fa-image text-base"></i>
            <span>相册选取</span>
          </button>
        </div>

        <!-- 仅拍照识别选项 (先核验后批改) -->
        <div class="pt-1">
          <button
            type="button"
            @click="triggerRecognizeOnly"
            class="w-full py-2 px-3 bg-blue-500/30 hover:bg-blue-500/50 active:bg-blue-500/60 text-white rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition border border-white/20 cursor-pointer"
          >
            <i class="fa-solid fa-eye text-xs"></i>
            <span>仅拍照识别填涂 (先核对后批改)</span>
          </button>
        </div>
      </div>

      <input ref="omrCameraInput" type="file" accept="image/*" capture="environment" class="hidden" @change="handleOmrFileChange">
      <input ref="omrAlbumInput" type="file" accept="image/*" class="hidden" @change="handleOmrFileChange">
      <input ref="recognizeInput" type="file" accept="image/*" class="hidden" @change="handleRecognizeChange">

      <i class="fa-solid fa-table-cells absolute right-1 bottom-1 text-8xl text-white/10 pointer-events-none"></i>
    </div>

    <!-- 在线涂卡纸交互入口 (当 activeSubMode === 'online') -->
    <OmrOnlineSheet v-else />
  </section>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useOmrStore } from '../../stores/omr';
import { useConfigStore } from '../../stores/config';
import { parseAnswerImage } from '../../api/omr';
import { compressImage } from '../../utils/imageCompressor';
import { parseAnswerKeyText } from '../../utils/answerParser';
import { useRouter } from 'vue-router';
import OmrOnlineSheet from './OmrOnlineSheet.vue';

const omrStore = useOmrStore();
const configStore = useConfigStore();
const router = useRouter();

const ansImgInput = ref(null);
const isParsingAns = ref(false);

const omrCameraInput = ref(null);
const omrAlbumInput = ref(null);
const recognizeInput = ref(null);

const parsedAnswerInfo = computed(() => {
  return parseAnswerKeyText(omrStore.answerKey || '');
});

const parsedAnswerCount = computed(() => parsedAnswerInfo.value.count);
const parsedMaxQ = computed(() => parsedAnswerInfo.value.maxQ);

const isSheetSyncedWithAnswers = computed(() => {
  if (parsedMaxQ.value <= 0) return true;
  return omrStore.totalQuestions === parsedMaxQ.value;
});

// 监听答案输入防抖自适应答题卡题数
let debounceTimer = null;
watch(() => omrStore.answerKey, (newVal) => {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    const info = parseAnswerKeyText(newVal || '');
    if (info.maxQ > 0) {
      // 当解析出有效题数且与当前答题卡题数不一致时，自动自适应答题卡
      if (omrStore.totalQuestions !== info.maxQ) {
        omrStore.adaptSectionsToAnswerCount(info.maxQ);
      }
    }
  }, 300);
});

function handleSyncToAnswerCount() {
  if (parsedMaxQ.value > 0) {
    omrStore.adaptSectionsToAnswerCount(parsedMaxQ.value);
  }
}

function triggerAnswerImage() {
  ansImgInput.value?.click();
}

async function handleAnswerImgChange(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  isParsingAns.value = true;
  try {
    const uploadFile = await compressImage(file, 2000, 0.85);
    const fd = new FormData();
    fd.append('file', uploadFile);
    configStore.appendApiCredentials(fd);
    const res = await parseAnswerImage(fd);
    if (res.formatted_text) {
      omrStore.answerKey = res.formatted_text;
      const info = parseAnswerKeyText(res.formatted_text);
      if (info.maxQ > 0) {
        omrStore.adaptSectionsToAnswerCount(info.maxQ);
      } else if (res.suggested_preset) {
        omrStore.selectPreset(res.suggested_preset);
      }
      alert(`🎉 成功识别提取 ${res.total_detected} 道题标准答案！已自动自适应答题卡为 ${info.maxQ || res.total_detected} 题。`);
    } else {
      alert('未能从图片中解析出有效题号和答案，请确认图片清晰度。');
    }
  } catch (err) {
    alert('答案截图识别失败: ' + err.message);
  } finally {
    isParsingAns.value = false;
    e.target.value = '';
  }
}

function fillDemoAnswers() {
  const total = omrStore.totalQuestions;
  const sample = "BACDDACBDDCBABDDCBAACBDD";
  let res = "";
  while (res.length < total) {
    res += sample;
  }
  omrStore.answerKey = res.substring(0, total);
}

function triggerOmrCamera() {
  omrCameraInput.value?.click();
}

function triggerOmrAlbum() {
  omrAlbumInput.value?.click();
}

function triggerRecognizeOnly() {
  recognizeInput.value?.click();
}

async function handleOmrFileChange(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  try {
    const data = await omrStore.submitGradeFromUpload(file);
    if (data?.task_id) {
      router.replace({ path: '/', query: { mode: 'omr', task_id: data.task_id } });
    }
  } catch (err) {
    alert(err.message || '答题卡批改失败');
  } finally {
    e.target.value = '';
  }
}

async function handleRecognizeChange(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  try {
    const res = await omrStore.recognizeOnly(file);
    alert(`🎉 成功识别 ${res.total_detected || Object.keys(omrStore.onlineAnswers).length} 道题目的考生填涂！\n已自动填入极速涂卡纸，核对后点击底部【提交在线答卷】即可出分！`);
  } catch (err) {
    alert('识别失败: ' + err.message);
  } finally {
    e.target.value = '';
  }
}
</script>
