# 策略绩效指标补齐

来源：冻结蓝图 §38；限定既有单标的、只做多或持现金回测。
不开发券商执行、不把模拟收益称作真实收益或预测准确率。

- 保留总收益、最大回撤、每bar波动率、成交笔数、佣金。
- 增加完成买卖往返数、胜率、profit factor、平均盈利/亏损（账户币种金额）。
  仅已平仓参与；盈亏包含持仓期间分红、拆股影响、佣金和滑点；未平仓不冒充胜利。
  平手计入胜率分母；没有完成往返或没有亏损时对应比率为null，不输出无穷大。
- gross turnover=双向原始价格成交额之和/平均NAV；slippage为
  sum(abs(execution_price-raw_price)*shares)；transaction_cost=佣金+slippage。
  成本已在NAV中体现，统计不能再扣一次。
- exposure=各bar的持仓市值/NAV均值；time_in_market=持仓bar比例。
- CAGR用实际首末时间跨度按365.25天年化；零/非法跨度或溢出为null。
  Sharpe/Sortino只在显式periods_per_year和risk_free_annual_return策略配置下输出，
  risk_free换算成每期复利；Sharpe使用超额收益样本标准差，Sortino使用
  全部期数上的负超额平方均值平方根。零方差/零下行风险/样本不足为null。
  配置与不可用原因写入结果，不默认宣称日线频率或无风险利率为事实。
- 基准可选，必须提供标识、来源版本、完整质量金例及逐bar对齐的总收益净值序列，
  available_at不晚于对应bar的available_at。无基准则excess=null；拒绝不合格、
  来源不匹配、时间不齐或迟到的基准。超额为策略总收益-基准总收益（算术差）。
- 回测继续执行已有历史证券池、公司行动、价格单位和PIT资格检查。

限定统计定义由本仓库版本固定。Sharpe的频率转换参考
[Morningstar methodology](https://admainnew.morningstar.com/directhelp/Glossary/Risk_and_Rating/Sharpe_Ratio.htm)。
完成的是计算与边界回归；真实策略资格仍依赖完整历史合格来源。
