export const fallbackPayload = {
  generated_at: "2026-04-22",
  strategy: {
    advice: [
      {
        title: "建议市场",
        value: "主板优先",
        detail: "不同市场的波动和估值结构不同，阈值最好分开回测。",
      },
      {
        title: "建议阈值",
        value: "4% - 6%",
        detail: "把上方筹码压力收敛成明确区间，后面更容易优化。",
      },
      {
        title: "建议驱动",
        value: "筹码结构",
        detail: "建议保留一个主驱动信号，避免所有条件都变成平均主义。",
      },
    ],
    parameters: [
      {
        label: "上方筹码压力",
        value: "4% - 6%",
        hint: "风险偏好越保守，越建议把压力阈值收紧。",
      },
      {
        label: "放量门槛",
        value: ">= 1.8",
        hint: "突破型策略更适合提高量比要求。",
      },
      {
        label: "筑底时长",
        value: "60 - 120 天",
        hint: "持股越久，越需要更充分的底部整理。",
      },
      {
        label: "估值规则",
        value: "估值不过热即可",
        hint: "主板更适合强调估值，科创板更适合把估值作为辅助。",
      },
    ],
    summary:
      "当前展示的是离线后备样本，用来保证页面和交互流程始终可用。等你正式启动本地服务后，这里会自动切回真实接口结果。",
  },
  results: {
    label: "主板",
    note: "当前处于离线样本模式；正式启动本地服务后，这里会切成实时样本或回退样本接口。",
    live_data: false,
    items: [
      {
        symbol: "600036.SH",
        market_segment: "main_board",
        trade_date: "2026-04-21",
        passed_filters: false,
        preview_mock: false,
        score: {
          total: 58.85,
          reasons: ["Chip distribution is compact", "Base-building period is long enough"],
        },
        failed_reasons: ["missing breakout confirmation", "volume_ratio=0.89 below 1.50"],
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
          reasons: ["Chip distribution is compact", "Base-building period is long enough"],
        },
        failed_reasons: ["moving averages are not in bullish alignment", "volume_ratio=0.68 below 1.50"],
        metrics: { volume_ratio: 0.6801, overhead_pressure: 0.0657, base_days: 120 },
      },
      {
        symbol: "600276.SH",
        market_segment: "main_board",
        trade_date: "2026-04-22",
        passed_filters: true,
        preview_mock: true,
        score: {
          total: 72.2,
          reasons: ["Preview mock for main-board pass state", "Low overhead chip pressure"],
        },
        failed_reasons: [],
        metrics: { volume_ratio: 2.06, overhead_pressure: 0.028, base_days: 102 },
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
