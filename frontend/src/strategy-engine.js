import { getScopeLabel, holdingLabels, priorityLabels, styleLabels } from "./content.js";

function buildPlaybookPack(formValues) {
  const narrativeText = formValues.narrative || "";

  if (/(反转|反弹|V反|拐头)/.test(narrativeText)) {
    return {
      headline: "我把“反转策略”拆成了 3 种常见做法，你可以先选一种再看结果。",
      recommendedId: "reversal_base",
      selectedId: formValues.playbookId || null,
      items: [
        {
          id: "reversal_base",
          title: "底部反转型",
          thesis: "更看重筑底、均线拐头和压力释放，不追求最猛的爆量。",
          fit_for: "适合想做中短波段反转的人。",
          highlights: ["筑底 60-120 天", "量比 >= 1.3", "上方压力 <= 6%"],
          overrides: { style: "rebound", holding: "swing", risk: "balanced", priority: "base" },
        },
        {
          id: "reversal_left",
          title: "左侧试错型",
          thesis: "更早介入，放宽放量要求，但更强调筹码和空间。",
          fit_for: "适合偏左侧，愿意用更紧止损换更早位置。",
          highlights: ["筑底 40-90 天", "量比 >= 1.1", "止损更紧"],
          overrides: { style: "rebound", holding: "short", risk: "aggressive", priority: "chip" },
        },
        {
          id: "reversal_right",
          title: "右侧确认型",
          thesis: "先等站回均线和放量确认，宁可慢一点，也更稳一点。",
          fit_for: "适合不想猜底，想先看到转强信号再上车。",
          highlights: ["量比 >= 1.8", "更看重均线确认", "上方压力 <= 5%"],
          overrides: { style: "trend_start", holding: "swing", risk: "conservative", priority: "volume" },
        },
      ],
    };
  }

  if (/(突破|启动|主升|放量)/.test(narrativeText)) {
    return {
      headline: "这段描述更像趋势启动，我先给你 3 套常见的突破版本。",
      recommendedId: "breakout_classic",
      selectedId: formValues.playbookId || null,
      items: [
        {
          id: "breakout_classic",
          title: "经典突破型",
          thesis: "把平台突破和放量确认放在第一位，先求确定性。",
          fit_for: "适合趋势启动的基础版本。",
          highlights: ["量比 >= 1.8", "突破确认优先", "筑底 60-120 天"],
          overrides: { style: "breakout", holding: "swing", risk: "balanced", priority: "volume" },
        },
        {
          id: "breakout_value",
          title: "估值修复突破型",
          thesis: "在突破逻辑里，再加一层估值不过热和行业匹配。",
          fit_for: "适合主板里偏低估修复的启动机会。",
          highlights: ["估值要求更严", "适合更久一点", "行业热度要达标"],
          overrides: { style: "breakout", holding: "trend", valuation: "high", priority: "valuation" },
        },
        {
          id: "breakout_fast",
          title: "短线爆量型",
          thesis: "更看重爆量和短周期反馈，适合快进快出。",
          fit_for: "适合做强信号的短线机会。",
          highlights: ["量比 >= 2.0", "持有 3-7 天", "强信号优先"],
          overrides: { style: "breakout", holding: "short", risk: "aggressive", priority: "volume" },
        },
      ],
    };
  }

  return {
    headline: "你的描述还比较笼统，我先给你 3 套能落地的默认版本。",
    recommendedId: "balanced_default",
    selectedId: formValues.playbookId || null,
    items: [
      {
        id: "balanced_default",
        title: "平衡试探型",
        thesis: "先用一套中性的参数把方向跑通，再决定往哪边加码。",
        fit_for: "适合描述还不够具体时先验证方向。",
        highlights: ["风险平衡", "波段持有", "先在主板验证"],
        overrides: {},
      },
      {
        id: "chip_first",
        title: "筹码优先型",
        thesis: "先把上方压力和筹码干净度放在第一位。",
        fit_for: "适合特别看重上方筹码干净的人。",
        highlights: ["上方压力更严", "筹码结构优先", "容忍更少噪音"],
        overrides: { risk: "conservative", priority: "chip" },
      },
      {
        id: "trend_first",
        title: "趋势确认型",
        thesis: "先确认均线、斜率和量能，再决定是否上车。",
        fit_for: "适合偏右侧确认。",
        highlights: ["均线多头优先", "放量确认更严", "更适合右侧交易"],
        overrides: { style: "trend_start", risk: "conservative", priority: "volume" },
      },
    ],
  };
}

