export const fallbackPayload = {
  generated_at: "2026-04-22",
  strategy: {
    advice: [
      { title: "推荐市场", value: "先测主板", detail: "先把主板规则跑顺，再扩展到别的市场。" },
      { title: "上方压力", value: "4% - 6%", detail: "先用较稳的压力区间做第一轮验证。" },
      { title: "核心驱动", value: "筹码结构", detail: "先让一个主信号决定结果，再叠加其他过滤。" },
      { title: "量比门槛", value: ">= 1.8", detail: "突破型策略建议先看放量是否充分。" },
    ],
    parsed_rules: [
      { group: "系统判断", label: "当前为演示模式" },
      { group: "系统判断", label: "未读取你的实时自然语言约束" },
    ],
    parameters: [
      { label: "上方筹码压力", value: "4% - 6%", hint: "风险越保守，这个阈值越要收紧。" },
      { label: "放量标准", value: ">= 1.8", hint: "量比越高，突破确认通常越强。" },
      { label: "筑底时长", value: "60 - 120 天", hint: "底部整理不够，趋势持续性往往偏弱。" },
      { label: "估值要求", value: "不过热即可", hint: "第一版可以先不过度卡死估值条件。" },
    ],
    summary: "当前是稳定演示模式。后续接入更完整数据后，这里会自动切到真实扫描结果。",
  },
  results: {
    label: "主板",
    note: "当前是演示数据模式，用来保证网页流程稳定可用。",
    live_data: false,
    items: [
      {
        symbol: "600276.SH",
        market_segment: "main_board",
        trade_date: "2026-04-22",
        passed_filters: true,
        preview_mock: true,
        score: {
          total: 72.2,
          reasons: ["上方压力较小", "筑底时间充分", "量比已接近有效突破区间"],
        },
        failed_reasons: [],
        metrics: { volume_ratio: 2.06, overhead_pressure: 0.028, base_days: 102 },
      },
      {
        symbol: "600036.SH",
        market_segment: "main_board",
        trade_date: "2026-04-21",
        passed_filters: false,
        preview_mock: false,
        score: {
          total: 58.85,
          reasons: ["筹码相对集中", "筑底周期较完整"],
        },
        failed_reasons: ["放量确认不足", "突破信号还不够明确"],
        metrics: { volume_ratio: 0.8919, overhead_pressure: 0.0464, base_days: 120 },
      },
      {
        symbol: "600519.SH",
        market_segment: "main_board",
        trade_date: "2026-04-21",
        passed_filters: false,
        preview_mock: false,
        score: {
          total: 43.51,
          reasons: ["筹码结构尚可", "底部整理时间够长"],
        },
        failed_reasons: ["均线结构未完全转强", "量比仍然偏弱"],
        metrics: { volume_ratio: 0.6801, overhead_pressure: 0.0657, base_days: 120 },
      },
    ],
  },
  backtest: {
    hold_days: 15,
    stop_loss: "-7%",
    take_profit: "18%",
    max_positions: 10,
  },
};
