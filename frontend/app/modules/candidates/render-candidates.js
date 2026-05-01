import { getScopeLabel } from "../../contracts/ui-copy.js";
import { formatPercent, formatText, getCandidateStatus } from "../../utils/render-formatters.js";

export function renderCandidates(container, resultItems) {
  const sections = [
    { title: "通过", className: "bucket-pass", items: resultItems.filter((item) => item.passedFilters).slice(0, 3), emptyText: "当前没有完全通过的股票。" },
    { title: "观察", className: "bucket-watch", items: resultItems.filter((item) => !item.passedFilters && item.score.total >= 55).slice(0, 3), emptyText: "当前没有接近通过的股票。" },
    { title: "淘汰", className: "bucket-blocked", items: resultItems.filter((item) => !item.passedFilters && item.score.total < 55).slice(0, 3), emptyText: "当前没有明显需要淘汰的样本。" },
  ];
  container.innerHTML = sections.map(buildCandidateSection).join("");
}

function buildCandidateSection(section) {
  const cardsHtml = section.items.length ? section.items.map(buildCandidateCard).join("") : `<div class="candidate-empty">${section.emptyText}</div>`;
  return `<section class="candidate-section ${section.className}"><div class="candidate-section-head"><h3>${section.title}</h3><span class="candidate-count">${section.items.length}</span></div><div class="candidate-section-list">${cardsHtml}</div></section>`;
}

function buildCandidateCard(item) {
  const status = getCandidateStatus(item);
  const reasons = item.passedFilters ? item.score.reasons : item.failedReasons;
  const metrics = item.metrics;
  return `<article class="candidate-card"><div class="candidate-main"><div class="candidate-head"><h3>${item.symbol}</h3><span class="pill ${status.className}">${status.label}</span></div><div class="candidate-sub">${getScopeLabel(item.marketSegment)} / ${item.tradeDate}</div><ul class="reasons">${reasons.slice(0, 3).map((reason) => `<li>${reason}</li>`).join("")}</ul></div><div class="candidate-side"><div class="candidate-score">${item.score.total}</div><div class="candidate-metrics"><span>量比 ${metrics.volumeRatio}</span><span>上方压力 ${formatPercent(metrics.overheadPressure)}</span><span>获利盘 ${formatPercent(metrics.winnerRate)}</span><span>筑底 ${metrics.baseDays} 天</span></div><div class="candidate-detail-grid"><span>筹码：${formatText(metrics.chipSourceLabel)}</span><span>90成本：${formatText(metrics.cost5pct)} - ${formatText(metrics.cost95pct)}</span><span>涨停：${formatLimitStatus(metrics)}</span><span>封板：${formatLimitTimes(metrics)}</span></div></div></article>`;
}

function formatLimitStatus(metrics) {
  if (metrics.brokenLimit) return "炸板";
  if (metrics.relimit) return `回封 ${metrics.limitOpenTimes || 0} 次`;
  if (metrics.limitUp) return "涨停";
  return "否";
}

function formatLimitTimes(metrics) {
  if (!metrics.firstLimitTime && !metrics.lastLimitTime) return "--";
  return `${formatText(metrics.firstLimitTime)} / ${formatText(metrics.lastLimitTime)}`;
}

export function renderResultsTable(container, resultItems) {
  container.innerHTML = resultItems.map((item) => {
    const status = getCandidateStatus(item);
    return `<tr><td>${item.symbol}</td><td>${getScopeLabel(item.marketSegment)}</td><td>${item.score.total}</td><td>${item.metrics.volumeRatio}</td><td>${formatPercent(item.metrics.overheadPressure)}</td><td>${formatPercent(item.metrics.winnerRate)}</td><td>${formatLimitStatus(item.metrics)}</td><td>${item.metrics.baseDays}</td><td><span class="pill ${status.className}">${status.label}</span></td></tr>`;
  }).join("");
}
