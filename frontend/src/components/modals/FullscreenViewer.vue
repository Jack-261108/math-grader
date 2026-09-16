<template>
  <div
    v-if="modalStore.isFullscreenOpen"
    class="fixed inset-0 z-[100] bg-black/95 backdrop-blur-md flex flex-col justify-between select-none touch-none animate-in fade-in duration-150"
    @keydown.esc="modalStore.closeFullscreen"
  >
    <!-- 顶部操作栏 -->
    <div class="flex items-center justify-between text-white px-4 pt-3 pb-2.5 bg-gradient-to-b from-black/80 to-transparent z-10 safe-top">
      <div class="flex items-center space-x-2">
        <span class="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full bg-white/20 text-white/95 backdrop-blur-sm">
          {{ Math.round(scale * 100) }}%
        </span>
        <span class="text-[11px] text-white/70 hidden sm:inline">双击缩放 · 拖拽平移 · 双指捏合</span>
      </div>
      <div class="flex items-center space-x-2">
        <a
          :href="modalStore.fullscreenImageUrl"
          download="批注原卷大图.jpg"
          class="w-8 h-8 rounded-full bg-white/15 hover:bg-white/25 active:bg-white/35 flex items-center justify-center text-white transition text-xs shadow-xs"
          title="保存/下载原图"
        >
          <i class="fa-solid fa-download"></i>
        </a>
        <button
          type="button"
          @click="modalStore.closeFullscreen"
          class="w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 active:bg-white/40 flex items-center justify-center text-white transition text-sm shadow-xs"
          title="关闭预览 (Esc)"
        >
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>
    </div>

    <!-- 中间视口与图片 -->
    <div
      ref="viewportRef"
      class="flex-1 w-full h-full relative overflow-hidden flex items-center justify-center cursor-grab active:cursor-grabbing touch-none select-none"
      @wheel.prevent="handleWheel"
      @mousedown="handleMouseDown"
      @dblclick="handleDblClick"
      @touchstart="handleTouchStart"
      @touchmove="handleTouchMove"
      @touchend="handleTouchEnd"
      @touchcancel="handleTouchEnd"
      @click="handleViewportClick"
    >
      <img
        ref="imgRef"
        :src="modalStore.fullscreenImageUrl"
        alt="查看大图"
        class="max-w-full max-h-full object-contain pointer-events-auto select-none will-change-transform"
        :style="{
          transform: `translate(${translateX}px, ${translateY}px) scale(${scale}) rotate(${rotation}deg)`,
          transition: withTransition ? 'transform 0.12s cubic-bezier(0.2, 0, 0, 1)' : 'none'
        }"
      >
    </div>

    <!-- 底部缩放与控制栏 -->
    <div class="px-4 pb-4 pt-2 bg-gradient-to-t from-black/80 to-transparent z-10 flex flex-col items-center safe-bottom">
      <div class="flex items-center space-x-1 sm:space-x-2 bg-white/15 backdrop-blur-md px-3 py-1.5 rounded-2xl border border-white/10 shadow-lg text-white text-xs">
        <button type="button" @click="zoomOut" class="w-8 h-8 rounded-xl hover:bg-white/20 active:bg-white/30 flex items-center justify-center transition" title="缩小">
          <i class="fa-solid fa-minus text-xs"></i>
        </button>
        <button type="button" @click="resetTransform" class="px-2.5 h-8 rounded-xl hover:bg-white/20 active:bg-white/30 flex items-center justify-center font-medium text-[11px] transition" title="适应屏幕">
          <span>适应</span>
        </button>
        <button type="button" @click="zoom100" class="px-2.5 h-8 rounded-xl hover:bg-white/20 active:bg-white/30 flex items-center justify-center font-medium text-[11px] transition" title="1:1 原尺寸">
          <span>1:1</span>
        </button>
        <button type="button" @click="zoomIn" class="w-8 h-8 rounded-xl hover:bg-white/20 active:bg-white/30 flex items-center justify-center transition" title="放大">
          <i class="fa-solid fa-plus text-xs"></i>
        </button>
        <div class="w-px h-4 bg-white/20 mx-1"></div>
        <button type="button" @click="rotateRight" class="w-8 h-8 rounded-xl hover:bg-white/20 active:bg-white/30 flex items-center justify-center transition" title="顺时针旋转90°">
          <i class="fa-solid fa-rotate-right text-xs"></i>
        </button>
      </div>
      <p class="text-[10px] text-white/60 mt-1.5 text-center">双击快速缩放 · 单指拖拽平移 · 双指捏合缩放 · 边缘轻触退出</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { useModalStore } from '../../stores/modal';

const modalStore = useModalStore();
const viewportRef = ref(null);
const imgRef = ref(null);

const scale = ref(1);
const translateX = ref(0);
const translateY = ref(0);
const rotation = ref(0);
const withTransition = ref(true);

let isDragging = false;
let startX = 0;
let startY = 0;
let dragMoved = false;
let initialPinchDist = 0;
let initialPinchScale = 1;
let lastTapTime = 0;

function resetTransform() {
  scale.value = 1;
  translateX.value = 0;
  translateY.value = 0;
  rotation.value = 0;
  isDragging = false;
  dragMoved = false;
  withTransition.value = false;
}

