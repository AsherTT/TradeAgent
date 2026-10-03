# V1 技术指标补齐（P10 前）

来源：冻结蓝图 §20；用户要求修复 P10 前业务缺口。保持证券身份、PIT、
价格口径及 ACCEPTABLE 质量门槛。只是补齐计算能力，不授予真实行情资格。

新 feature_version=v1-technical-v2。既有快照不回写。确定以下可复验口径：

- SMA 5/10/20/50；EMA20 用首个收盘价初始化、alpha=2/21，20 根后才输出。
- RSI14 用前14个涨跌初始化均值，之后 Wilder 递推；零涨跌=50，只涨=100。
- MACD 为 EMA12-EMA26；EMA均首价初始化，26根后输出；signal为有效MACD的
  EMA9，9个有效值后输出；histogram=MACD-signal。
- ATR14：首根TR=high-low，其余TR=max(high-low,abs(high-prev_close),
  abs(low-prev_close))；前14根均值初始化，之后 Wilder 递推。
- MAVOL5/10 含当前bar；volume_ratio_5=当前量/前5根平均量，零分母=null。
- distance_to_sma_20=close/SMA20-1（小数比例）。
- historical_volatility_20=20个单期简单收益的样本标准差，不年化。
  realized_volatility_20 只在调用者明确提供 periods_per_year 时乘其平方根；
  默认null，避免把不明周期强行按252年化；该参数记录在元数据。
- trend_regime：close>SMA20>SMA50为uptrend，严格反向为downtrend，其余range；
  少于50根为null。保留20根线性趋势斜率。
- support_20/resistance_20 为前20根（排除当前）最低low/最高high，明确是历史
  区间代理，不是确认支撑阻力或交易建议；少于21根为null。
- 时间必须带时区；按 timestamp/available_at/observed_at 截止过滤，拒绝
  不同证券/重复时刻/混合口径/RAW/低质量/非有限或非法OHLCV。

独立金例覆盖初始化、递推、涨跌/横盘、缺窗口、零量、年化显式配置及未来过滤；
拆股/反拆股/分红沿用已有规范化金例并复验。不得以这些测试声称真实策略盈利。

基础指标定义参照 [Fidelity ATR](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/atr)
和 [Fidelity MACD](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/macd)。
初始化、窗口、量比、趋势/区间代理是本仓库明确选定的版本口径。
