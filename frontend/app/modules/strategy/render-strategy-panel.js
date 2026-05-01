import { getScopeLabel, pageCopy } from "../../contracts/ui-copy.js";

export function renderAdvice(container, adviceItems) {
  container.innerHTML = adviceItems.map((item) => `<article class="advice-card"><span class="card-label">${item.title}</span><strong class="card-value">${item.value}</strong><p class="card-detail">${item.detail}</p></article>`).join("");
}

export function renderPlaybooks(container, playbooks, selectedPlaybookId, recommendedPlaybookId) {
  container.innerHTML = (playbooks || []).map((playbook) => buildPlaybookCard(playbook, selectedPlaybookId, recommendedPlaybookId)).join("");
}

function buildPlaybookCard(playbook, selectedPlaybookId, recommendedPlaybookId) {
  const isSelected = playbook.id === selectedPlaybookId;
  const isRecommended = playbook.id === recommendedPlaybookId;
  return `<article class="playbook-card ${isSelected ? "active" : ""}"><div class="playbook-title-row"><h3>${playbook.title}</h3>${buildPlaybookBadge(isSelected, isRecommended)}</div><p class="playbook-body">${playbook.thesis}</p><p class="playbook-fit">${playbook.fit_for}</p><div class="playbook-highlights">${(playbook.highlights || []).map((item) => `<span class="playbook-chip">${item}</span>`).join("")}</div><button class="playbook-button" data-playbook-id="${playbook.id}">${isSelected ? "已采用" : "采用这套"}</button></article>`;
}

function buildPlaybookBadge(isSelected, isRecommended) {
  if (isSelected) return '<span class="playbook-badge">当前方案</span>';
  if (isRecommended) return '<span class="playbook-badge">推荐</span>';
  return "";
}

export function renderParsedRules(container, parsedRules) {
  const rulesByGroup = new Map();
  (parsedRules || []).forEach((rule) => {
    const groupName = typeof rule === "string" ? "系统判断" : rule.group || "系统判断";
    const label = typeof rule === "string" ? rule : rule.label;
    if (!rulesByGroup.has(groupName)) rulesByGroup.set(groupName, []);
    rulesByGroup.get(groupName).push(label);
  });
  container.innerHTML = [...rulesByGroup.entries()].map(([groupName, labels]) => `<div class="parsed-group"><div class="parsed-group-title">${groupName}</div><div class="parsed-group-list">${labels.map((label) => `<span class="parsed-pill">${label}</span>`).join("")}</div></div>`).join("");
}

export function renderParameters(container, parameterItems) {
  container.innerHTML = parameterItems.map((item) => `<div class="parameter-item"><div><div class="parameter-name">${item.label}</div><div class="card-detail">${item.hint}</div></div><div class="parameter-value">${item.value}</div></div>`).join("");
}

export function renderSummaryText(container, summaryText) {
  container.textContent = summaryText;
}

export function renderTopMeta(generatedAtElement, scopeStatusElement, generatedAt, statusText = pageCopy.loading) {
  generatedAtElement.textContent = generatedAt || "--";
  scopeStatusElement.textContent = statusText;
}

export function renderScope(scopeLabelElement, scopeNoteElement, scope, noteText) {
  scopeLabelElement.textContent = getScopeLabel(scope);
  scopeNoteElement.textContent = noteText;
}

export function renderBacktest(container, backtest) {
  container.innerHTML = `<div class="metric-chip"><span class="metric-label">持有天数</span><span class="metric-value">${backtest.holdDays}</span></div><div class="metric-chip"><span class="metric-label">止损</span><span class="metric-value">${backtest.stopLoss}</span></div><div class="metric-chip"><span class="metric-label">止盈</span><span class="metric-value">${backtest.takeProfit}</span></div><div class="metric-chip"><span class="metric-label">最多持仓</span><span class="metric-value">${backtest.maxPositions}</span></div>`;
}

export function renderSummaryGrid(container, resultItems) {
  const passedCount = resultItems.filter((item) => item.passedFilters).length;
  const watchCount = resultItems.filter((item) => !item.passedFilters && item.score.total >= 55).length;
  const topItem = resultItems[0];
  const summaryCards = [
    { title: "样本数", value: String(resultItems.length), detail: "这次展示出来的股票数量。" },
    { title: "通过数", value: String(passedCount), detail: "完全过线的股票数量。" },
    { title: "观察数", value: String(watchCount), detail: "还差一点，可以继续跟踪的股票。" },
    { title: "最高分", value: topItem ? `${topItem.score.total}` : "--", detail: topItem ? topItem.symbol : "暂时没有结果" },
  ];
  container.innerHTML = summaryCards.map((card) => `<article class="summary-card"><span class="card-label">${card.title}</span><div class="summary-value">${card.value}</div><div class="summary-detail">${card.detail}</div></article>`).join("");
}
