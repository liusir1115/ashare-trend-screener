export function buildStrategyPayload(formValues) {
  return {
    narrative: formValues.narrative,
    market_scope: formValues.scope,
    style_focus: formValues.style,
    holding_period: formValues.holding,
    risk_tolerance: formValues.risk,
    valuation_weight: formValues.valuation,
    priority_signal: formValues.priority,
    playbook_id: formValues.playbookId,
  };
}

export function buildQuestionPayload(formValues, question) {
  return {
    question,
    ...buildStrategyPayload(formValues),
  };
}
