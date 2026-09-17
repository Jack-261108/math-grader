/**
 * 公考行测速算与资料分析高频核心公式及模块口诀库
 * 涵盖：十字相乘法、两期比重升降判定、平均数增长率、隔年增长率、特征数字法、截位直除法等
 */

export const FORMULA_CATEGORIES = [
  { id: 'all', name: '全部公式' },
  { id: 'ratio', name: '比重与平均数' },
  { id: 'growth', name: '增长率与隔年' },
  { id: 'speed_math', name: '速算与技巧' }
];

export const FORMULA_LIST = [
  {
    id: 'cross_multiplication',
    name: '十字相乘法模型',
    shortName: '十字相乘',
    category: 'speed_math',
    icon: 'fa-solid fa-xmark',
    badgeColor: 'from-amber-500 to-orange-500',
    tags: ['资料分析', '数量关系', '混合增长率'],
    jingle: '部分平均居两边，总体平均居中间；交叉作差得比例，所得比例为分母！',
    derivation: [
      '核心原理：设两个组成部分的指标分别为 a、b（且 a < r < b），混合后的总体指标为 r。',
      '交叉作差：部分 A 对应差值 (b - r)，部分 B 对应差值 (r - a)。',
      '结论比例：A : B = (b - r) : (r - a)。',
      '⚠️ 考场死穴：所得比值 A:B 永远对应各自指标分母的“基期实际量”之比（如基期总人数、基期总产值），绝非现期量之比！'
    ],
    example: {
      question: '【真题例题】2023年上半年某市城镇居民人均消费支出同比增长 6.2%，农村居民同比增长 9.8%，全市全体居民人均消费支出同比增长 7.4%。求 2022 年上半年该市城镇与农村居民的消费支出基期之比。',
      options: ['A. 2 : 1', 'B. 1 : 2', 'C. 3 : 2', 'D. 4 : 3'],
      answer: 'A',
      analysis: '总体增长率 7.4% 居中，与农村 9.8% 交叉作差得 9.8% - 7.4% = 2.4%；与城镇 6.2% 交叉作差得 7.4% - 6.2% = 1.2%。二者之比为 2.4% : 1.2% = 2 : 1。直接秒选 A 项！'
    },
    pitfalls: '切勿直接用现期消费支出代替基期权重；总体增长率必然严格介于两部分之间，且必然靠近基数较大的一侧。'
  },
  {
    id: 'two_period_proportion',
    name: '两期比重升降判定模型',
    shortName: '两期比重升降',
    category: 'ratio',
    icon: 'fa-solid fa-scale-balanced',
    badgeColor: 'from-blue-500 to-indigo-600',
    tags: ['资料分析', '比重变化', '高频必考'],
    jingle: '部分增速 a 大于整体增速 b，比重上升；a 小于 b，比重下降；差值必小于 |a - b|！',
    derivation: [
      '现期比重 P1 = A / B，基期比重 P0 = (A / B) × [(1 + b) / (1 + a)]。',
      '两期比重差值 ΔP = P1 - P0 = (A / B) × [(a - b) / (1 + a)]。',
      '性质 1（方向）：因 A/B > 0 且 1+a > 0，故 ΔP 的符号完全取决于 (a - b)。若 a > b 则比重上升，若 a < b 则比重下降。',
      '性质 2（幅度上限）：因部分占总体比重 A/B < 1 且通常 1+a > 1，故两期比重变化值严格满足 |ΔP| < |a - b|。'
    ],
    example: {
      question: '【真题例题】2022年某国高技术制造业增加值同比增长 7.4%，占全部规模以上工业的比重为 15.5%（全部规模以上工业增加值同比增长 3.6%）。问高技术制造业增加值占规模以上工业的比重较上年：',
      options: ['A. 上升 3.8 个百分点', 'B. 下降 3.8 个百分点', 'C. 上升 0.5 个百分点', 'D. 下降 0.5 个百分点'],
      answer: 'C',
      analysis: '部分增速 a = 7.4%，整体增速 b = 3.6%。因 a > b，比重必然上升，秒杀排除 B、D 项；差值 ΔP 必小于 |7.4% - 3.6%| = 3.8%，排除 A 项。无需精算，5秒直接秒杀锁定 C！'
    },
    pitfalls: '题目问的是“百分点”而非“%”；关注题干时间是“同比”还是“环比”。'
  },
  {
    id: 'avg_growth_rate',
    name: '平均数增长率公式',
    shortName: '平均数增长率',
    category: 'ratio',
    icon: 'fa-solid fa-divide',
    badgeColor: 'from-emerald-500 to-teal-600',
    tags: ['资料分析', '平均数', '高频公式'],
    jingle: '总量增速为 a，份数增速为 b；平均数增长率 = (a - b) / (1 + b)！',
    derivation: [
      '现期平均数 Avg1 = A / B，基期平均数 Avg0 = [A / (1 + a)] / [B / (1 + b)]。',
      '增长率 r = (Avg1 - Avg0) / Avg0 = [(1 + a) / (1 + b)] - 1 = (a - b) / (1 + b)。',
      '应用要领：分子为“总量增速减份数增速”，分母为“1 + 份数增速”。与两期比重公式分母 (1+a) 严格区分开！'
    ],
    example: {
      question: '【真题例题】2023年某省农林牧渔业总产值 8200 亿元，同比增长 5.5%；从业人员数量同比下降 1.2%。问该省该年度农林牧渔业人均产值同比增长约：',
      options: ['A. 6.8%', 'B. 4.3%', 'C. -6.8%', 'D. 5.5%'],
      answer: 'A',
      analysis: '产值增速 a = 5.5%，人数增速 b = -1.2%。代入公式：r = [5.5% - (-1.2%)] / [1 + (-1.2%)] = 6.7% / 0.988 ≈ 6.8%。直接锁定 A！'
    },
    pitfalls: '分母是 (1 + b)，即份数（单位）的增长率，千万不要除以 (1 + a)；当 b 为负数时注意负负得正。'
  },
  {
    id: 'biennial_growth_rate',
    name: '隔年增长率公式',
    shortName: '隔年增长率',
    category: 'growth',
    icon: 'fa-solid fa-forward-step',
    badgeColor: 'from-purple-500 to-indigo-600',
    tags: ['资料分析', '隔年期', '间隔增长'],
    jingle: '隔年增速等于两期增速之和，再加上两期增速乘积：r = r1 + r2 + r1 × r2！',
    derivation: [
      '设第一年增速为 r1，第二年增速为 r2，基期为 A0。',
      '现期 A2 = A0 × (1 + r1) × (1 + r2) = A0 × (1 + r1 + r2 + r1 × r2)。',
      '两期复合增长率 r = r1 + r2 + r1 × r2。',
      '心算技巧：通常 r1 × r2 数值较小（如 5% × 8% = 0.4%），先算 r1 + r2 锁定大致范围，再根据选项间距决定是否补上微小乘积。'
    ],
    example: {
      question: '【真题例题】2024年某市高新技术产业增加值同比增长 12.5%，2023年同比增长 8.0%。问 2024 年该市高新技术产业增加值较 2022 年增长了约：',
      options: ['A. 20.5%', 'B. 21.5%', 'C. 22.5%', 'D. 24.0%'],
      answer: 'B',
      analysis: 'r1 = 12.5%, r2 = 8.0%。r1 + r2 = 20.5%；r1 × r2 = 12.5% × 8% = 1.0%。合共 r = 20.5% + 1.0% = 21.5%。心算 3 秒出答案，选 B！'
    },
    pitfalls: '小心乘积的百分号陷阱，如 10% × 10% = 1% 而非 10%；若其中一年为负增长，加号变为减号。'
  },
  {
    id: 'feature_fraction_method',
    name: '特征数字法与百倍分数速查',
    shortName: '特征数字法',
    category: 'speed_math',
    icon: 'fa-solid fa-hashtag',
    badgeColor: 'from-rose-500 to-pink-600',
    tags: ['速算技巧', '增长量计算', '乘除速算'],
    jingle: '化小数为百倍分数：A × x% ≈ A / n；增长量公式：现期 × r / (1 + r) = 现期 / (n + 1)！',
    derivation: [
      '常用分数速记金字塔：',
      '• 1/6 ≈ 16.7%    • 1/7 ≈ 14.3%    • 1/8 = 12.5%    • 1/9 ≈ 11.1%',
      '• 1/11 ≈ 9.1%    • 1/12 ≈ 8.3%    • 1/13 ≈ 7.7%    • 1/14 ≈ 7.1%',
      '• 1/15 ≈ 6.7%    • 1/16 = 6.25%   • 1/17 ≈ 5.9%    • 1/19 ≈ 5.3%',
      '增长量秒杀模型：若 r ≈ 1/n，则增长量 Δ = 现期 × r / (1 + r) = 现期 / (n + 1)；若为减少量，则 Δ = 现期 / (n - 1)。'
    ],
    example: {
      question: '【真题例题】2023年我国某轻工产品出口额 8472 亿元，同比增长 14.3%。问该产品该年度出口额同比增加约多少亿元？',
      options: ['A. 1059 亿元', 'B. 1210 亿元', 'C. 980 亿元', 'D. 1150 亿元'],
      answer: 'A',
      analysis: 'r = 14.3% ≈ 1/7，对应 n = 7。增长量 = 现期 / (n + 1) = 8472 / (7 + 1) = 8472 / 8 = 1059 亿元！将两位数复杂乘除直接降维成一位数除法，秒选 A！'
    },
    pitfalls: '如果是负增长（减少量），分母是 (n - 1) 而不是 (n + 1)；若实际增速略大于 1/n，计算所得增量应略微往大估。'
  },
  {
    id: 'truncated_division',
    name: '截位直除保留法则',
    shortName: '截位直除法',
    category: 'speed_math',
    icon: 'fa-solid fa-bullseye',
    badgeColor: 'from-cyan-600 to-blue-600',
    tags: ['资料分析', '算式速算', '必修基本功'],
    jingle: '分子不动，分母截位！选项差距大截前两位，选项差距小截前三位，四舍五入防偏差！',
    derivation: [
      '标准原则：资料分析分数求值（如基期量 A/(1+r)、比重 A/B），分子绝对不截位保持原数，仅对分母截位。',
      '两步研判准则：',
      '1. 步看选项首位：若 4 个选项首位各不相同，或首位相同但次位差 ≥ 1（大差距），分母四舍五入保留前 2 位有效数字直除；',
      '2. 选项差距小：若选项首位相同且次位差 < 1（如 23.4 与 23.8），分母四舍五入保留前 3 位有效数字直除。'
    ],
    example: {
      question: '【真题例题】计算基期量：54219 / (1 + 13.8%)。选项：A. 4.76万  B. 4.35万  C. 4.12万  D. 3.89万。',
      options: ['A. 4.76万', 'B. 4.35万', 'C. 4.12万', 'D. 3.89万'],
      answer: 'A',
      analysis: '选项首位虽然大多为 4，但第二位 7、3、1 差距显著。分母 1.138 截前两位为 11。算式变为 54219 / 11。商首位为 4（4×11=44，余102），次位为 9，最接近 4.76万，5秒锁定 A！'
    },
    pitfalls: '四舍五入看的是被截掉的第 3 或第 4 位数字；注意量级单位转换（亿元与万元、吨与万吨），防止差 10 倍。'
  }
];

