import {
  renderAdvice,
  renderBacktest,
  renderCandidates,
  renderParsedRules,
  renderParameters,
  renderPlaybooks,
  renderResultsTable,
  renderScope,
  renderSummaryGrid,
  renderSummaryText,
  renderTopMeta,
} from "./render.js";
import { buildStrategyState } from "./strategy-engine.js";
import { fallbackPayload } from "./fallback-data.js";

const strategyForm = document.getElementById("strategyForm");
let currentPlaybookId = null;

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
  playbookStatus: document.getElementById("playbookStatus"),
  playbookHeadline: document.getElementById("playbookHeadline"),
  playbookGrid: document.getElementById("playbookGrid"),
  scopeNote: document.getElementById("scopeNote"),
  adviceGrid: document.getElementById("adviceGrid"),
  parsedRules: document.getElementById("parsedRules"),
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
    playbookId: currentPlaybookId,
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

function applyPayload(payload, scope = readFormValues().scope) {
  const strategy = payload.strategy;
  const results = payload.results;
  const items = [...results.items].sort((a, b) => b.score.total - a.score.total);

  renderTopMeta(
    elements.generatedAt,
    elements.scopeStatus,
    payload.generated_at,
    results.live_data ? "实时数据" : "演示数据",
  );
  currentPlaybookId = strategy.selected_playbook_id ?? currentPlaybookId;
  elements.playbookHeadline.textContent =
    strategy.playbook_headline || "系统先给出几种可量化版本，你可以任选其一。";
  elements.playbookStatus.textContent = currentPlaybookId ? "已选择方案" : "等待选择";
  renderPlaybooks(
    elements.playbookGrid,
    strategy.playbooks || [],
    currentPlaybookId,
    strategy.recommended_playbook_id || null,
  );
  renderAdvice(elements.adviceGrid, strategy.advice);
  renderParsedRules(elements.parsedRules, strategy.parsed_rules);
  renderParameters(elements.parameterGrid, strategy.parameters);
  renderSummaryText(elements.strategySummary, strategy.summary);
  renderScope(elements.scopeLabel, elements.scopeNote, scope, results.note);
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
    applyPayload(payload, "main_board");
  } catch {
    applyPayload(fallbackPayload, "main_board");
  }
}

async function renderAll() {
  const formValues = readFormValues();
  const localPlan = buildStrategyState(formValues);

  renderAdvice(elements.adviceGrid, localPlan.advice);
  elements.playbookHeadline.textContent =
    localPlan.playbook_headline || "系统先给出几种可量化版本，你可以任选其一。";
  elements.playbookStatus.textContent = currentPlaybookId ? "已选择方案" : "等待选择";
  renderPlaybooks(
    elements.playbookGrid,
    localPlan.playbooks || [],
    currentPlaybookId,
    localPlan.recommended_playbook_id || null,
  );
  renderParsedRules(elements.parsedRules, localPlan.parsed_rules);
  renderParameters(elements.parameterGrid, localPlan.parameters);
  renderSummaryText(elements.strategySummary, localPlan.summary);
  renderTopMeta(elements.generatedAt, elements.scopeStatus, "--", "生成中");

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
        playbook_id: currentPlaybookId,
      }),
    });
    applyPayload(payload, formValues.scope);
  } catch {
    applyPayload(
      {
        ...fallbackPayload,
        strategy: localPlan,
        results: {
          ...fallbackPayload.results,
          label: formValues.scope,
        },
      },
      formValues.scope,
    );
  }
}

strategyForm.addEventListener("submit", (event) => {
  event.preventDefault();
  renderAll().then(() => {
    document.querySelector(".results-card").scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

elements.playbookGrid.addEventListener("click", (event) => {
  const button = event.target.closest("[data-playbook-id]");
  if (!button) {
    return;
  }
  currentPlaybookId = button.dataset.playbookId;
  renderAll();
});

loadBootstrap();
