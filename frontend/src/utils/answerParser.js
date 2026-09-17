/**
 * 行测选择题标准答案多模式高精准解析工具
 * 对齐后端 omr_judge.py 中的 parse_answer_key 规则
 */

export function parseAnswerKeyText(rawText) {
  if (!rawText || typeof rawText !== 'string') {
    return { map: {}, count: 0, maxQ: 0 };
  }

  const text = rawText.trim();
  if (!text) {
    return { map: {}, count: 0, maxQ: 0 };
  }

  const result = {};

  // 形式 A: 带明确题号的模式 (例如 1.A 或 1:A 或 1 A、1、A、1-A 等)
  const numberedRegex = /(\d+)[\s.:、-]*([A-Da-d])\b/g;
  const numberedMatches = [...text.matchAll(numberedRegex)];
  if (numberedMatches && numberedMatches.length >= 3) {
    for (const m of numberedMatches) {
      result[parseInt(m[1], 10)] = m[2].toUpperCase();
    }
    const keys = Object.keys(result).map(Number);
    if (keys.length > 0) {
      const maxQ = Math.max(...keys);
      return { map: result, count: keys.length, maxQ };
    }
  }

  // 形式 B: 题号区间模式 (例如 1-5 CBADA 6-10 ABBAC ... 31-35 BCCAC)
  const rangeRegex = /(\d+)\s*(?:[-~至—–]{1,2})\s*(\d+)[\s:：]*([A-Da-d]{1,10})/g;
  const rangeMatches = [...text.matchAll(rangeRegex)];
  if (rangeMatches && rangeMatches.length > 0) {
    let maxSeenQ = 0;
    for (const m of rangeMatches) {
      const startNum = parseInt(m[1], 10);
      const ansBlock = m[3];
      const letters = [...ansBlock].filter(c => /[ABCDabcd]/.test(c)).map(c => c.toUpperCase());

      // 附加题保护检查
      const prefixText = text.substring(Math.max(0, m.index - 30), m.index);
      const isExtra = /附加|加试|选做|选考/.test(prefixText) || (maxSeenQ > 50 && startNum <= 10);

      if (isExtra && maxSeenQ > 0) {
        for (let idx = 0; idx < letters.length; idx++) {
          const curQ = maxSeenQ + 1 + idx;
          result[curQ] = letters[idx];
        }
        maxSeenQ += letters.length;
      } else {
        for (let idx = 0; idx < letters.length; idx++) {
          const curQ = startNum + idx;
          result[curQ] = letters[idx];
          if (curQ > maxSeenQ) {
            maxSeenQ = curQ;
          }
        }
      }
    }

    const keys = Object.keys(result).map(Number);
    if (keys.length > 0) {
      return { map: result, count: keys.length, maxQ: maxSeenQ };
    }
  }

  // 形式 C: 纯字母序列（提取所有 ABCD 选项）
  const pureLetters = [...text].filter(c => /[ABCDabcd]/.test(c)).map(c => c.toUpperCase());
  for (let i = 0; i < pureLetters.length; i++) {
    result[i + 1] = pureLetters[i];
  }

  return {
    map: result,
    count: pureLetters.length,
    maxQ: pureLetters.length
  };
}