/**
 * 根据错题上下文智能推荐最相关的核心公式
 */
export function getRecommendedFormulas(context = {}) {
  const { type, questionData } = context;
  if (!questionData) return FORMULA_LIST;

  // 速算练习册上下文
  if (type === 'math') {
    const priorityIds = ['feature_fraction_method', 'truncated_division', 'cross_multiplication'];
    return [
      ...FORMULA_LIST.filter(f => priorityIds.includes(f.id)),
      ...FORMULA_LIST.filter(f => !priorityIds.includes(f.id))
    ];
  }

  // 行测客观题上下文
  const stem = (questionData.stem || '').toLowerCase();
  const sec = (questionData.section_name || '');
  const expr = (questionData.expression || '');

  let topId = null;
  if (stem.includes('比重') || expr.includes('比重')) {
    topId = 'two_period_proportion';
  } else if (stem.includes('平均') || stem.includes('每') || expr.includes('平均')) {
    topId = 'avg_growth_rate';
  } else if (stem.includes('隔年') || stem.includes('间隔') || stem.includes('两年')) {
    topId = 'biennial_growth_rate';
  } else if (sec.includes('数量') || stem.includes('混合') || stem.includes('浓度')) {
    topId = 'cross_multiplication';
  }

  if (topId) {
    return [
      ...FORMULA_LIST.filter(f => f.id === topId),
      ...FORMULA_LIST.filter(f => f.id !== topId)
    ];
  }

  return FORMULA_LIST;
}