function collectNarrativeRules(narrativeText) {
  const rules = [];

  const addRule = (group, label) => {
    rules.push({ group, label });
  };

  const monthMatch = narrativeText.match(/(?:筑底|横盘|盘整|底部).{0,10}?(\d{1,2})\s*个?\s*月/);
  if (monthMatch) {
    addRule("数值规则", `筑底时长 >= ${Number(monthMatch[1]) * 20} 天`);
  }

  const dayMatch = narrativeText.match(/(?:筑底|横盘|盘整|底部).{0,10}?(\d{2,3})\s*天/);
  if (dayMatch) {
    addRule("数值规则", `筑底时长 >= ${dayMatch[1]} 天`);
  }

  const pressureMatch = narrativeText.match(/(?:上方压力|压力|套牢盘).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%/);
  if (pressureMatch) {
    addRule("数值规则", `上方压力 <= ${pressureMatch[1]}%`);
  }

  const volumeMatch = narrativeText.match(/(?:量比|放量).{0,8}?(\d(?:\.\d+)?)/);
  if (volumeMatch) {
    addRule("数值规则", `量比 >= ${volumeMatch[1]}`);
  }

  const stopLossMatch = narrativeText.match(/(?:止损|回撤).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%/);
  if (stopLossMatch) {
    addRule("交易管理", `止损 ${stopLossMatch[1]}%`);
  }

  const takeProfitMatch = narrativeText.match(/(?:止盈|目标收益).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%/);
  if (takeProfitMatch) {
    addRule("交易管理", `止盈 ${takeProfitMatch[1]}%`);
  }

  if (narrativeText.includes("左侧")) {
    addRule("风格偏好", "偏好左侧切入");
  }

  if (narrativeText.includes("右侧")) {
    addRule("风格偏好", "偏好右侧确认");
  }

  if (/(涨停|回封|首板)/.test(narrativeText)) {
    addRule("交易管理", "要求涨停或回封确认");
  }

  if (/(低估|估值修复|估值)/.test(narrativeText)) {
    addRule("风格偏好", "强调估值修复");
  }

  if (narrativeText.includes("筹码")) {
    addRule("风格偏好", "强调筹码结构");
  }

  if (/(趋势|均线|多头排列)/.test(narrativeText)) {
    addRule("风格偏好", "强调趋势和均线");
  }

  return rules.length ? rules : [{ group: "系统判断", label: "未识别到额外文字约束" }];
}

function applySelectedPlaybook(formValues, playbookPack) {
  const selectedPlaybook = playbookPack.items.find((item) => item.id === playbookPack.selectedId);
  const overrides = selectedPlaybook?.overrides || {};

  return {
    ...formValues,
    style: overrides.style || formValues.style,
    holding: overrides.holding || formValues.holding,
    risk: overrides.risk || formValues.risk,
    valuation: overrides.valuation || formValues.valuation,
    priority: overrides.priority || formValues.priority,
  };
}

function getPressureRange(effectiveFormValues) {
  if (effectiveFormValues.risk === "conservative") {
    return "3% - 5%";
  }

  if (effectiveFormValues.risk === "balanced") {
    return "4% - 6%";
  }

  return "5% - 8%";
}

function getVolumeRule(effectiveFormValues) {
  if (effectiveFormValues.style === "breakout") {
    return ">= 1.8";
  }

  if (effectiveFormValues.style === "trend_start") {
    return ">= 1.5";
  }

  return ">= 1.3";
}

function getBaseDaysRule(effectiveFormValues) {
  if (effectiveFormValues.holding === "trend") {
    return "90 - 150 天";
  }

  if (effectiveFormValues.holding === "swing") {
    return "60 - 120 天";
  }

  return "35 - 80 天";
}

function getValuationRule(effectiveFormValues) {
  if (effectiveFormValues.valuation === "high") {
    return "优先低于行业中位";
  }

  if (effectiveFormValues.valuation === "medium") {
    return "不过热即可";
  }

  return "仅作辅助条件";
}

export function buildStrategyState(formValues) {
  const playbookPack = buildPlaybookPack(formValues);
  const parsedRules = collectNarrativeRules(formValues.narrative);
  const effectiveFormValues = applySelectedPlaybook(
    { ...formValues, playbookId: playbookPack.selectedId },
    playbookPack,
  );

  const pressureRange = getPressureRange(effectiveFormValues);
  const volumeRule = getVolumeRule(effectiveFormValues);
  const baseDaysRule = getBaseDaysRule(effectiveFormValues);
  const valuationRule = getValuationRule(effectiveFormValues);

  return {
    scope: effectiveFormValues.scope,
    playbooks: playbookPack.items,
    selected_playbook_id: playbookPack.selectedId,
    recommended_playbook_id: playbookPack.recommendedId,
    playbook_headline: playbookPack.headline,
    advice: [
      {
        title: "推荐市场",
        value:
          effectiveFormValues.scope === "main_board"
            ? "先测主板"
            : effectiveFormValues.scope === "star_market"
            ? "单测科创板"
            : "分市场分别测",
        detail: "不同市场波动差别大，参数不要混在一起回测。",
      },
      {
        title: "上方压力",
        value: pressureRange,
        detail: "这是当前策略里最建议先固定的阈值。",
      },
      {
        title: "核心驱动",
        value: priorityLabels[effectiveFormValues.priority],
        detail: "先确定一个主信号，其余条件只做辅助。",
      },
      {
        title: "量比门槛",
        value: volumeRule,
        detail: "突破型策略需要更严格的放量确认。",
      },
    ],
    parsed_rules: parsedRules,
    parameters: [
      {
        label: "上方筹码压力",
        value: pressureRange,
        hint: "风险越保守，这个阈值越要收紧。",
      },
      {
        label: "放量标准",
        value: volumeRule,
        hint: "量比越高，突破有效性通常越强。",
      },
      {
        label: "筑底时长",
        value: baseDaysRule,
        hint: "持股周期越长，越需要更充分的底部整理。",
      },
      {
        label: "估值要求",
        value: valuationRule,
        hint: "主板更适合重视估值，科创板可以稍微放宽。",
      },
    ],
    summary: `当前策略先按“${styleLabels[effectiveFormValues.style]} + ${
      holdingLabels[effectiveFormValues.holding]
    }”理解，优先在 ${getScopeLabel(effectiveFormValues.scope)} 里验证“${
      priorityLabels[effectiveFormValues.priority]
    }”是否有效。策略原文：${formValues.narrative.trim()}`,
  };
}

export { getScopeLabel };
