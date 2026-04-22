import { getScopeLabel, pageCopy } from "./content.js";
import { formatPercent, getCandidateStatus } from "./render-utils.js";

export function renderAdvice(container, adviceItems) {
  container.innerHTML = adviceItems
    .map(
      (item) => `
        <article class="advice-card">
          <span class="card-label">${item.title}</span>
          <strong class="card-value">${item.value}</strong>
          <p class="card-detail">${item.detail}</p>
        </article>
      `,
    )
    .join("");
}

export function renderPlaybooks(container, playbooks, selectedPlaybookId, recommendedPlaybookId) {
  container.innerHTML = (playbooks || [])
    .map((playbook) => buildPlaybookCard(playbook, selectedPlaybookId, recommendedPlaybookId))
    .join("");
}

function buildPlaybookCard(playbook, selectedPlaybookId, recommendedPlaybookId) {
  const isSelected = playbook.id === selectedPlaybookId;
  const isRecommended = playbook.id === recommendedPlaybookId;

  return `
    <article class="playbook-card ${isSelected ? "active" : ""}">
      <div class="playbook-title-row">
        <h3>${playbook.title}</h3>
        ${buildPlaybookBadge(isSelected, isRecommended)}
      </div>
      <p class="playbook-body">${playbook.thesis}</p>
      <p class="playbook-fit">${playbook.fit_for}</p>
      <div class="playbook-highlights">
        ${(playbook.highlights || []).map((item) => `<span class="playbook-chip">${item}</span>`).join("")}
      </div>
      <button class="playbook-button" data-playbook-id="${playbook.id}">
        ${isSelected ? "已采用" : "采用这套"}
      </button>
    </article>
  `;
}

function buildPlaybookBadge(isSelected, isRecommended) {
  if (isSelected) {
    return '<span class="playbook-badge">当前方案</span>';
  }

  if (isRecommended) {
    return '<span class="playbook-badge">推荐</span>';
  }

  return "";
}

export function renderParsedRules(container, parsedRules) {
  const rulesByGroup = new Map();

  (parsedRules || []).forEach((rule) => {
    const groupName = typeof rule === "string" ? "系统判断" : rule.group || "系统判断";
    const label = typeof rule === "string" ? rule : rule.label;

    if (!rulesByGroup.has(groupName)) {
      rulesByGroup.set(groupName, []);
    }

    rulesByGroup.get(groupName).push(label);
  });

  container.innerHTML = [...rulesByGroup.entries()]
    .map(
      ([groupName, labels]) => `
        <div class="parsed-group">
          <div class="parsed-group-title">${groupName}</div>
          <div class="parsed-group-list">
            ${labels.map((label) => `<span class="parsed-pill">${label}</span>`).join("")}
          </div>
        </div>
      `,
    )
    .join("");
}

export function renderParameters(container, parameterItems) {
  container.innerHTML = parameterItems
    .map(
      (item) => `
        <div class="parameter-item">
          <div>
            <div class="parameter-name">${item.label}</div>
            <div class="card-detail">${item.hint}</div>
          </div>
          <div class="parameter-value">${item.value}</div>
        </div>
      `,
    )
    .join("");
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
  container.innerHTML = `
    <div class="metric-chip">
      <span class="metric-label">持有天数</span>
      <span class="metric-value">${backtest.holdDays}</span>
    </div>
    <div class="metric-chip">
      <span class="metric-label">止损</span>
      <span class="metric-value">${backtest.stopLoss}</span>
    </div>
    <div class="metric-chip">
      <span class="metric-label">止盈</span>
      <span class="metric-value">${backtest.takeProfit}</span>
    </div>
    <div class="metric-chip">
      <span class="metric-label">最多持仓</span>
      <span class="metric-value">${backtest.maxPositions}</span>
    </div>
  `;
}

