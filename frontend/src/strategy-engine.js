const scopeLabels = {
  all: "全市场",
  main_board: "主板",
  star_market: "科创板",
  growth_board: "成长板",
};

const styleLabels = {
  breakout: "平台突破",
  trend_start: "趋势启动",
  rebound: "底部反转",
};

const holdingLabels = {
  swing: "波段",
  short: "短线",
  trend: "趋势",
};

const priorityLabels = {
  chip: "筹码结构",
  volume: "放量突破",
  base: "筑底时长",
  valuation: "估值修复",
};

function extractNarrativeRules(narrative) {
  const text = narrative || "";
  const rules = [];

  const pushRule = (group, label) => rules.push({ group, label });

  const monthMatch = text.match(/(?:筑底|横盘|盘整|底部).{0,10}?(\d{1,2})\s*个?月/);
  if (monthMatch) {
    pushRule("数值规则", `筑底时长 >= ${Number(monthMatch[1]) * 20} 天`);
  }

  const dayMatch = text.match(/(?:筑底|横盘|盘整|底部).{0,10}?(\d{2,3})\s*天/);
  if (dayMatch) {
    pushRule("数值规则", `筑底时长 >= ${dayMatch[1]} 天`);
  }

  const pressureMatch = text.match(/(?:上方压力|压力|套牢盘).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%/);
  if (pressureMatch) {
    pushRule("数值规则", `上方压力 <= ${pressureMatch[1]}%`);
  }

  const volumeMatch = text.match(/(?:量比|放量).{0,8}?(\d(?:\.\d+)?)/);
  if (volumeMatch) {
    pushRule("数值规则", `量比 >= ${volumeMatch[1]}`);
  }

  const stopLossMatch = text.match(/(?:止损|回撤).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%/);
  if (stopLossMatch) {
    pushRule("交易管理", `止损 ${stopLossMatch[1]}%`);
  }

  const takeProfitMatch = text.match(/(?:止盈|目标收益).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%/);
  if (takeProfitMatch) {
    pushRule("交易管理", `止盈 ${takeProfitMatch[1]}%`);
  }

  if (text.includes("左侧")) {
    pushRule("风格偏好", "偏好左侧切入");
  }
  if (text.includes("右侧")) {
    pushRule("风格偏好", "偏好右侧确认");
  }
  if (/(涨停|回封|首板)/.test(text)) {
    pushRule("交易管理", "要求涨停或回封确认");
  }
  if (/(低估|估值修复|估值)/.test(text)) {
    pushRule("风格偏好", "强调估值修复");
  }
  if (text.includes("筹码")) {
    pushRule("风格偏好", "强调筹码结构");
  }
  if (/(趋势|均线|多头排列)/.test(text)) {
    pushRule("风格偏好", "强调趋势与均线");
  }

  return rules.length ? rules : [{ group: "系统判断", label: "未识别到额外文字约束" }];
}

export function buildStrategyState(formValues) {
  const { scope, risk, style, holding, valuation, priority, narrative } = formValues;
  const parsedRules = extractNarrativeRules(narrative);

  const overheadPressure =
    risk === "conservative" ? "3% - 5%" : risk === "balanced" ? "4% - 6%" : "5% - 8%";
  const volumeRatio =
    style === "breakout" ? ">= 1.8" : style === "trend_start" ? ">= 1.5" : ">= 1.3";
  const baseDays =
    holding === "trend" ? "90 - 150 天" : holding === "swing" ? "60 - 120 天" : "35 - 80 天";
  const valuationRule =
    valuation === "high" ? "优先低于行业中位" : valuation === "medium" ? "不过热即可" : "仅作辅助条件";

  return {
    scope,
    advice: [
      {
        title: "推荐市场",
        value:
          scope === "main_board" ? "先测主板" : scope === "star_market" ? "单测科创板" : "分市场分别测试",
        detail: "不同市场波动差异大，参数不要混在一起回测。",
      },
      {
        title: "上方压力",
        value: overheadPressure,
        detail: "这是当前策略里最建议先固定的阈值。",
      },
      {
        title: "核心驱动",
        value: priorityLabels[priority],
        detail: "先确定一个主信号，其余条件只做辅助。",
      },
      {
        title: "量比门槛",
        value: volumeRatio,
        detail: "突破型策略需要更严格的放量确认。",
      },
    ],
    parsed_rules: parsedRules,
    parameters: [
      {
        label: "上方筹码压力",
        value: overheadPressure,
        hint: "风险越保守，这个阈值越要收紧。",
      },
      {
        label: "放量标准",
        value: volumeRatio,
        hint: "量比越高，突破有效性通常越强。",
      },
      {
        label: "筑底时长",
        value: baseDays,
        hint: "持股周期越长，越需要更充分的底部整理。",
      },
      {
        label: "估值要求",
        value: valuationRule,
        hint: "主板更适合重视估值，科创板可以稍放宽。",
      },
    ],
    summary: `当前策略可先按“${styleLabels[style]} + ${holdingLabels[holding]}”来测试，优先在${scopeLabels[scope]}里验证“${priorityLabels[priority]}”是否有效。策略原文：${narrative.trim()}`,
  };
}

export function getScopeLabel(scope) {
  return scopeLabels[scope] || scope;
}
