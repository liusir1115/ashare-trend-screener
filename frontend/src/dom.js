export const strategyForm = document.getElementById("strategyForm");

export const pageElements = {
  narrativeInput: document.getElementById("strategyNarrative"),
  marketScopeSelect: document.getElementById("marketScope"),
  styleFocusSelect: document.getElementById("styleFocus"),
  holdingPeriodSelect: document.getElementById("holdingPeriod"),
  riskToleranceSelect: document.getElementById("riskTolerance"),
  valuationWeightSelect: document.getElementById("valuationWeight"),
  prioritySignalSelect: document.getElementById("prioritySignal"),
  generatedAtText: document.getElementById("generatedAt"),
  scopeLabelText: document.getElementById("scopeLabel"),
  scopeStatusText: document.getElementById("scopeStatus"),
  playbookStatusText: document.getElementById("playbookStatus"),
  playbookHeadlineText: document.getElementById("playbookHeadline"),
  playbookGrid: document.getElementById("playbookGrid"),
  scopeNoteText: document.getElementById("scopeNote"),
  adviceGrid: document.getElementById("adviceGrid"),
  parsedRulesBox: document.getElementById("parsedRules"),
  parameterGrid: document.getElementById("parameterGrid"),
  strategySummaryBox: document.getElementById("strategySummary"),
  summaryGrid: document.getElementById("summaryGrid"),
  candidateList: document.getElementById("candidateList"),
  resultsTableBody: document.getElementById("resultsTable"),
  backtestMetrics: document.getElementById("backtestMetrics"),
};

export function readStrategyForm(selectedPlaybookId) {
  return {
    narrative: pageElements.narrativeInput.value,
    scope: pageElements.marketScopeSelect.value,
    style: pageElements.styleFocusSelect.value,
    holding: pageElements.holdingPeriodSelect.value,
    risk: pageElements.riskToleranceSelect.value,
    valuation: pageElements.valuationWeightSelect.value,
    priority: pageElements.prioritySignalSelect.value,
    playbookId: selectedPlaybookId,
  };
}

export function scrollToResults() {
  document.querySelector(".results-card")?.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
}
