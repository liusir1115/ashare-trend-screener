import { getScopeLabel } from "./strategy-engine.js";

function statusMeta(item) {
  if (item.passedFilters) {
    return { label: "通过", className: "pill-pass" };
  }
  if ((item.score?.total || 0) >= 55) {
    return { label: "观察", className: "pill-watch" };
  }
  return { label: "淘汰", className: "pill-blocked" };
}

function percent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

export function renderAdvice(container, advice) {
  container.innerHTML = advice
    .map(
      (item) => `
        <article class="advice-card">
          <p class="eyebrow">${item.title}</p>
          <strong>${item.value}</strong>
          <p class="summary-caption">${item.detail}</p>
        </article>
      `,
    )
    .join("");
}

export function renderParameters(container, items) {
  container.innerHTML = items
    .map(
      (item) => `
        <article class="parameter-card">
          <span class="label">${item.label}</span>
          <span class="value">${item.value}</span>
          <p class="hint">${item.hint}</p>
        </article>
      `,
    )
    .join("");
}

export function renderSummaryText(container, text) {
  container.innerHTML = `<article><strong>策略摘要</strong><p>${text}</p></article>`;
}

export function renderTopMeta(generatedAtEl, scopeStatusEl, generatedAt, text = "策略已优化") {
  generatedAtEl.textContent = generatedAt;
  scopeStatusEl.textContent = text;
}

export function renderScope(scopeLabelEl, scopeNoteEl, scope, note) {
  scopeLabelEl.textContent = getScopeLabel(scope);
  scopeNoteEl.textContent = note;
}

export function renderBacktest(container, backtest) {
  container.innerHTML = `
    <div class="metric-chip">
      <span class="helper-text">持有天数</span>
      <span class="metric-value">${backtest.holdDays}</span>
    </div>
    <div class="metric-chip">
      <span class="helper-text">止损</span>
      <span class="metric-value">${backtest.stopLoss}</span>
    </div>
    <div class="metric-chip">
      <span class="helper-text">止盈</span>
      <span class="metric-value">${backtest.takeProfit}</span>
    </div>
    <div class="metric-chip">
      <span class="helper-text">最大持仓</span>
      <span class="metric-value">${backtest.maxPositions}</span>
    </div>
  `;
}

export function renderSummaryGrid(container, items) {
  const passed = items.filter((item) => item.passedFilters).length;
  const watch = items.filter((item) => !item.passedFilters && item.score.total >= 55).length;
  const avgScore = items.length
    ? (items.reduce((sum, item) => sum + item.score.total, 0) / items.length).toFixed(1)
    : "0.0";
  const top = items[0];

  const cards = [
    {
      title: "测试样本",
      value: String(items.length),
      caption: "当前策略和市场范围下的演示样本数量。",
    },
    {
      title: "通过数",
      value: String(passed),
      caption: "完全通过硬过滤的股票。",
    },
    {
      title: "观察数",
      value: String(watch),
      caption: "只差 1-2 项条件，适合继续盯。",
    },
    {
      title: "平均分",
      value: avgScore,
      caption: top ? `当前最高分是 ${top.symbol}` : "暂无样本",
    },
  ];

  container.innerHTML = cards
    .map(
      (card) => `
        <article>
          <p class="eyebrow">${card.title}</p>
          <div class="summary-value">${card.value}</div>
          <div class="summary-caption">${card.caption}</div>
        </article>
      `,
    )
    .join("");
}

export function renderCandidates(container, items) {
  container.innerHTML = items
    .slice(0, 4)
    .map((item) => {
      const status = statusMeta(item);
      const reasons = item.passedFilters ? item.score.reasons : item.failedReasons;
      const angle = Math.max(24, Math.min(360, item.score.total * 3.6));
      return `
        <article class="candidate-card">
          <div>
            <div class="candidate-subline">${getScopeLabel(item.marketSegment)} / ${item.tradeDate}${item.previewMock ? " / preview" : ""}</div>
            <h4>${item.symbol}</h4>
            <span class="pill ${status.className}">${status.label}</span>
            <ul class="reasons">
              ${reasons.slice(0, 3).map((reason) => `<li>${reason}</li>`).join("")}
            </ul>
          </div>
          <div class="candidate-score">
            <div class="score-ring" style="--score-angle:${angle}deg">
              <span>${item.score.total}</span>
            </div>
            <div>
              <div class="candidate-subline">量比 ${item.metrics.volumeRatio}</div>
              <div class="candidate-subline">上方压力 ${percent(item.metrics.overheadPressure)}</div>
              <div class="candidate-subline">筑底 ${item.metrics.baseDays} 天</div>
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

export function renderResultsTable(container, items) {
  container.innerHTML = items
    .map((item) => {
      const status = statusMeta(item);
      return `
        <tr>
          <td>${item.symbol}${item.previewMock ? "<br><small>preview</small>" : ""}</td>
          <td>${getScopeLabel(item.marketSegment)}</td>
          <td>${item.score.total}</td>
          <td>${item.metrics.volumeRatio}</td>
          <td>${percent(item.metrics.overheadPressure)}</td>
          <td>${item.metrics.baseDays}</td>
          <td><span class="pill ${status.className}">${status.label}</span></td>
        </tr>
      `;
    })
    .join("");
}
