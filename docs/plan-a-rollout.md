# Plan A 落地说明

这个版本对应的是：

- 10 人以内的小范围试用
- 盘后选股
- 日线回测
- 不做分钟级实时盯盘

## 目标

先验证三件事：

1. 你的策略能不能稳定筛出“像你会关注的票”
2. 这些票在历史回测里有没有统计优势
3. 这套流程能不能以较低成本稳定运行

## Plan A 的功能边界

这个阶段会做：

- 每日盘后拉取 A 股日线相关数据
- 计算筹码、趋势、底部整理、估值/行业热度评分
- 输出候选股票列表、总分、入选理由、淘汰原因
- 按固定规则跑日线回测

这个阶段不做：

- 实时分钟级监控
- 高频盘中策略
- 对外公开推荐
- 多租户复杂权限系统

## 数据要求

Plan A 优先使用 `Tushare` 的日线能力。

首批最关键的接口：

- `stock_basic`
- `daily`
- `daily_basic`
- `adj_factor`
- `moneyflow`
- `limit_list_d`

如果后续权限足够，再加：

- `cyq_perf`

说明：

- 如果 `cyq_perf` 暂时不可用，可以先用价格结构和量价平台替代部分筹码判断
- 这会让“上方筹码非常干净”的精度下降，但不影响先验证策略框架

## 免费过渡方案

如果 `Tushare token` 还没准备好，可以先走 `AKShare Lite`：

- 日线行情：`stock_zh_a_hist`
- 当日市场快照：`stock_zh_a_spot_em`
- 先不依赖分钟数据
- 筹码指标先用近 90 个交易日收盘分布近似

这个版本适合：

- 先验证策略有没有感觉
- 先做盘后候选股
- 先做日线回测

这个版本的限制：

- 不是严格的真实筹码分布
- 行业热度和行业估值先用中性值或后续补充
- 不适合直接当长期正式底座

## 成本预估

个人试用阶段，Plan A 的典型成本区间：

- 数据权限：约 `0 ~ 1000 元/年`
- 服务器：约 `0 ~ 300 元/月`
- 数据库存储：通常可忽略

如果只在你自己的电脑本地跑：

- 初期服务器成本可以接近 `0`

## 技术架构

推荐结构：

1. 定时拉取 `Tushare` 日线数据
2. 存入本地数据库或 CSV 缓存
3. 每日盘后运行筛选器
4. 写入候选结果和历史回测结果
5. 通过 API 或页面展示

## 当前代码对应位置

- 默认策略样例：[strategy.example.toml](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/strategy.example.toml)
- Plan A 预设：[strategy.plan_a.toml](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/strategy.plan_a.toml)
- 筛选引擎：[strategy.py](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/src/ashare_strategy/strategy.py)
- 回测引擎：[backtest.py](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/src/ashare_strategy/backtest.py)
- 数据模型：[models.py](/C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/src/ashare_strategy/models.py)

## 从现在到第一版真实结果的步骤

### 第一步

拿到你的 `Tushare token`

### 第二步

先接这些免费或低门槛可验证的数据：

- `stock_basic`
- `daily`

如果权限允许，再接：

- `daily_basic`
- `moneyflow`
- `limit_list_d`

### 第三步

落地一张统一日线表，至少包含：

- 股票代码
- 交易日
- 开高低收
- 成交量
- 估值字段
- 资金流字段
- 涨停/炸板标记

### 第四步

跑第一版盘后选股结果：

- 输出 Top N
- 输出每只票的分数和理由
- 输出哪些票被淘汰、为什么被淘汰

### 第五步

跑第一版历史回测：

- 胜率
- 平均收益
- 持有期收益分布
- 最大回撤

## 你接下来要给我的东西

为了把 Plan A 真正接上真实市场数据，我最需要的是：

- `Tushare token`

可选但很有帮助的信息：

- 你更偏好的买入规则
- 你更偏好的卖出规则
- 你想先回测哪一段时间

## 当前状态

截至现在：

- 策略核心已经写好
- 回测骨架已经写好
- Plan A 方案已经固化
- 已补上 `AKShare Lite` 免费起步能力
- 还没接入你的真实 `Tushare token`

所以项目当前属于：

- 架构完成
- 等待接入真实数据
