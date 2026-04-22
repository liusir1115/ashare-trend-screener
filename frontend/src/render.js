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
          <span class="card-label">${item.title}</span>
          <strong class="card-value">${item.value}</strong>
          <p class="card-detail">${item.detail}</p>
        </article>
      `,
    )
    .join("");
}

export function renderParsedRules(container, rules) {
  const groups = new Map();
  (rules || []).forEach((rule) => {
    const group = typeof rule === "string" ? "系统判断" : rule.group || "系统判断";
    const label = typeof rule === "string" ? rule : rule.label;
    if (!groups.has(group)) {
      groups.set(group, []);
    }
    groups.get(group).push(label);
  });

  container.innerHTML = [...groups.entries()]
    .map(
      ([group, items]) => `
        <div class="parsed-group">
          <div class="parsed-group-title">${group}</div>
          <div class="parsed-group-list">
            ${items.map((item) => `<span class="parsed-pill">${item}</span>`).join("")}
          </div>
        </div>
      `,
    )
    .join("");
}

export function renderParameters(container, items) {
  container.innerHTML = items
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

export function renderSummaryText(container, text) {
  container.textContent = text;
}

export function renderTopMeta(generatedAtEl, scopeStatusEl, generatedAt, text = "已生成") {
  generatedAtEl.textContent = generatedAt || "--";
  scopeStatusEl.textContent = text;
}

export function renderScope(scopeLabelEl, scopeNoteEl, scope, note) {
  scopeLabelEl.textContent = getScopeLabel(scope);
  scopeNoteEl.textContent = note;
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
      <span class="metric-label">最大持仓</span>
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
      title: "样本数",
      value: String(items.length),
      detail: "本次结果里参与展示的股票数量",
    },
    {
      title: "通过数",
      value: String(passed),
      detail: "完全满足当前硬过滤条件",
    },
    {
      title: "观察数",
      value: String(watch),
      detail: "接近通过，适合继续跟踪",
    },
    {
      title: "最高分",
      value: top ? `${top.score.total}` : "--",
      detail: top ? `${top.symbol}` : "暂无结果",
    },
  ];

  container.innerHTML = cards
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

export function renderCandidates(container, items) {
  const passed = items.filter((item) => item.passedFilters).slice(0, 3);
  const watch = items.filter((item) => !item.passedFilters && item.score.total >= 55).slice(0, 3);
  const blocked = items.filter((item) => !item.passedFilters && item.score.total < 55).slice(0, 3);

  const sections = [
    { title: "通过", className: "bucket-pass", items: passed, empty: "当前没有完全通过的股票" },
    { title: "观察", className: "bucket-watch", items: watch, empty: "当前没有接近通过的股票" },
    { title: "淘汰", className: "bucket-blocked", items: blocked, empty: "当前没有明显淘汰样本" },
  ];

  container.innerHTML = sections
    .map((section) => {
      const cards = section.items.length
        ? section.items
            .map((item) => {
              const status = statusMeta(item);
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
                      <span>上方压力 ${percent(item.metrics.overheadPressure)}</span>
                      <span>筑底 ${item.metrics.baseDays} 天</span>
                    </div>
                  </div>
                </article>
              `;
            })
            .join("")
        : `<div class="candidate-empty">${section.empty}</div>`;

      return `
        <section class="candidate-section ${section.className}">
          <div class="candidate-section-head">
            <h3>${section.title}</h3>
            <span class="candidate-count">${section.items.length}</span>
          </div>
          <div class="candidate-section-list">
            ${cards}
          </div>
        </section>
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
          <td>${item.symbol}</td>
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
