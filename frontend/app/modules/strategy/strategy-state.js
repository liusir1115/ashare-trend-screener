import { getScopeLabel, holdingLabels, priorityLabels, styleLabels } from "../../contracts/ui-copy.js";
import { buildPlaybookPack, applySelectedPlaybook } from "./playbooks.js";
import { collectNarrativeRules } from "./rules.js";
import { getBaseDaysRule, getPressureRange, getValuationRule, getVolumeRule } from "./thresholds.js";

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
        detail: "不同市场波动差异大，参数不要混在一起回测。",
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
    summary: `当前策略可先按“${styleLabels[effectiveFormValues.style]} + ${
      holdingLabels[effectiveFormValues.holding]
    }”测试，优先在 ${getScopeLabel(effectiveFormValues.scope)} 里验证“${
      priorityLabels[effectiveFormValues.priority]
    }”是否有效。策略原文：${formValues.narrative.trim()}`,
  };
}

export { getScopeLabel };
