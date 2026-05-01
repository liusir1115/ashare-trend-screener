export function renderMarketReview(elements, marketReview) {
  const review = marketReview || {};
  elements.marketReviewStatus.textContent = getMarketReviewStatus(review);
  elements.marketReviewHeadline.textContent = review.headline || "暂时没有资金流摘要。";
  elements.topInflowList.innerHTML = buildFlowList(review.top_inflow || []);
  elements.topOutflowList.innerHTML = buildFlowList(review.top_outflow || []);
  elements.rotationSummary.textContent = review.rotation?.summary || "暂时没有高切低判断。";
  elements.rotationTags.innerHTML = buildRotationTags(review.rotation || {});
  renderNewsReview(elements, review.news || {});
}

export function renderQuestionAnswer(elements, payload) {
  elements.qaMode.textContent = payload.mode || "规则问答";
  elements.qaAnswer.textContent = payload.answer || "暂时没有回答。";
  elements.qaSuggestions.innerHTML = (payload.suggestions || []).map((item) => `<button type="button" class="flow-tag qa-suggestion" data-question="${item}">${item}</button>`).join("");
}

export function renderSourceStatus(elements, sourceStatus) {
  const status = sourceStatus || {};
  elements.sourceStatusHeadline.textContent = status.headline || "这里会显示本次结果到底用了真实数据还是演示兜底。";
  elements.sourceStatusGrid.innerHTML = (status.items || []).map((item) => `<article class="source-status-item ${item.ok ? "source-ok" : "source-warn"}"><div class="source-status-head"><strong>${item.name}</strong><span>${item.state}</span></div><p>${item.detail}</p></article>`).join("");
  elements.sourceTips.innerHTML = (status.tips || []).map((item) => `<span>${item}</span>`).join("");
}

function buildFlowList(items) {
  if (!items.length) return '<div class="flow-empty">暂无数据</div>';
  return items.map((item) => `<div class="flow-item"><div><strong>${item.name}</strong><span>${item.source || ""}</span></div><div class="flow-number ${item.net_inflow >= 0 ? "flow-in" : "flow-out"}">${item.net_inflow_text}</div></div>`).join("");
}

function buildRotationTags(rotation) {
  const lowLevelItems = rotation.low_level_inflow || [];
  const highLevelItems = rotation.high_level_outflow || [];
  const tags = [...lowLevelItems.map((item) => `低位承接：${item.name}`), ...highLevelItems.map((item) => `高位流出：${item.name}`)];
  if (!tags.length) return '<span class="flow-tag">暂未形成明显切换</span>';
  return tags.map((tag) => `<span class="flow-tag">${tag}</span>`).join("");
}

function renderNewsReview(elements, newsReview) {
  elements.newsHeadline.textContent = newsReview.headline || "暂时没有热点摘要。";
  elements.newsTags.innerHTML = (newsReview.hot_tags || []).map((item) => `<span class="flow-tag">${item.name} ${item.count}</span>`).join("");
  elements.newsList.innerHTML = buildNewsList(newsReview.items || [], newsReview.risks || []);
  elements.newsCandidateNote.textContent = newsReview.candidate_note || "";
  elements.newsCandidateLinks.innerHTML = buildNewsCandidateLinks(newsReview.candidate_links || []);
}

function buildNewsList(newsItems, riskItems) {
  const combined = [...riskItems.map((item) => ({ ...item, isRisk: true })), ...newsItems.slice(0, 5).map((item) => ({ ...item, isRisk: false }))].slice(0, 7);
  if (!combined.length) return '<div class="flow-empty">暂无快讯</div>';
  return combined.map((item) => `<div class="news-item ${item.isRisk ? "news-risk" : ""}"><span>${item.tag || "综合"}</span><p>${item.title}</p></div>`).join("");
}

function buildNewsCandidateLinks(items) {
  if (!items.length) return '<div class="flow-empty">当前还没有特别贴近热点的候选股。</div>';
  return items.map((item) => `<article class="news-candidate-item"><div class="news-candidate-head"><strong>${item.symbol}</strong><span>${item.status}</span></div><p>${item.note}</p></article>`).join("");
}

function getMarketReviewStatus(review) {
  if (review.flow_live_data && review.news_live_data) return "真实复盘";
  if (review.news_live_data) return "新闻真实";
  if (review.flow_live_data) return "资金流真实";
  return "演示复盘";
}
