function reversalPlaybookPack(formValues, narrativeText) {
  if (!/(反转|反弹|V反|拐头)/.test(narrativeText)) {
    return null;
  }

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

function breakoutPlaybookPack(formValues, narrativeText) {
  if (!/(突破|启动|主升|放量)/.test(narrativeText)) {
    return null;
  }

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

function defaultPlaybookPack(formValues) {
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

export function buildPlaybookPack(formValues) {
  const narrativeText = formValues.narrative || "";
  return (
    reversalPlaybookPack(formValues, narrativeText) ||
    breakoutPlaybookPack(formValues, narrativeText) ||
    defaultPlaybookPack(formValues)
  );
}

export function applySelectedPlaybook(formValues, playbookPack) {
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
