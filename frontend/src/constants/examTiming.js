/**
 * 公考行测实战做题节奏与模块标准建议用时基准库
 */

export const DEFAULT_EXAM_DURATION_MINUTES = 120; // 标准行测考试时长 120 分钟

export const SECTION_TIMING_BENCHMARKS = {
  politics: {
    name: "政治理论",
    perQSec: 30,
    targetMin: 8,
    badgeColor: "indigo",
    desc: "新思想与时政要点，依靠第一反应快速选定，控制在 30 秒/题内"
  },
  common_sense: {
    name: "常识判断",
    perQSec: 30,
    targetMin: 10,
    badgeColor: "blue",
    desc: "法律文史综合常识，会就会、不会排除后快速蒙猜，切忌久拖"
  },
  verbal: {
    name: "言语理解与表达",
    perQSec: 48,
    targetMin: 32,
    badgeColor: "teal",
    desc: "语境逻辑与中心主旨抓取，兼顾正确率与速度，45~50 秒/题"
  },
  quantity: {
    name: "数量关系",
    perQSec: 60,
    targetMin: 15,
    badgeColor: "amber",
    desc: "挑选会做的 3~5 题精做，其余代入排除或合理蒙选，切莫恋战"
  },
  reasoning: {
    name: "判断推理",
    perQSec: 48,
    targetMin: 32,
    badgeColor: "purple",
    desc: "图推与类比速战速决，定义与逻辑论证预留充足审题时间"
  },
  data_analysis: {
    name: "资料分析",
    perQSec: 75,
    targetMin: 25,
    badgeColor: "rose",
    desc: "行测核心抢分主力阵地，熟练运用截位直除与速算技巧，必须留足时间"
  }
};

/**
 * 根据模块 ID 或模块名称智能匹配基准用时
 */
export function getSectionBenchmark(secId = "", secName = "") {
  if (secId && SECTION_TIMING_BENCHMARKS[secId]) {
    return SECTION_TIMING_BENCHMARKS[secId];
  }
  const name = String(secName);
  if (name.includes("资料")) return SECTION_TIMING_BENCHMARKS.data_analysis;
  if (name.includes("数量")) return SECTION_TIMING_BENCHMARKS.quantity;
  if (name.includes("言语")) return SECTION_TIMING_BENCHMARKS.verbal;
  if (name.includes("判断")) return SECTION_TIMING_BENCHMARKS.reasoning;
  if (name.includes("政治")) return SECTION_TIMING_BENCHMARKS.politics;
  if (name.includes("常识")) return SECTION_TIMING_BENCHMARKS.common_sense;

  return {
    name: secName || "综合模块",
    perQSec: 50,
    targetMin: 15,
    badgeColor: "blue",
    desc: "标准客观选择题做题节奏"
  };
}

/**
 * 格式化秒数为 hh:mm:ss 或 mm:ss
 */
export function formatTimerSeconds(seconds) {
  if (!seconds || seconds <= 0) return "00:00";
  const s = Math.floor(seconds % 60);
  const m = Math.floor((seconds / 60) % 60);
  const h = Math.floor(seconds / 3600);

  const pad = (n) => String(n).padStart(2, "0");
  if (h > 0) {
    return `${pad(h)}:${pad(m)}:${pad(s)}`;
  }
  return `${pad(m)}:${pad(s)}`;
}

/**
 * 格式化秒数为中文时间表达
 */
export function formatSecondsToChinese(seconds) {
  if (!seconds || seconds <= 0) return "0秒";
  const s = Math.floor(seconds % 60);
  const m = Math.floor((seconds / 60) % 60);
  const h = Math.floor(seconds / 3600);

  if (h > 0) {
    return `${h}小时${m ? m + '分' : ''}${s ? s + '秒' : ''}`;
  }
  if (m > 0) {
    return `${m}分${s ? s + '秒' : ''}`;
  }
  return `${s}秒`;
}

/**
 * 行测纸质模考常见做题时长预设
 */
export const EXAM_DURATION_PRESETS = [
  { min: 120, label: "标准模考 120m", desc: "国考/省考行测标准考场控时" },
  { min: 90, label: "高压冲刺 90m", desc: "抗压实战练习，逼出潜能" },
  { min: 60, label: "半卷强化 60m", desc: "三大主力模块连做" },
  { min: 30, label: "小卷微模 30m", desc: "午间/晚间碎片时间模考" },
  { min: 15, label: "专项突击 15m", desc: "单篇资料或专项突破" }
];

/**
 * 公考实战常见做题策略路线
 */
export const PAPER_EXAM_STRATEGIES = [
  {
    id: "default",
    name: "大纲标准顺序",
    desc: "按试卷题号从头到尾稳步推进"
  },
  {
    id: "data_first",
    name: "资料主力抢分流",
    desc: "精力最充沛时攻克高性价比资料分析"
  },
  {
    id: "easy_first",
    name: "先易后难抢分流",
    desc: "先拿稳常识言语图推，后啃大题"
  }
];

/**
 * 考场温和提示音生成器 (基于原生 Web Audio API，无须外部音频文件)
 */
export function playExamChime(type = "lap") {
  if (typeof window === "undefined" || !window.AudioContext && !window.webkitAudioContext) return;
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    const ctx = new AudioCtx();
    const now = ctx.currentTime;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    if (type === "start") {
      // 欢快两音阶上行
      osc.type = "sine";
      osc.frequency.setValueAtTime(523.25, now); // C5
      osc.frequency.exponentialRampToValueAtTime(659.25, now + 0.15); // E5
      gain.gain.setValueAtTime(0.2, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
      osc.start(now);
      osc.stop(now + 0.5);
    } else if (type === "warning") {
      // 警示双音
      osc.type = "triangle";
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.setValueAtTime(349.23, now + 0.18);
      gain.gain.setValueAtTime(0.25, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.6);
      osc.start(now);
      osc.stop(now + 0.6);
    } else if (type === "finish") {
      // 考场结束长钟声
      osc.type = "sine";
      osc.frequency.setValueAtTime(392.00, now); // G4
      gain.gain.setValueAtTime(0.3, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 1.2);
      osc.start(now);
      osc.stop(now + 1.2);
    } else {
      // lap 打卡清脆音
      osc.type = "sine";
      osc.frequency.setValueAtTime(880, now); // A5
      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
      osc.start(now);
      osc.stop(now + 0.3);
    }
  } catch (e) {
    // 忽略音频上下文限制
  }
}

/**
 * 考场广播朗读器 (基于 Web Speech API)
 */
export function speakExamBroadcast(text) {
  if (typeof window === "undefined" || !('speechSynthesis' in window)) return;
  try {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "zh-CN";
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  } catch (e) {
    // 忽略朗读异常
  }
}

