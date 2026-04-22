export function getCandidateStatus(item) {
  if (item.passedFilters) {
    return { label: "通过", className: "pill-pass" };
  }

  if ((item.score?.total || 0) >= 55) {
    return { label: "观察", className: "pill-watch" };
  }

  return { label: "淘汰", className: "pill-blocked" };
}

export function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
}
