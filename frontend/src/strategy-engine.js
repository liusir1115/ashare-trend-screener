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

function buildPlaybooks(formValues) {
  const text = formValues.narrative || "";

  if (/(反转|反弹|V反|拐头)/.test(text)) {
    return {
      headline: "我把“反转策略”拆成了 3 种常见做法，你可以先选一种再跑结果。",
      recommendedId: "reversal_base",
      selectedId: formValues.playbookId || null,
      items: [
        {
          id: "reversal_base",
          title: "底部反转型",
          thesis: "强调筑底、均线拐头和压力释放，不追求最极端爆量。",
          fit_for: "适合想做中短波段反转的场景。",
          highlights: ["筑底 60-120 天", "量比 >= 1.3", "上方压力 <= 6%"],
          overrides: { style: "rebound", holding: "swing", risk: "balanced", priority: "base" },
        },
        {
          id: "reversal_left",
          title: "左侧试错型",
          thesis: "更早介入，放松放量要求，但要求筹码和空间更干净。",
          fit_for: "适合偏左侧、用更紧止损换更早位置。",
          highlights: ["筑底 40-90 天", "量比 >= 1.1", "止损偏紧"],
          overrides: { style: "rebound", holding: "short", risk: "aggressive", priority: "chip" },
        },
        {
          id: "reversal_right",
          title: "右侧确认型",
          thesis: "要求放量和均线确认，宁可晚一点，也提高胜率。",
          fit_for: "适合不想猜底、希望看到明显转强信号再进。",
          highlights: ["量比 >= 1.8", "更看重均线", "上方压力 <= 5%"],
          overrides: { style: "trend_start", holding: "swing", risk: "conservative", priority: "volume" },
        },
      ],
    };
  }

  if (/(突破|启动|主升|放量)/.test(text)) {
    return {
      headline: "这类描述更像趋势启动，我先给你 3 个常见突破版本。",
      recommendedId: "breakout_classic",
      selectedId: formValues.playbookId || null,
      items: [
        {
          id: "breakout_classic",
          title: "经典突破型",
          thesis: "平台突破和放量确认为核心，先求确定性。",
          fit_for: "适合趋势启动的基础版本。",
          highlights: ["量比 >= 1.8", "突破确认优先", "筑底 60-120 天"],
          overrides: { style: "breakout", holding: "swing", risk: "balanced", priority: "volume" },
        },
        {
          id: "breakout_value",
          title: "估值修复突破型",
          thesis: "在突破逻辑里额外强调估值不过热和行业匹配。",
          fit_for: "适合主板、偏低估修复的启动机会。",
          highlights: ["估值阈值更严", "持有更久", "行业热度达标"],
          overrides: { style: "breakout", holding: "trend", valuation: "high", priority: "valuation" },
        },
        {
          id: "breakout_fast",
          title: "短线爆量型",
          thesis: "更强调爆量和短周期反馈，适合快进快出。",
          fit_for: "适合短线强信号博弈。",
          highlights: ["量比 >= 2.0", "持有 3-7 天", "强信号优先"],
          overrides: { style: "breakout", holding: "short", risk: "aggressive", priority: "volume" },
        },
      ],
    };
  }

  return {
    headline: "你的描述还比较抽象，我先给你 3 个可落地的默认版本。",
    recommendedId: "balanced_default",
    selectedId: formValues.playbookId || null,
    items: [
      {
        id: "balanced_default",
        title: "平衡试探型",
        thesis: "先用一版中性参数把方向跑通，再决定往哪边加码。",
        fit_for: "适合描述还模糊的时候先验证。",
        highlights: ["风险平衡", "波段持有", "优先主板验证"],
        overrides: {},
      },
      {
        id: "chip_first",
        title: "筹码优先型",
        thesis: "先把上方压力和筹码干净度放在第一位。",
        fit_for: "适合强调上方筹码干净的思路。",
        highlights: ["上方压力更严", "筹码结构优先", "容忍更少噪音"],
        overrides: { risk: "conservative", priority: "chip" },
      },
      {
        id: "trend_first",
        title: "趋势确认型",
        thesis: "先确认均线、斜率和量能，再决定是否上车。",
        fit_for: "适合偏右侧确认。",
        highlights: ["均线多头优先", "放量确认更严", "右侧交易"],
        overrides: { style: "trend_start", risk: "conservative", priority: "volume" },
      },
    ],
  };
}

