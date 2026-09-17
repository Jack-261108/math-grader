/**
 * 高可用屏幕常亮控制器 (High-Availability Screen Wake Lock Manager)
 * 1. 优先使用 W3C Screen Wake Lock API (navigator.wakeLock)
 * 2. 自动监听 visibilitychange / focus / fullscreenchange，前台切回时自动无缝续期
 * 3. 针对受限环境与移动端 WebView 具备隐藏静音微视频播放兜底 (NoSleep Fallback)
 */

class ScreenWakeLockController {
  constructor() {
    this.isActive = false;
    this.sentinel = null;
    this.fallbackVideo = null;
    this.listenersBound = false;
    this.onStatusChangeCallbacks = new Set();
  }

  onStatusChange(cb) {
    if (typeof cb === 'function') {
      this.onStatusChangeCallbacks.add(cb);
    }
    return () => this.onStatusChangeCallbacks.delete(cb);
  }

  notifyStatus(active) {
    this.onStatusChangeCallbacks.forEach(cb => {
      try { cb(active); } catch (e) {}
    });
  }

  bindLifecycleListeners() {
    if (this.listenersBound || typeof document === 'undefined') return;
    this.listenersBound = true;

    // 当页面从后台切回前台时，原生 WakeLock 会被系统自动释放，必须立即重新激活
    const handleReactivate = async () => {
      if (this.isActive && typeof document !== 'undefined' && document.visibilityState === 'visible') {
        await this.requestNativeWakeLock();
      }
    };

    document.addEventListener('visibilitychange', handleReactivate);
    window.addEventListener('focus', handleReactivate);
    document.addEventListener('fullscreenchange', handleReactivate);
    document.addEventListener('webkitfullscreenchange', handleReactivate);
  }

  async requestNativeWakeLock() {
    if (typeof navigator === 'undefined' || !('wakeLock' in navigator)) {
      return false;
    }
    try {
      if (this.sentinel) {
        try { await this.sentinel.release(); } catch (e) {}
        this.sentinel = null;
      }
      this.sentinel = await navigator.wakeLock.request('screen');
      this.sentinel.addEventListener('release', () => {
        this.sentinel = null;
        // 如果当前仍需要常亮且页面可见，说明是系统行为引起的临时释放，准备自动重获
        if (this.isActive && typeof document !== 'undefined' && document.visibilityState === 'visible') {
          setTimeout(() => {
            if (this.isActive) this.requestNativeWakeLock();
          }, 500);
        }
      });
      return true;
    } catch (err) {
      return false;
    }
  }

  // 兜底微视频（专供部分禁止或未放开 navigator.wakeLock 的移动端浏览器）
  ensureFallbackVideo() {
    if (typeof document === 'undefined') return null;
    if (!this.fallbackVideo) {
      const v = document.createElement('video');
      v.setAttribute('playsinline', '');
      v.setAttribute('webkit-playsinline', '');
      v.setAttribute('muted', '');
      v.muted = true;
      v.setAttribute('loop', '');
      v.style.position = 'fixed';
      v.style.top = '-9999px';
      v.style.left = '-9999px';
      v.style.width = '1px';
      v.style.height = '1px';
      v.style.opacity = '0.01';
      v.style.pointerEvents = 'none';
      v.style.zIndex = '-1';
      // 1秒空白静音 mp4 base64 数据
      v.src = 'data:video/mp4;base64,AAAAHGZ0eXBtcDQyAAAAAG1wNDJpc29tYXZjMQAAADpmcmVlAAAF+W1kYXQAAAAAAAABAAEAABAAEQAAABAAAAABAQEAAAABAAAAAQAAAAAAAAABAAAAGnZkYXRhc2UAAAAAAAABAAEAAAEAAAAB';
      document.body.appendChild(v);
      this.fallbackVideo = v;
    }
    return this.fallbackVideo;
  }

  async acquire() {
    this.isActive = true;
    this.bindLifecycleListeners();
    let success = await this.requestNativeWakeLock();

    // 如果原生唤醒锁不可用或报错，启用微视频播放兜底
    if (!success) {
      try {
        const vid = this.ensureFallbackVideo();
        if (vid && vid.paused) {
          await vid.play();
          success = true;
        }
      } catch (e) {
        // 用户手势限制等
      }
    }

    this.notifyStatus(true);
    return true;
  }

  async release() {
    this.isActive = false;
    if (this.sentinel) {
      try {
        await this.sentinel.release();
      } catch (e) {}
      this.sentinel = null;
    }

    if (this.fallbackVideo) {
      try {
        this.fallbackVideo.pause();
      } catch (e) {}
    }

    this.notifyStatus(false);
  }
}

export const globalWakeLock = new ScreenWakeLockController();
