import { askStrategyQuestion, loadBootstrapPayload, loadStrategyPayload } from "../api/mvp-client.js";
import { pageCopy } from "../contracts/ui-copy.js";
import { pageElements, questionForm, readStrategyForm, scrollToResults, strategyForm } from "../utils/dom-elements.js";
import {
  renderAdvice,
  renderBacktest,
  renderCandidates,
  renderParsedRules,
  renderParameters,
  renderMarketReview,
  renderPlaybooks,
  renderResultsTable,
  renderScope,
  renderSourceStatus,
  renderSummaryGrid,
  renderSummaryText,
  renderQuestionAnswer,
  renderTopMeta,
} from "../view/index.js";
import { buildStrategyState } from "../modules/strategy/index.js";
import { buildFallbackPayload, fallbackPayloadSeed } from "../utils/fallback-payload.js";
import { getSelectedPlaybookId, setSelectedPlaybookId, syncSelectedPlaybook } from "../stores/strategy-store.js";

function getCurrentFormValues() {
  return readStrategyForm(getSelectedPlaybookId());
}

function applyPayloadToPage(payload, scope = getCurrentFormValues().scope) {
  const strategyData = payload.strategy;
  const resultsData = payload.results;
  const sortedItems = [...resultsData.items].sort((left, right) => right.score.total - left.score.total);

  renderTopMeta(
    pageElements.generatedAtText,
    pageElements.scopeStatusText,
    payload.generated_at,
    resultsData.live_data ? pageCopy.liveData : pageCopy.demoData,
  );

  syncSelectedPlaybook(strategyData);
  pageElements.playbookHeadlineText.textContent =
    strategyData.playbook_headline || pageCopy.defaultPlaybookHeadline;
  pageElements.playbookStatusText.textContent = getSelectedPlaybookId()
    ? pageCopy.selectedPlaybook
    : pageCopy.waitingPlaybook;

  renderPlaybooks(
    pageElements.playbookGrid,
    strategyData.playbooks || [],
    getSelectedPlaybookId(),
    strategyData.recommended_playbook_id || null,
  );
  renderAdvice(pageElements.adviceGrid, strategyData.advice);
  renderParsedRules(pageElements.parsedRulesBox, strategyData.parsed_rules);
  renderParameters(pageElements.parameterGrid, strategyData.parameters);
  renderSummaryText(pageElements.strategySummaryBox, strategyData.summary);
  renderMarketReview(pageElements, payload.market_review);
  renderSourceStatus(pageElements, payload.source_status);
  renderScope(pageElements.scopeLabelText, pageElements.scopeNoteText, scope, resultsData.note);
  renderBacktest(pageElements.backtestMetrics, {
    holdDays: payload.backtest.hold_days,
    stopLoss: payload.backtest.stop_loss,
    takeProfit: payload.backtest.take_profit,
    maxPositions: payload.backtest.max_positions,
  });
  renderSummaryGrid(pageElements.summaryGrid, sortedItems);
  renderCandidates(pageElements.candidateList, sortedItems);
  renderResultsTable(pageElements.resultsTableBody, sortedItems);
}

function renderLocalPreview(formValues) {
  const localPlan = buildStrategyState(formValues);

  renderAdvice(pageElements.adviceGrid, localPlan.advice);
  pageElements.playbookHeadlineText.textContent = localPlan.playbook_headline || pageCopy.defaultPlaybookHeadline;
  pageElements.playbookStatusText.textContent = getSelectedPlaybookId()
    ? pageCopy.selectedPlaybook
    : pageCopy.waitingPlaybook;
  renderPlaybooks(
    pageElements.playbookGrid,
    localPlan.playbooks || [],
    getSelectedPlaybookId(),
    localPlan.recommended_playbook_id || null,
  );
  renderParsedRules(pageElements.parsedRulesBox, localPlan.parsed_rules);
  renderParameters(pageElements.parameterGrid, localPlan.parameters);
  renderSummaryText(pageElements.strategySummaryBox, localPlan.summary);
  renderTopMeta(pageElements.generatedAtText, pageElements.scopeStatusText, "--", pageCopy.loading);

  return localPlan;
}

async function loadPage() {
  try {
    const bootstrapPayload = await loadBootstrapPayload();
    applyPayloadToPage(bootstrapPayload, "main_board");
  } catch {
    applyPayloadToPage(fallbackPayloadSeed, "main_board");
  }
}

async function refreshResults() {
  const formValues = getCurrentFormValues();
  const localPlan = renderLocalPreview(formValues);

  try {
    const strategyPayload = await loadStrategyPayload(formValues);
    applyPayloadToPage(strategyPayload, formValues.scope);
  } catch {
    applyPayloadToPage(buildFallbackPayload(localPlan, formValues.scope), formValues.scope);
  }
}

async function submitQuestion(question) {
  if (!question.trim()) {
    return;
  }

  pageElements.qaAnswer.textContent = "正在回答...";
  try {
    const payload = await askStrategyQuestion(getCurrentFormValues(), question);
    renderQuestionAnswer(pageElements, payload);
  } catch {
    renderQuestionAnswer(pageElements, {
      mode: "规则问答",
      answer: "当前问答服务暂时不可用，但不影响策略筛选和复盘查看。",
      suggestions: ["今天有没有高切低？", "反转策略怎么量化？"],
    });
  }
}

function bindStrategyForm() {
  strategyForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await refreshResults();
    scrollToResults();
  });
}

function bindPlaybookClicks() {
  pageElements.playbookGrid.addEventListener("click", async (event) => {
    const clickedButton = event.target.closest("[data-playbook-id]");
    if (!clickedButton) {
      return;
    }

    setSelectedPlaybookId(clickedButton.dataset.playbookId);
    await refreshResults();
  });
}

function bindQuestionForm() {
  questionForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await submitQuestion(pageElements.questionInput.value);
  });
}

function bindQuestionSuggestions() {
  pageElements.qaSuggestions.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-question]");
    if (!button) {
      return;
    }

    pageElements.questionInput.value = button.dataset.question;
    await submitQuestion(button.dataset.question);
  });
}

export function initStrategyPage() {
  bindStrategyForm();
  bindPlaybookClicks();
  bindQuestionForm();
  bindQuestionSuggestions();
  loadPage();
}
