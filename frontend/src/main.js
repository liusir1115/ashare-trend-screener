import {
  renderAdvice,
  renderBacktest,
  renderCandidates,
  renderParameters,
  renderResultsTable,
  renderScope,
  renderSummaryGrid,
  renderSummaryText,
  renderTopMeta,
} from "./render.js";
import { buildStrategyState } from "./strategy-engine.js";
import { fallbackPayload } from "./fallback-data.js";

const strategyForm = document.getElementById("strategyForm");
const runPreviewButton = document.getElementById("runPreviewButton");

const elements = {
  narrative: document.getElementById("strategyNarrative"),
  marketScope: document.getElementById("marketScope"),
  styleFocus: document.getElementById("styleFocus"),
  holdingPeriod: document.getElementById("holdingPeriod"),
  riskTolerance: document.getElementById("riskTolerance"),
  valuationWeight: document.getElementById("valuationWeight"),
  prioritySignal: document.getElementById("prioritySignal"),
  generatedAt: document.getElementById("generatedAt"),
  scopeLabel: document.getElementById("scopeLabel"),
  scopeStatus: document.getElementById("scopeStatus"),
  scopeNote: document.getElementById("scopeNote"),
  adviceGrid: document.getElementById("adviceGrid"),
  parameterGrid: document.getElementById("parameterGrid"),
  strategySummary: document.getElementById("strategySummary"),
  summaryGrid: document.getElementById("summaryGrid"),
  candidateList: document.getElementById("candidateList"),
  resultsTable: document.getElementById("resultsTable"),
  backtestMetrics: document.getElementById("backtestMetrics"),
};

function readFormValues() {
  return {
    narrative: elements.narrative.value,
    scope: elements.marketScope.value,
    style: elements.styleFocus.value,
    holding: elements.holdingPeriod.value,
    risk: elements.riskTolerance.value,
    valuation: elements.valuationWeight.value,
    priority: elements.prioritySignal.value,
  };
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
}

function applyPayload(payload) {
  const strategy = payload.strategy;
  const results = payload.results;
  const items = [...results.items].sort((a, b) => b.score.total - a.score.total);

  renderTopMeta(elements.generatedAt, elements.scopeStatus, payload.generated_at, results.live_data ? "实时样本已接入" : "样本回退模式");
  renderAdvice(elements.adviceGrid, strategy.advice);
  renderParameters(elements.parameterGrid, strategy.parameters);
  renderSummaryText(elements.strategySummary, strategy.summary);
  renderScope(elements.scopeLabel, elements.scopeNote, results.label === "全市场" ? "all" : readFormValues().scope, results.note);
  renderBacktest(elements.backtestMetrics, {
    holdDays: payload.backtest.hold_days,
    stopLoss: payload.backtest.stop_loss,
    takeProfit: payload.backtest.take_profit,
    maxPositions: payload.backtest.max_positions,
  });
  renderSummaryGrid(elements.summaryGrid, items);
  renderCandidates(elements.candidateList, items);
  renderResultsTable(elements.resultsTable, items);
}

async function loadBootstrap() {
  try {
    const payload = await fetchJson("/api/mvp/bootstrap");
    applyPayload(payload);
  } catch {
    applyPayload(fallbackPayload);
  }
}

async function renderAll() {
  const formValues = readFormValues();
  const localPlan = buildStrategyState(formValues);

  renderAdvice(elements.adviceGrid, localPlan.advice);
  renderParameters(elements.parameterGrid, localPlan.parameters);
  renderSummaryText(elements.strategySummary, localPlan.summary);
  renderTopMeta(elements.generatedAt, elements.scopeStatus, "--", "正在生成策略方案");

  try {
    const payload = await fetchJson("/api/mvp/strategy", {
      method: "POST",
      body: JSON.stringify({
        narrative: formValues.narrative,
        market_scope: formValues.scope,
        style_focus: formValues.style,
        holding_period: formValues.holding,
        risk_tolerance: formValues.risk,
        valuation_weight: formValues.valuation,
        priority_signal: formValues.priority,
      }),
    });
    applyPayload(payload);
  } catch {
    const offlinePayload = {
      ...fallbackPayload,
      strategy: localPlan,
      results: {
        ...fallbackPayload.results,
        label: formValues.scope === "star_market" ? "科创板" : formValues.scope === "all" ? "全市场" : "主板",
      },
    };
    applyPayload(offlinePayload);
  }
}

strategyForm.addEventListener("submit", (event) => {
  event.preventDefault();
  renderAll().then(() => {
    document.querySelector(".main-rail").scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

runPreviewButton.addEventListener("click", () => {
  renderAll().then(() => {
    document.querySelector(".main-rail").scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

loadBootstrap();