export function renderSummaryGrid(container, resultItems) {
  const passedCount = resultItems.filter((item) => item.passedFilters).length;
  const watchCount = resultItems.filter((item) => !item.passedFilters && item.score.total >= 55).length;
  const topItem = resultItems[0];

  const summaryCards = [
    {
      title: "样本数",
      value: String(resultItems.length),
      detail: "这次展示出来的股票数量。",
    },
    {
      title: "通过数",
      value: String(passedCount),
      detail: "完全过线的股票数量。",
    },
    {
      title: "观察数",
      value: String(watchCount),
      detail: "还差一点，可以继续跟踪的股票。",
    },
    {
      title: "最高分",
      value: topItem ? `${topItem.score.total}` : "--",
      detail: topItem ? topItem.symbol : "暂时没有结果",
    },
  ];

  container.innerHTML = summaryCards
    .map(
      (card) => `
        <article class="summary-card">
          <span class="card-label">${card.title}</span>
          <div class="summary-value">${card.value}</div>
          <div class="summary-detail">${card.detail}</div>
        </article>
      `,
    )
    .join("");
}

export function renderCandidates(container, resultItems) {
  const sections = [
    {
      title: "通过",
      className: "bucket-pass",
      items: resultItems.filter((item) => item.passedFilters).slice(0, 3),
      emptyText: "当前没有完全通过的股票。",
    },
    {
      title: "观察",
      className: "bucket-watch",
      items: resultItems.filter((item) => !item.passedFilters && item.score.total >= 55).slice(0, 3),
      emptyText: "当前没有接近通过的股票。",
    },
    {
      title: "淘汰",
      className: "bucket-blocked",
      items: resultItems.filter((item) => !item.passedFilters && item.score.total < 55).slice(0, 3),
      emptyText: "当前没有明显需要淘汰的样本。",
    },
  ];

  container.innerHTML = sections.map(buildCandidateSection).join("");
}

function buildCandidateSection(section) {
  const cardsHtml = section.items.length
    ? section.items.map(buildCandidateCard).join("")
    : `<div class="candidate-empty">${section.emptyText}</div>`;

  return `
    <section class="candidate-section ${section.className}">
      <div class="candidate-section-head">
        <h3>${section.title}</h3>
        <span class="candidate-count">${section.items.length}</span>
      </div>
      <div class="candidate-section-list">${cardsHtml}</div>
    </section>
  `;
}

function buildCandidateCard(item) {
  const status = getCandidateStatus(item);
  const reasons = item.passedFilters ? item.score.reasons : item.failedReasons;

  return `
    <article class="candidate-card">
      <div class="candidate-main">
        <div class="candidate-head">
          <h3>${item.symbol}</h3>
          <span class="pill ${status.className}">${status.label}</span>
        </div>
        <div class="candidate-sub">${getScopeLabel(item.marketSegment)} / ${item.tradeDate}</div>
        <ul class="reasons">
          ${reasons.slice(0, 3).map((reason) => `<li>${reason}</li>`).join("")}
        </ul>
      </div>
      <div class="candidate-side">
        <div class="candidate-score">${item.score.total}</div>
        <div class="candidate-metrics">
          <span>量比 ${item.metrics.volumeRatio}</span>
          <span>上方压力 ${formatPercent(item.metrics.overheadPressure)}</span>
          <span>筑底 ${item.metrics.baseDays} 天</span>
        </div>
      </div>
    </article>
  `;
}

export function renderResultsTable(container, resultItems) {
  container.innerHTML = resultItems
    .map((item) => {
      const status = getCandidateStatus(item);
      return `
        <tr>
          <td>${item.symbol}</td>
          <td>${getScopeLabel(item.marketSegment)}</td>
          <td>${item.score.total}</td>
          <td>${item.metrics.volumeRatio}</td>
          <td>${formatPercent(item.metrics.overheadPressure)}</td>
          <td>${item.metrics.baseDays}</td>
          <td><span class="pill ${status.className}">${status.label}</span></td>
        </tr>
      `;
    })
    .join("");
}
