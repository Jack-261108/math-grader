/**
 * 手机/桌面全屏与防滚动穿透辅助工具
 */

export function requestFullscreenSafe(element = document.documentElement) {
  if (typeof document === 'undefined' || !element) return;
  try {
    if (element.requestFullscreen) {
      element.requestFullscreen().catch(() => {});
    } else if (element.webkitRequestFullscreen) {
      element.webkitRequestFullscreen();
    } else if (element.mozRequestFullScreen) {
      element.mozRequestFullScreen();
    } else if (element.msRequestFullscreen) {
      element.msRequestFullscreen();
    }
  } catch (e) {
    // 忽略特定平台的全屏策略限制
  }
}

export function exitFullscreenSafe() {
  if (typeof document === 'undefined') return;
  try {
    if (document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement) {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen();
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
      }
    }
  } catch (e) {
    // 忽略异常
  }
}

export function lockBodyScroll(locked = true) {
  if (typeof document === 'undefined') return;
  if (locked) {
    document.body.style.overflow = 'hidden';
    document.body.style.touchAction = 'none';
    document.documentElement.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
    document.body.style.touchAction = '';
    document.documentElement.style.overflow = '';
  }
}

export async function lockOrientationSafe(orientation = 'landscape') {
  if (typeof window === 'undefined' || !window.screen) return false;
  const screenOri = window.screen.orientation || window.screen.mozOrientation || window.screen.msOrientation;
  if (screenOri && screenOri.lock) {
    try {
      await screenOri.lock(orientation);
      return true;
    } catch (e) {
      return false;
    }
  }
  return false;
}

export function unlockOrientationSafe() {
  if (typeof window === 'undefined' || !window.screen) return;
  const screenOri = window.screen.orientation || window.screen.mozOrientation || window.screen.msOrientation;
  if (screenOri && screenOri.unlock) {
    try {
      screenOri.unlock();
    } catch (e) {}
  }
}
