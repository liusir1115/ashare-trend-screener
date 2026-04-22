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
  swing: "波段持有",
  short: "短线快进快出",
  trend: "趋势跟随",
};

const priorityLabels = {
  chip: "筹码结构",
  volume: "量价突破",
  base: "筑底时长",
  valuation: "估值修复",
};

export function buildStrategyState(formValues) {
  const { scope, risk, style, holding, valuation, priority, narrative } = formValues;

  const overheadPressure =
    risk === "conservative" ? "3% - 5%" : risk === "balanced" ? "4% - 6%" : "5% - 8%";
  const volumeRatio =
    style === "breakout" ? ">= 1.8" : style === "trend_start" ? ">= 1.5" : ">= 1.3";
  const baseDays =
    holding === "trend" ? "90 - 150 天" : holding === "swing" ? "60 - 120 天" : "35 - 80 天";
  const valuationRule =
    valuation === "high" ? "要求行业内偏低估" : valuation === "medium" ? "估值不过热即可" : "估值只做辅助";

  return {
    scope,
    advice: [
      {
        title: "建议市场",
        value:
          scope === "main_board" ? "主板优先" : scope === "star_market" ? "科创板单测" : "先分组后汇总",
        detail: "不同市场的波动和估值结构不同，阈值最好分开回测。",
      },
      {
        title: "建议阈值",
        value: overheadPressure,
        detail: "把上方筹码压力收敛成明确区间，后面更容易优化。",
      },
      {
        title: "建议驱动",
        value: priorityLabels[priority],
        detail: "建议保留一个主驱动信号，避免所有条件都变成平均主义。",
      },
    ],
    parameters: [
      {
        label: "上方筹码压力",
        value: overheadPressure,
        hint: "风险偏好越保守，越建议把压力阈值收紧。",
      },
      {
        label: "放量门槛",
        value: volumeRatio,
        hint: "突破型策略更适合提高量比要求。",
      },
      {
        label: "筑底时长",
        value: baseDays,
        hint: "持股越久，越需要更充分的底部整理。",
      },
      {
        label: "估值规则",
        value: valuationRule,
        hint: "主板更适合强调估值，科创板更适合把估值作为辅助。",
      },
    ],
    summary: `你的策略更接近“${styleLabels[style]} + ${holdingLabels[holding]}”。
建议先在${scopeLabels[scope]}里验证“${priorityLabels[priority]}”是否真的有效，再决定是否扩大到全市场。
当前输入的策略描述是：${narrative.trim()}`,
  };
}

export function getScopeLabel(scope) {
  return scopeLabels[scope] || scope;
}
