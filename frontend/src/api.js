import { fallbackPayload } from "./fallback-data.js";

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
}

export async function loadBootstrapPayload() {
  return requestJson("/api/mvp/bootstrap");
}

export async function loadStrategyPayload(formValues) {
  return requestJson("/api/mvp/strategy", {
    method: "POST",
    body: JSON.stringify({
      narrative: formValues.narrative,
      market_scope: formValues.scope,
      style_focus: formValues.style,
      holding_period: formValues.holding,
      risk_tolerance: formValues.risk,
      valuation_weight: formValues.valuation,
      priority_signal: formValues.priority,
      playbook_id: formValues.playbookId,
    }),
  });
}

export function buildFallbackPayload(localPlan, scope) {
  return {
    ...fallbackPayload,
    strategy: localPlan,
    results: {
      ...fallbackPayload.results,
      label: scope,
    },
  };
}
