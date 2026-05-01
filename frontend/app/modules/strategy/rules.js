function addRule(rules, group, label) {
  rules.push({ group, label });
}

export function collectNarrativeRules(narrativeText) {
  const rules = [];

  const monthMatch = narrativeText.match(/(?:筑底|横盘|盘整|底部).{0,10}?(\d{1,2})\s*个?\s*月/);
  if (monthMatch) {
    addRule(rules, "数值规则", `筑底时长 >= ${Number(monthMatch[1]) * 20} 天`);
  }

  const dayMatch = narrativeText.match(/(?:筑底|横盘|盘整|底部).{0,10}?(\d{2,3})\s*天/);
  if (dayMatch) {
    addRule(rules, "数值规则", `筑底时长 >= ${dayMatch[1]} 天`);
  }

  const pressureMatch = narrativeText.match(/(?:上方压力|压力|套牢盘).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%/);
  if (pressureMatch) {
    addRule(rules, "数值规则", `上方压力 <= ${pressureMatch[1]}%`);
  }

  const volumeMatch = narrativeText.match(/(?:量比|放量).{0,8}?(\d(?:\.\d+)?)/);
  if (volumeMatch) {
    addRule(rules, "数值规则", `量比 >= ${volumeMatch[1]}`);
  }

  const stopLossMatch = narrativeText.match(/(?:止损|回撤).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%/);
  if (stopLossMatch) {
    addRule(rules, "交易管理", `止损 ${stopLossMatch[1]}%`);
  }

  const takeProfitMatch = narrativeText.match(/(?:止盈|目标收益).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%/);
  if (takeProfitMatch) {
    addRule(rules, "交易管理", `止盈 ${takeProfitMatch[1]}%`);
  }

  if (narrativeText.includes("左侧")) {
    addRule(rules, "风格偏好", "偏好左侧切入");
  }

  if (narrativeText.includes("右侧")) {
    addRule(rules, "风格偏好", "偏好右侧确认");
  }

  if (/(涨停|回封|首板)/.test(narrativeText)) {
    addRule(rules, "交易管理", "要求涨停或回封确认");
  }

  if (/(低估|估值修复|估值)/.test(narrativeText)) {
    addRule(rules, "风格偏好", "强调估值修复");
  }

  if (narrativeText.includes("筹码")) {
    addRule(rules, "风格偏好", "强调筹码结构");
  }

  if (/(趋势|均线|多头排列)/.test(narrativeText)) {
    addRule(rules, "风格偏好", "强调趋势和均线");
  }

  return rules.length ? rules : [{ group: "系统判断", label: "未识别到额外文字约束" }];
}
