<template>
  <section class="space-y-4">
    <!-- 引导横幅 -->
    <div class="bg-gradient-to-br from-emerald-600 to-teal-700 rounded-2xl p-5 text-white shadow-md relative overflow-hidden">
      <div class="relative z-10">
        <h2 class="text-xl font-bold mb-1">对准练习册，一键拍照批改</h2>
        <p class="text-emerald-100 text-xs leading-relaxed mb-4">
          自动校正拍摄倾斜，智能辨识手写笔迹并红绿勾叉标注，自动统计正确率与等级。
        </p>

        <!-- 用时设置 -->
        <div class="bg-black/15 rounded-xl p-2.5 flex items-center justify-between text-xs mb-4">
          <span class="text-emerald-50 flex items-center">
            <i class="fa-regular fa-clock mr-1.5"></i> 完成用时:
          </span>
          <input
            type="text"
            v-model="mathStore.timeStr"
            class="bg-white/20 text-white font-medium text-center rounded px-2 py-1 w-24 border border-white/30 text-xs focus:outline-none focus:ring-1 focus:ring-white"
          >
        </div>

        <!-- 双按钮：拍照与相册选择 -->
        <div class="grid grid-cols-2 gap-2.5">
          <button
            type="button"
            @click="triggerCamera"
            class="flex items-center justify-center space-x-2 bg-white text-emerald-700 hover:bg-emerald-50 active:scale-98 transition font-bold py-3 px-3 rounded-xl shadow text-sm cursor-pointer"
          >
            <i class="fa-solid fa-camera text-base"></i>
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

    <!-- 拍照小贴士卡片 -->
    <div class="bg-white rounded-xl p-4 border border-slate-200/80 shadow-2xs">
      <h3 class="font-bold text-xs text-slate-700 mb-2 flex items-center">
        <i class="fa-solid fa-circle-info text-emerald-600 mr-1.5"></i> 拍摄建议
      </h3>
      <ul class="text-xs text-slate-500 space-y-1.5 pl-1">
        <li class="flex items-start">
          <i class="fa-solid fa-check text-emerald-500 mr-1.5 mt-0.5 text-[10px]"></i>
          尽量让练习题完整表格位于镜头画面居中位置
        </li>
        <li class="flex items-start">
          <i class="fa-solid fa-check text-emerald-500 mr-1.5 mt-0.5 text-[10px]"></i>
          支持纸面略微倾斜与角度畸变，算法将自动正射矫正
        </li>
        <li class="flex items-start">
          <i class="fa-solid fa-check text-emerald-500 mr-1.5 mt-0.5 text-[10px]"></i>
          确保光线均匀，避免大面积深色手影遮挡手写数字
        </li>
      </ul>
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
