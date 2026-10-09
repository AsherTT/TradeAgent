"use client";

import { useState, type KeyboardEvent } from "react";
import { ArrowUpRight, BookOpen, Check, FileText, Layers3 } from "lucide-react";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";

const tabs = ["portal", "financials", "report", "evidence"] as const;
type DemoTab = (typeof tabs)[number];
const annual = {
  "2023": {
    revenue: "80.0",
    income: "9.6",
    cash: "18.0",
    revenueWidth: "w-[67%]",
    incomeWidth: "w-[40%]",
    cashWidth: "w-[60%]",
  },
  "2024": {
    revenue: "96.0",
    income: "13.4",
    cash: "22.0",
    revenueWidth: "w-[80%]",
    incomeWidth: "w-[56%]",
    cashWidth: "w-[73%]",
  },
};

export function DemoPanel({ appearance = "integration" }: { appearance?: "integration" | "source-frame" }) {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  const [tab, setTab] = useState<DemoTab>("portal");
  const [period, setPeriod] = useState<keyof typeof annual>("2024");
  const [showQuote, setShowQuote] = useState(false);
  const labels = zh
    ? ["门户", "财务", "报告", "证据"]
    : ["Portal", "Financials", "Report", "Evidence"];
  const excerpt = zh
    ? "本年度收入为96.0百万示例币，其中订阅服务收入为64.0百万示例币。收入数字用于演示界面操作，不代表任何真实公司。"
    : "Annual revenue was 96.0 million demo units, including 64.0 million from subscriptions. These figures demonstrate the interface and do not represent a real company.";
  function changeTab(next: DemoTab) {
    setTab(next);
    setShowQuote(false);
  }
  function navigateTabs(
    event: KeyboardEvent<HTMLButtonElement>,
    index: number,
  ) {
    const next =
      event.key === "ArrowRight"
        ? (index + 1) % tabs.length
        : event.key === "ArrowLeft"
          ? (index + tabs.length - 1) % tabs.length
          : event.key === "Home"
            ? 0
            : event.key === "End"
              ? tabs.length - 1
              : null;
    if (next === null) return;
    event.preventDefault();
    changeTab(tabs[next]);
    document.getElementById(`demo-tab-${tabs[next]}`)?.focus();
  }
  return (
    <section
      aria-label={zh ? "可交互产品演示" : "Interactive product demonstration"}
      className={`overflow-hidden bg-[var(--demo-surface)] text-[var(--demo-ink)] ${appearance === "source-frame" ? "[font-family:var(--ui)] [--demo-line:#394351] [--demo-surface:#191f27] [--demo-line-soft:#2d3643] [--demo-badge:#293b4b] [--demo-badge-ink:#9dd5fc] [--demo-accent:#41b6ff] [--demo-accent-ink:#9dd5fc] [--demo-muted:#a2adbc] [--demo-ink:#f5f7fb] [--demo-raised:#252d38] [--demo-raised-hover:#2d3744] [--demo-selected:#315474] [--demo-track:#252d38] [--demo-chart:#41b6ff] [--demo-quote:#252d38]" : "rounded-2xl border border-[var(--demo-line)] shadow-[0_24px_64px_#3a322612] [--demo-line:#d9d5bf] [--demo-surface:#fffdf8] [--demo-line-soft:#e7e2d5] [--demo-badge:#fff0ca] [--demo-badge-ink:#77531e] [--demo-accent:#986e2e] [--demo-accent-ink:#855d21] [--demo-muted:#777065] [--demo-ink:#191816] [--demo-raised:#f1eee5] [--demo-raised-hover:#f8f5ed] [--demo-selected:#fdcc6a] [--demo-track:#edebe1] [--demo-line-soft:#ece8dd] [--demo-chart:#d9b97a] [--demo-quote:#faf6e9]"}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--demo-line-soft)] px-5 py-4">
        <span className="flex items-center gap-2 text-sm font-semibold">
          <Layers3 size={16} aria-hidden="true" />
          TradeAgent
        </span>
        <span className="rounded-full bg-[var(--demo-badge)] px-3 py-1 text-[11px] font-medium text-[var(--demo-badge-ink)]">
          {zh ? "演示数据 · 本地交互" : "Demo data · local interactions"}
        </span>
      </div>
      <div
        role="tablist"
        aria-label={zh ? "演示页面" : "Demo pages"}
        className="grid grid-cols-4 border-b border-[var(--demo-line-soft)] px-3 pt-2"
      >
        {tabs.map((item, index) => (
          <button
            key={item}
            id={`demo-tab-${item}`}
            role="tab"
            aria-selected={tab === item}
            aria-controls="demo-content"
            tabIndex={tab === item ? 0 : -1}
            onKeyDown={(event) => navigateTabs(event, index)}
            onClick={() => changeTab(item)}
            className={`cursor-pointer border-b-2 px-1 py-3 text-[13px] font-medium ${tab === item ? "border-[var(--demo-accent)] text-[var(--demo-accent-ink)]" : "border-transparent text-[var(--demo-muted)] hover:text-[var(--demo-ink)]"}`}
          >
            {labels[index]}
          </button>
        ))}
      </div>
      <div
        role="tabpanel"
        id="demo-content"
        aria-labelledby={`demo-tab-${tab}`}
        tabIndex={0}
        className="min-h-[320px] p-5 md:min-h-[350px] md:p-6"
      >
        {tab === "portal" && (
          <>
            <p className="mb-1 text-xs text-[var(--demo-muted)]">
              {zh ? "我的研究空间" : "My research space"}
            </p>
            <h2 className="mb-5 text-xl font-semibold">
              {zh
                ? "把公司、问题与证据放在一起"
                : "Companies, questions, evidence"}
            </h2>
            <div className="mb-5 grid grid-cols-3 gap-2">
              {[
                [zh ? "关注公司" : "Following", "3"],
                [zh ? "研究记录" : "Research", "2"],
                [zh ? "活动任务" : "Active", "1"],
              ].map(([label, value]) => (
                <div key={label} className="rounded-lg bg-[var(--demo-raised)] p-3">
                  <p className="mb-2 text-[11px] text-[var(--demo-muted)]">{label}</p>
                  <p className="text-2xl">{value}</p>
                </div>
              ))}
            </div>
            <button
              onClick={() => changeTab("financials")}
              className="flex w-full cursor-pointer items-center justify-between rounded-xl border border-[var(--demo-line-soft)] p-4 text-left hover:bg-[var(--demo-raised-hover)]"
            >
              <span>
                <span className="block text-sm font-semibold">
                  DEMO · {zh ? "示例科技" : "Example Technology"}
                </span>
                <span className="mt-1 block text-xs text-[var(--demo-muted)]">
                  {zh
                    ? "打开财务演示，切换年度"
                    : "Open financial demo and change the year"}
                </span>
              </span>
              <ArrowUpRight size={18} aria-hidden="true" />
            </button>
            <p className="mt-4 flex items-center gap-2 text-xs text-[var(--demo-muted)]">
              <Check size={14} aria-hidden="true" />
              {zh
                ? "示例任务：等待采集材料"
                : "Sample task: awaiting collection"}
            </p>
          </>
        )}
        {tab === "financials" && (
          <>
            <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold">
                  {zh ? "年度财务" : "Annual financials"}
                </h2>
                <p className="mt-1 text-xs text-[var(--demo-muted)]">
                  {zh
                    ? "示例科技 · 单位：百万示例币"
                    : "Example Technology · million demo units"}
                </p>
              </div>
              <div
                role="group"
                aria-label={zh ? "演示年度" : "Demo year"}
                className="flex rounded-md border border-[var(--demo-line)] p-1"
              >
                {(["2023", "2024"] as const).map((year) => (
                  <button
                    key={year}
                    aria-pressed={period === year}
                    onClick={() => setPeriod(year)}
                    className={`cursor-pointer rounded px-3 py-1.5 text-xs ${period === year ? "bg-[var(--demo-selected)]" : "hover:bg-[var(--demo-track)]"}`}
                  >
                    {year}
                  </button>
                ))}
              </div>
            </div>
            <table className="w-full text-sm">
              <caption className="sr-only">
                {zh ? `${period}年演示财务` : `${period} demo financials`}
              </caption>
              <thead>
                <tr className="border-b border-[var(--demo-line)] text-xs text-[var(--demo-muted)]">
                  <th scope="col" className="pb-3 text-left font-normal">
                    {zh ? "指标" : "Metric"}
                  </th>
                  <th scope="col" className="pb-3 text-right font-normal">
                    {period}
                  </th>
                </tr>
              </thead>
              <tbody>
                {[
                  [
                    zh ? "收入" : "Revenue",
                    annual[period].revenue,
                    annual[period].revenueWidth,
                  ],
                  [
                    zh ? "净利润" : "Net income",
                    annual[period].income,
                    annual[period].incomeWidth,
                  ],
                  [
                    zh ? "现金" : "Cash",
                    annual[period].cash,
                    annual[period].cashWidth,
                  ],
                ].map(([name, value, width]) => (
                  <tr key={name} className="border-b border-[var(--demo-line-soft)]">
                    <th scope="row" className="py-3 pr-5 text-left font-normal">
                      <span className="mb-2 block">{name}</span>
                      <span
                        aria-hidden="true"
                        className="block h-1.5 rounded bg-[var(--demo-track)]"
                      >
                        <span
                          className={`block h-full rounded bg-[var(--demo-chart)] ${width}`}
                        />
                      </span>
                    </th>
                    <td className="py-3 text-right font-mono">{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-4 text-[11px] leading-5 text-[var(--demo-muted)]">
              {zh
                ? "年度选择会切换示例记录；真实多期财务仍在开发。"
                : "Year selection changes demo records; real multi-period financials are in development."}
            </p>
          </>
        )}
        {tab === "report" && (
          <>
            <div className="mb-4 flex items-center gap-2 text-xs text-[var(--demo-muted)]">
              <FileText size={15} aria-hidden="true" />
              {zh ? "示例报告 · 部分结果" : "Sample report · partial result"}
            </div>
            <h2 className="mb-3 text-xl font-semibold">
              {zh
                ? "每条结论，都能回到材料"
                : "Follow a finding back to its source"}
            </h2>
            <p className="text-sm leading-7">
              {zh
                ? "示例科技在2024年报告收入96.0百万示例币。"
                : "Example Technology reported 96.0 million demo units in revenue for 2024."}{" "}
              <button
                className="cursor-pointer rounded bg-[var(--demo-badge)] px-2 text-[var(--demo-accent-ink)]"
                onClick={() => setShowQuote(true)}
                aria-label={
                  zh
                    ? "查看引用1的示例片段"
                    : "Open demo excerpt for citation 1"
                }
              >
                [1]
              </button>
            </p>
            <p className="mt-3 text-xs leading-6 text-[var(--demo-muted)]">
              {zh
                ? "该片段不构成完整研究，也不能据此冻结预测。"
                : "This excerpt is not complete research and cannot qualify a frozen forecast."}
            </p>
            {showQuote && (
              <aside
                className="mt-4 rounded-xl border border-[var(--demo-chart)] bg-[var(--demo-quote)] p-4"
                aria-label={zh ? "引用对应片段" : "Cited excerpt"}
              >
                <p className="mb-2 text-xs font-semibold">
                  {zh
                    ? "示例年度材料 · 保存片段 [1]"
                    : "Sample annual material · saved excerpt [1]"}
                </p>
                <blockquote className="text-xs leading-6">{excerpt}</blockquote>
                <button
                  className="mt-2 cursor-pointer text-xs underline"
                  onClick={() => setShowQuote(false)}
                >
                  {zh ? "收起片段" : "Close excerpt"}
                </button>
              </aside>
            )}
            {!showQuote && (
              <button
                onClick={() => setShowQuote(true)}
                className="mt-6 flex cursor-pointer items-center gap-2 text-sm text-[var(--demo-accent-ink)]"
              >
                <BookOpen size={16} aria-hidden="true" />
                {zh ? "查看引用材料" : "Read cited material"} →
              </button>
            )}
          </>
        )}
        {tab === "evidence" && (
          <>
            <p className="mb-2 text-xs text-[var(--demo-muted)]">
              {zh ? "来源与原文核验" : "Source verification"}
            </p>
            <h2 className="mb-4 text-xl font-semibold">
              {zh ? "保存的内容，明确的范围" : "Saved content, explicit scope"}
            </h2>
            <div className="rounded-xl border border-[var(--demo-line)] bg-[var(--demo-raised-hover)] p-4">
              <p className="mb-3 text-xs font-semibold">
                {zh
                  ? "示例年度材料 · 片段 1"
                  : "Sample annual material · excerpt 1"}
              </p>
              <blockquote className="text-sm leading-7">{excerpt}</blockquote>
            </div>
            <p className="mt-4 text-xs leading-6 text-[var(--demo-muted)]">
              {zh
                ? "这是本地保存的虚构示例文本，没有对应外部全文。真实原文读取与定位将在后续阶段接入。"
                : "This is saved, fictional demo text with no external full document. Authorized source reading and location will follow in a later increment."}
            </p>
          </>
        )}
      </div>
    </section>
  );
}
