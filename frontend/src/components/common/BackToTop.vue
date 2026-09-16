<template>
  <button
    type="button"
    @click="scrollToTop"
    :class="[
      'fixed right-4 bottom-6 z-30 w-11 h-11 rounded-2xl bg-white/90 backdrop-blur-md text-slate-700 hover:text-blue-600 border border-slate-200/80 shadow-lg flex items-center justify-center transition-all duration-300 active:scale-95 cursor-pointer',
      isVisible ? 'opacity-100 translate-y-0 pointer-events-auto' : 'opacity-0 translate-y-4 pointer-events-none'
    ]"
    title="返回顶部"
  >
    <i class="fa-solid fa-arrow-up text-sm"></i>
  </button>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const isVisible = ref(false);

function handleScroll() {
  const top = window.scrollY || document.documentElement.scrollTop || document.body.scrollTop || 0;
  isVisible.value = top > 240;
}

function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true });
  handleScroll();
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});
</script>
