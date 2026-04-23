# A-Share Trend Screener

这是一个面向个人研究使用的 A 股选股与回测骨架，目标是把你的策略拆成确定性的量化规则，而不是让 AI 直接“拍脑袋选股”。

## 当前能力

- 将“筹码结构 + 技术信号 + 筑底阶段 + 估值/行业热度”量化成统一评分
- 提供硬过滤条件，避免只靠总分导致选股偏掉
- 提供基础回测引擎，用于验证历史表现
- 暴露 FastAPI 接口，方便后续接网页、小程序或 App
- 预留 `Tushare` / `AKShare` 接入口，先用规范化数据就能跑
- 内置 `CSVProvider`，先用样本数据就能验证筛选与回测

## 你最关心的 `overhead pressure`

这里默认定义为：

```text
overhead_pressure = max(cost_95pct - close, 0) / close
```

意思是：当前价格离 95% 成本线还有多远。越小，说明上方套牢筹码越轻。

默认经验阈值：

- `<= 3%`：非常干净，适合重点关注
- `3% ~ 6%`：可交易区间，属于默认通过标准
- `6% ~ 10%`：有明显压力，除非技术面非常强
- `> 10%`：默认淘汰

在本项目里，默认硬阈值写在 [strategy.example.toml](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/strategy.example.toml)：

- `max_overhead_pressure = 0.06`
- `excellent_overhead_pressure = 0.03`

## 推荐工作流

1. 每天盘后用日线数据跑一次全市场筛选
2. 得到候选池后，盘中只对候选池做分钟级确认
3. 对候选池跑回测，看历史胜率、盈亏比、持有期收益分布
4. AI 只负责解释“为什么这只票入选”，不负责替代量化规则

## 当前推荐方案

如果你准备先以较低成本推进，推荐先用 `Plan A`：

- 10 人以内小范围试用
- 盘后选股
- 日线回测
- 不做实时分钟

对应预设文件：

- [strategy.plan_a.toml](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/strategy.plan_a.toml)
- [Plan A 落地说明](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/docs/plan-a-rollout.md)

## 免费起步

如果你暂时还没买 `Tushare token`，可以先用 `AKShare Lite` 路线：

- 用 `AKShare` 拉日线和当日快照
- 先跑盘后筛选
- 先跑日线回测
- 筹码优先读取东方财富筹码接口；取不到时才用历史价格做近似替代
- 涨停/炸板优先读取东方财富涨停池和炸板池；取不到时才用涨跌幅粗略估算

对应代码：

- [analytics.py](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/src/ashare_strategy/analytics.py)
- [akshare_provider.py](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/src/ashare_strategy/providers/akshare_provider.py)

## 快速开始

安装依赖后运行 API：

```bash
uvicorn ashare_strategy.api:app --reload
```

运行内置单元测试：

```bash
python -m unittest discover -s tests -p "test_*.py"
```

运行 `AKShare Lite` 扫描：

```bash
python scripts/run_akshare_scan.py --symbols 000001,600519,300750,002594,601318 --all
```

检查免费数据源是否可用：

```bash
python scripts/check_akshare.py --symbol 000001
```

如果你想把结果保存成 JSON：

```bash
python scripts/run_akshare_scan.py --symbols 000001,600519,300750,002594,601318 --all --output outputs/scan.json
```

## MVP 启动

如果你想启动网页版 MVP：

1. 直接双击 [start_mvp_server.cmd](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/scripts/start_mvp_server.cmd)
2. 浏览器打开 `http://127.0.0.1:8000`

说明：

- 如果本地服务没有启动，前端也会自动回退到离线样本模式
- 如果本地服务启动成功，前端会优先请求 `/api/mvp/bootstrap` 和 `/api/mvp/strategy`

## 公网部署

当前版本已经可以推进到公网 MVP。

关键文件：

- [Dockerfile](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/Dockerfile)
- [render.yaml](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/render.yaml)
- [Procfile](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/Procfile)
- [DEPLOY.md](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/DEPLOY.md)

推荐先部署成：

- `AKShare + fallback` 的公网测试版

等 `Tushare token` 接入后，再把数据层升级成正式版。

## 下一步怎么接真实数据

### 方案 A：先快速验证

- 用 `Tushare` 拉 `daily_basic`、`cyq_perf`、`limit_list_d`
- 自己补足最近 250 日行情，算均线、斜率、平台突破、筑底指标
- 将数据整理成 `DailySnapshot` 结构后喂给筛选器
- 如果你暂时不想直接接 API，可以先把整理后的数据导出成 CSV，再用 `CSVProvider`

### 方案 B：先做私有稳定版

- 建一个每天增量更新的本地数据库
- 盘后跑全市场评分
- 盘中只刷新候选池分钟线
- FastAPI 只读你的本地库，不直接对外暴露第三方接口

## 文件结构

- [src/ashare_strategy/config.py](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/src/ashare_strategy/config.py)
- [src/ashare_strategy/models.py](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/src/ashare_strategy/models.py)
- [src/ashare_strategy/providers/csv_provider.py](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/src/ashare_strategy/providers/csv_provider.py)
- [src/ashare_strategy/strategy.py](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/src/ashare_strategy/strategy.py)
- [src/ashare_strategy/backtest.py](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/src/ashare_strategy/backtest.py)
- [src/ashare_strategy/api.py](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/src/ashare_strategy/api.py)
