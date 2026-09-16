/**
 * 智能解析资料分析材料文本并以纯净优雅的自然段落排版呈现
 */
export function renderStructuredMaterialHtml(rawText, hasImages = false) {
  if (!rawText || !rawText.trim()) return '';
  // 1. 过滤材料末尾残留的“请回答 116～120 题”印刷噪音
  let cleanText = rawText.replace(/(?:^|\n)\s*(?:根据以[下上]资料[，,]?\s*)?请?回答\s*\d+\s*[～~至-]\s*\d+\s*题[。.\s]*$/g, '').trim();
  if (!cleanText) cleanText = rawText.trim();

  const lines = cleanText.split('\n').map(l => l.trim()).filter(l => l.length > 0);

  // 2. 将因 PDF 物理硬换行而切断的单句智能拼接缝合为连贯自然的段落
  const mergedParagraphs = [];
  let curPara = '';

  for (const line of lines) {
    const isSpecialLine = /^【(?:图表|表|图)[^】]+】/.test(line) ||
      /^(?:图|插图|附图)\s*(\d+|[一二三四五六七八九十]|[\d～~-]+年|[A-Za-z]|\b)/.test(line) ||
      (/^图\s+/.test(line) && !line.endsWith('。')) ||
      ((/^表\s*(\d+|[一二三四五六七八九十]|[\d～~-]+年|[A-Za-z]|\b)/.test(line) ||
        (line.startsWith('表') && ['统计', '对比', '情况', '增速', '规模', '结构', '明细', '清单', '如下'].some(k => line.includes(k)))) &&
        line.length < 50 && !line.endsWith('。'));

    if (isSpecialLine) {
      if (curPara) {
        mergedParagraphs.push(curPara);
        curPara = '';
      }
      mergedParagraphs.push(line);
    } else {
      if (!curPara) {
        curPara = line;
      } else {
        const lastChar = curPara.slice(-1);
        if (['。', '！', '？', '”', '；'].includes(lastChar)) {
          mergedParagraphs.push(curPara);
          curPara = line;
        } else {
          curPara += line;
        }
      }
    }
  }
  if (curPara) {
    mergedParagraphs.push(curPara);
  }

  return mergedParagraphs.map(p => {
    const isHeader = /^【(?:图表|表|图)[^】]+】/.test(p) || /^(?:图|表)\s*\d+/.test(p);
    if (isHeader) {
      return `<p class="font-bold text-slate-800 my-1 text-center">${escapeHtml(p)}</p>`;
    }
    return `<p class="indent-4 leading-relaxed my-1 text-slate-700">${escapeHtml(p)}</p>`;
  }).join('');
}

export function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