function extractNarrativeRules(narrative) {
  const text = narrative || "";
  const rules = [];
  const pushRule = (group, label) => rules.push({ group, label });

  const monthMatch = text.match(/(?:筑底|横盘|盘整|底部).{0,10}?(\d{1,2})\s*个?月/);
  if (monthMatch) pushRule("数值规则", `筑底时长 >= ${Number(monthMatch[1]) * 20} 天`);

  const dayMatch = text.match(/(?:筑底|横盘|盘整|底部).{0,10}?(\d{2,3})\s*天/);
  if (dayMatch) pushRule("数值规则", `筑底时长 >= ${dayMatch[1]} 天`);

  const pressureMatch = text.match(/(?:上方压力|压力|套牢盘).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%/);
  if (pressureMatch) pushRule("数值规则", `上方压力 <= ${pressureMatch[1]}%`);

  const volumeMatch = text.match(/(?:量比|放量).{0,8}?(\d(?:\.\d+)?)/);
  if (volumeMatch) pushRule("数值规则", `量比 >= ${volumeMatch[1]}`);

  const stopLossMatch = text.match(/(?:止损|回撤).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%/);
  if (stopLossMatch) pushRule("交易管理", `止损 ${stopLossMatch[1]}%`);

  const takeProfitMatch = text.match(/(?:止盈|目标收益).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%/);
  if (takeProfitMatch) pushRule("交易管理", `止盈 ${takeProfitMatch[1]}%`);

  if (text.includes("左侧")) pushRule("风格偏好", "偏好左侧切入");
  if (text.includes("右侧")) pushRule("风格偏好", "偏好右侧确认");
  if (/(涨停|回封|首板)/.test(text)) pushRule("交易管理", "要求涨停或回封确认");
  if (/(低估|估值修复|估值)/.test(text)) pushRule("风格偏好", "强调估值修复");
  if (text.includes("筹码")) pushRule("风格偏好", "强调筹码结构");
  if (/(趋势|均线|多头排列)/.test(text)) pushRule("风格偏好", "强调趋势与均线");

  return rules.length ? rules : [{ group: "系统判断", label: "未识别到额外文字约束" }];
}

function applyPlaybook(formValues, playbookPack) {
  const selected = playbookPack.items.find((item) => item.id === playbookPack.selectedId);
  const overrides = selected?.overrides || {};
  return {
    ...formValues,
    style: overrides.style || formValues.style,
    holding: overrides.holding || formValues.holding,
    risk: overrides.risk || formValues.risk,
    valuation: overrides.valuation || formValues.valuation,
    priority: overrides.priority || formValues.priority,
  };
}

export function buildStrategyState(formValues) {
  const playbookPack = buildPlaybooks(formValues);
  const parsedRules = extractNarrativeRules(formValues.narrative);
  const effective = applyPlaybook({ ...formValues, playbookId: playbookPack.selectedId }, playbookPack);

  const overheadPressure =
    effective.risk === "conservative" ? "3% - 5%" : effective.risk === "balanced" ? "4% - 6%" : "5% - 8%";
  const volumeRatio =
    effective.style === "breakout" ? ">= 1.8" : effective.style === "trend_start" ? ">= 1.5" : ">= 1.3";
  const baseDays =
    effective.holding === "trend" ? "90 - 150 天" : effective.holding === "swing" ? "60 - 120 天" : "35 - 80 天";
  const valuationRule =
    effective.valuation === "high" ? "优先低于行业中位" : effective.valuation === "medium" ? "不过热即可" : "仅作辅助条件";

  return {
    scope: effective.scope,
    playbooks: playbookPack.items,
    selected_playbook_id: playbookPack.selectedId,
    recommended_playbook_id: playbookPack.recommendedId,
    playbook_headline: playbookPack.headline,
    advice: [
      {
        title: "推荐市场",
        value:
          effective.scope === "main_board" ? "先测主板" : effective.scope === "star_market" ? "单测科创板" : "分市场分别测试",
        detail: "不同市场波动差异大，参数不要混在一起回测。",
      },
      {
        title: "上方压力",
        value: overheadPressure,
        detail: "这是当前策略里最建议先固定的阈值。",
      },
      {
        title: "核心驱动",
        value: priorityLabels[effective.priority],
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
    summary: `当前按“${styleLabels[effective.style]} + ${holdingLabels[effective.holding]}”理解你的策略，优先在${scopeLabels[effective.scope]}里验证“${priorityLabels[effective.priority]}”是否有效。策略原文：${formValues.narrative.trim()}`,
  };
}

export function getScopeLabel(scope) {
  return scopeLabels[scope] || scope;
}
