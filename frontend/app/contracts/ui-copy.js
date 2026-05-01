export const scopeLabels = {
  all: "全市场",
  main_board: "主板",
  star_market: "科创板",
  growth_board: "成长板",
};

export const styleLabels = {
  breakout: "平台突破",
  trend_start: "趋势启动",
  rebound: "底部反转",
};

export const holdingLabels = {
  swing: "波段",
  short: "短线",
  trend: "趋势",
};

export const priorityLabels = {
  chip: "筹码结构",
  volume: "放量突破",
  base: "筑底时长",
  valuation: "估值修复",
};

export const pageCopy = {
  liveData: "实时数据",
  demoData: "演示数据",
  loading: "生成中",
  waitingPlaybook: "等待选择",
  selectedPlaybook: "已选方案",
  defaultPlaybookHeadline: "系统会先把你的想法拆成几套可量化方案，再由你挑一套继续跑结果。",
};

export function getScopeLabel(scope) {
  return scopeLabels[scope] || scope;
}
