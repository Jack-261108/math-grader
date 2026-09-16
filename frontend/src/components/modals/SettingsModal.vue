<template>
  <div
    v-if="modalStore.isSettingsOpen"
    class="fixed inset-0 z-[60] bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-200"
    @click.self="modalStore.closeSettings"
  >
    <div class="bg-white rounded-2xl max-w-sm w-full p-5 shadow-2xl space-y-4 relative">
      <div class="flex items-center justify-between border-b border-slate-100 pb-3">
        <div class="flex items-center space-x-2">
          <div class="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center">
            <i class="fa-solid fa-sliders text-xs"></i>
          </div>
          <h3 class="font-bold text-slate-800 text-sm">AI 接口配置 (BYOK)</h3>
        </div>
        <button
          type="button"
          @click="modalStore.closeSettings"
          class="w-7 h-7 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 flex items-center justify-center transition"
        >
          <i class="fa-solid fa-xmark text-sm"></i>
        </button>
      </div>

      <div class="space-y-3 text-xs">
        <div class="bg-amber-50/90 border border-amber-200 text-amber-900 rounded-xl p-2.5 flex items-start space-x-2 text-[11px] leading-relaxed">
          <i class="fa-solid fa-triangle-exclamation text-amber-600 mt-0.5 shrink-0"></i>
          <span><b>重要说明</b>：您需要填写个人的 Base URL 和 API Key (BYOK) 才能使用视觉识别与批改功能。数据仅保存在当前手机/浏览器本地 (localStorage)，不上传服务器。</span>
        </div>

        <div>
          <label class="block font-bold text-slate-700 mb-1 flex items-center justify-between">
            <span>API Base URL</span>
            <span class="text-[10px] text-rose-500 font-extrabold">*必填</span>
          </label>
          <input
            type="text"
            v-model="formBaseUrl"
            placeholder="例如: https://api.anthropic.com 或您的转发中转地址"
            class="w-full border border-slate-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition"
          >
          <p class="text-[10px] text-slate-400 mt-1">支持 Anthropic 原生端点或 OneAPI / NewAPI 等兼容中转服务</p>
        </div>

        <div>
          <label class="block font-bold text-slate-700 mb-1 flex items-center justify-between">
            <span>API Key / Token</span>
            <span class="text-[10px] text-rose-500 font-extrabold">*必填</span>
          </label>
          <div class="relative">
            <input
              :type="showKey ? 'text' : 'password'"
              v-model="formApiKey"
              placeholder="sk-ant-api03-... 或您的个人令牌"
              class="w-full border border-slate-200 rounded-xl pl-3 pr-8 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 font-mono transition"
            >
            <button
              type="button"
              @click="showKey = !showKey"
              class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
            >
              <i :class="showKey ? 'fa-regular fa-eye-slash text-xs' : 'fa-regular fa-eye text-xs'"></i>
            </button>
          </div>
          <p class="text-[10px] text-slate-400 mt-1">仅存储在浏览器本地，批改时临时随请求发送</p>
        </div>

        <div>
          <label class="block font-medium text-slate-700 mb-1">视觉识别模型 (可选)</label>
          <input
            type="text"
            v-model="formModel"
            placeholder="留空默认使用高速模型"
            class="w-full border border-slate-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 font-mono transition"
          >
          <div class="flex flex-wrap gap-1 mt-1.5">
            <button
              v-for="m in quickModels"
              :key="m.val"
              type="button"
              @click="formModel = m.val"
              class="px-2 py-0.5 bg-slate-100 hover:bg-emerald-50 hover:text-emerald-700 active:bg-emerald-100 rounded-md text-[10px] text-slate-600 transition"
            >
              {{ m.label }}
            </button>
          </div>
        </div>

        <!-- 连通性测试结果提示条 -->
        <div v-if="testResult" :class="testResult.success ? 'rounded-xl p-2.5 text-[11px] leading-relaxed border bg-emerald-50 text-emerald-900 border-emerald-200 block' : 'rounded-xl p-2.5 text-[11px] leading-relaxed border bg-rose-50 text-rose-900 border-rose-200 block'">
          <div :class="testResult.success ? 'font-bold text-emerald-800 flex items-center mb-0.5' : 'font-bold text-rose-800 flex items-center mb-0.5'">
            <i :class="testResult.success ? 'fa-solid fa-circle-check mr-1.5 text-emerald-600' : 'fa-solid fa-circle-xmark mr-1.5 text-rose-600'"></i>
            <span>{{ testResult.msg }}</span>
          </div>
          <div :class="testResult.success ? 'text-[10px] text-emerald-700 font-mono mt-0.5 break-all' : 'text-[10px] text-rose-600 font-mono mt-0.5 break-all'">
            端点: {{ testResult.url || formBaseUrl }} | 模型: {{ formModel || '默认' }}
          </div>
        </div>
      </div>

      <!-- 操作按钮组 -->
      <div class="pt-2 space-y-2">
        <button
          type="button"
          @click="handleTest"
          :disabled="isTesting"
          class="w-full py-2 px-3 bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-700 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition disabled:opacity-60"
        >
          <i :class="isTesting ? 'fa-solid fa-spinner fa-spin text-xs text-blue-600' : 'fa-solid fa-satellite-dish text-xs text-blue-600'"></i>
          <span>{{ isTesting ? '正在测试 API 连通性...' : '测试 API 连通性' }}</span>
        </button>

        <div class="flex items-center space-x-2">
          <button
            type="button"
            @click="handleReset"
            class="flex-1 py-2 px-3 border border-slate-200 text-slate-600 hover:bg-slate-50 active:bg-slate-100 rounded-xl text-xs font-medium transition"
          >
            清空本地
          </button>
          <button
            type="button"
            @click="handleSave"
            class="flex-1 py-2 px-3 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white rounded-xl text-xs font-bold transition shadow-xs"
          >
            保存配置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useConfigStore } from '../../stores/config';