watch(() => modalStore.isFullscreenOpen, (open) => {
  if (open) {
    resetTransform();
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
});

function zoomIn() {
  withTransition.value = true;
  scale.value = Math.min(scale.value * 1.35, 6.0);
}

function zoomOut() {
  withTransition.value = true;
  scale.value = Math.max(scale.value / 1.35, 0.4);
  if (scale.value <= 1) {
    translateX.value = 0;
    translateY.value = 0;
  }
}

function zoom100() {
  withTransition.value = true;
  if (imgRef.value?.naturalWidth && imgRef.value?.clientWidth) {
    scale.value = Math.max(0.6, Math.min(5.0, imgRef.value.naturalWidth / imgRef.value.clientWidth));
  } else {
    scale.value = 2.0;
  }
  translateX.value = 0;
  translateY.value = 0;
}

function rotateRight() {
  withTransition.value = true;
  rotation.value = (rotation.value + 90) % 360;
}

function handleWheel(e) {
  withTransition.value = false;
  const factor = e.deltaY > 0 ? 0.88 : 1.15;
  scale.value = Math.max(0.4, Math.min(6.0, scale.value * factor));
  if (scale.value <= 1) {
    translateX.value = 0;
    translateY.value = 0;
  }
}

function handleMouseDown(e) {
  if (e.button !== 0) return;
  isDragging = true;
  dragMoved = false;
  startX = e.clientX - translateX.value;
  startY = e.clientY - translateY.value;
  window.addEventListener('mousemove', handleMouseMove);
  window.addEventListener('mouseup', handleMouseUp);
}

function handleMouseMove(e) {
  if (!isDragging) return;
  const moveX = e.clientX - startX;
  const moveY = e.clientY - startY;
  if (Math.abs(moveX - translateX.value) > 3 || Math.abs(moveY - translateY.value) > 3) {
    dragMoved = true;
  }
  withTransition.value = false;
  translateX.value = moveX;
  translateY.value = moveY;
}

function handleMouseUp() {
  isDragging = false;
  window.removeEventListener('mousemove', handleMouseMove);
  window.removeEventListener('mouseup', handleMouseUp);
}

function handleDblClick(e) {
  if (e.target.closest('button') || e.target.closest('a')) return;
  withTransition.value = true;
  if (scale.value > 1.2) {
    resetTransform();
  } else {
    scale.value = 2.5;
  }
}

function handleTouchStart(e) {
  if (e.touches.length === 1) {
    isDragging = true;
    dragMoved = false;
    startX = e.touches[0].clientX - translateX.value;
    startY = e.touches[0].clientY - translateY.value;

    const now = Date.now();
    if (now - lastTapTime < 300) {
      e.preventDefault();
      withTransition.value = true;
      if (scale.value > 1.2) {
        resetTransform();
      } else {
        scale.value = 2.5;
      }
      lastTapTime = 0;
    } else {
      lastTapTime = now;
    }
  } else if (e.touches.length === 2) {
    isDragging = false;
    dragMoved = true;
    initialPinchDist = Math.hypot(
      e.touches[0].clientX - e.touches[1].clientX,
      e.touches[0].clientY - e.touches[1].clientY
    );
    initialPinchScale = scale.value;
  }
}

function handleTouchMove(e) {
  if (e.touches.length === 1 && isDragging) {
    e.preventDefault();
    const moveX = e.touches[0].clientX - startX;
    const moveY = e.touches[0].clientY - startY;
    if (Math.abs(moveX - translateX.value) > 4 || Math.abs(moveY - translateY.value) > 4) {
      dragMoved = true;
    }
    withTransition.value = false;
    translateX.value = moveX;
    translateY.value = moveY;
  } else if (e.touches.length === 2 && initialPinchDist > 0) {
    e.preventDefault();
    dragMoved = true;
    const curDist = Math.hypot(
      e.touches[0].clientX - e.touches[1].clientX,
      e.touches[0].clientY - e.touches[1].clientY
    );
    const ratio = curDist / initialPinchDist;
    withTransition.value = false;
    scale.value = Math.max(0.4, Math.min(6.0, initialPinchScale * ratio));
  }
}

function handleTouchEnd(e) {
  if (e.touches.length === 0) {
    isDragging = false;
    if (scale.value < 0.85) {
      resetTransform();
    }
  } else if (e.touches.length === 1) {
    startX = e.touches[0].clientX - translateX.value;
    startY = e.touches[0].clientY - translateY.value;
    isDragging = true;
  }
}

function handleViewportClick(e) {
  if (dragMoved) return;
  if (e.target === viewportRef.value && scale.value <= 1.05) {
    modalStore.closeFullscreen();
  }
}

function handleKeydown(e) {
  if (!modalStore.isFullscreenOpen) return;
  if (e.key === 'Escape') modalStore.closeFullscreen();
  else if (e.key === '+' || e.key === '=') zoomIn();
  else if (e.key === '-') zoomOut();
  else if (e.key === 'r' || e.key === 'R') rotateRight();
  else if (e.key === '0') resetTransform();
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown);
});
</script>