import { useModalStore } from '../../stores/modal';

const configStore = useConfigStore();
const modalStore = useModalStore();

const formBaseUrl = ref('');
const formApiKey = ref('');
const formModel = ref('');
const showKey = ref(false);
const isTesting = ref(false);
const testResult = ref(null);

const quickModels = [
  { label: 'Sonnet 3.5', val: 'claude-3-5-sonnet-20241022' },
  { label: 'Sonnet 3.7', val: 'claude-3-7-sonnet-20250219' },
  { label: 'Haiku 3.5', val: 'claude-3-5-haiku-20241022' },
  { label: 'Gemini Flash', val: 'gemini-2.5-flash' }
];

watch(() => modalStore.isSettingsOpen, (open) => {
  if (open) {
    formBaseUrl.value = configStore.baseUrl;
    formApiKey.value = configStore.apiKey;
    formModel.value = configStore.model;
    testResult.value = null;
    showKey.value = false;
  }
});

async function handleTest() {
  if (!formBaseUrl.value.trim() || !formApiKey.value.trim()) {
    testResult.value = { success: false, msg: '请先填写 Base URL 和 API Key 再进行测试。' };
    return;
  }

  isTesting.value = true;
  testResult.value = null;

  try {
    const res = await configStore.testConnection(formBaseUrl.value, formApiKey.value, formModel.value);
    if (res.status === 'success') {
      testResult.value = {
        success: true,
        msg: res.message || 'API 连通测试成功！',
        url: res.url
      };
    } else {
      testResult.value = {
        success: false,
        msg: `测试失败: ${res.detail || '无法连通'}`,
        url: res.url
      };
    }
  } catch (err) {
    testResult.value = {
      success: false,
      msg: `网络请求异常: ${err.message}`
    };
  } finally {
    isTesting.value = false;
  }
}

function handleSave() {
  if (!formBaseUrl.value.trim() || !formApiKey.value.trim()) {
    alert('【Base URL】与【API Key】为必填项，请填写完整后再保存。');
    return;
  }
  configStore.saveConfig({
    base_url: formBaseUrl.value,
    api_key: formApiKey.value,
    model: formModel.value
  });
  modalStore.closeSettings();
  alert('✅ 配置保存成功！您填写的 Base URL 与 API Key 仅保存在当前浏览器本地。');
}

function handleReset() {
  if (confirm('确定要清空本地保存的 Base URL 和 API Key 吗？\n\n清空后将无法使用 AI 批改功能，直到您再次配置。')) {
    configStore.clearConfig();
    formBaseUrl.value = '';
    formApiKey.value = '';
    formModel.value = '';
    modalStore.closeSettings();
  }
}
</script>
