"use client";

import Link from "next/link";
import {
  ArrowUpRight,
  BookOpen,
  ChartNoAxesCombined,
  Fingerprint,
  Layers3,
} from "lucide-react";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import { DemoPanel } from "./DemoPanel";
import { ProductHeader } from "./ProductHeader";

export function ProductHome() {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  const modules = [
    {
      id: "portal",
      icon: Layers3,
      number: "01",
      title: zh
        ? "从关注公司，进入研究"
        : "From followed companies to research",
      description: zh
        ? "在自己的空间里组织公司、查看活动任务和已保存研究。每个入口都指向你的公司或研究记录。"
        : "Organize companies, active tasks and saved research in your own workspace. Every entry leads to your company or research record.",
      status: zh
        ? "账户与研究入口已接通"
        : "Account & research entries connected",
      link: "/app",
      label: zh ? "打开研究门户" : "Open research portal",
    },
    {
      id: "financials",
      icon: ChartNoAxesCombined,
      number: "02",
      title: zh
        ? "看财务，也看数据从哪里来"
        : "Read the numbers and their sources",
      description: zh
        ? "已有年度事实与部分指标。多期表格、趋势、分部与KPI将逐项补齐，期间、单位、来源与缺项始终明确。"
        : "Annual facts and limited metrics exist. Multi-period tables, trends, segments and KPIs will follow, with explicit periods, units, sources and gaps.",
      status: zh ? "多期财务开发中" : "Multi-period financials in development",
      link: "#demo",
      label: zh ? "查看财务演示" : "Try the financial demo",
    },
    {
      id: "reading",
      icon: BookOpen,
      number: "03",
      title: zh ? "从报告，回到原始证据" : "From a report back to evidence",
      description: zh
        ? "研究报告已支持基础章节、引用和来源信息。保存片段、原文定位与并排核验会在后续阶段接入。"
        : "Research reports have basic sections, citations and source metadata. Saved excerpts, source location and side-by-side verification are the next steps.",
      status: zh
        ? "基础报告可读 · 原文核验开发中"
        : "Basic reports available · source reading in development",
      link: "/app/research",
      label: zh ? "查看我的研究" : "View my research",
    },
  ];
  return (
    <div className="min-h-screen bg-[#edebe1] text-[#191816] [font-family:var(--font-geist-sans),'Microsoft_YaHei',sans-serif] [&_:focus-visible]:outline-2 [&_:focus-visible]:outline-[#986e2e] [&_:focus-visible]:outline-offset-4">
      <a
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-[#fdcc6a] focus:p-3"
        href="#main"
      >
        {zh ? "跳到正文" : "Skip to content"}
      </a>
      <ProductHeader />
      <main id="main">
        <section className="mx-auto grid max-w-[1360px] items-center gap-12 px-5 pt-12 pb-16 md:px-10 md:pt-20 md:pb-24 lg:grid-cols-[1fr_1.05fr] lg:gap-16">
          <div>
            <p className="mb-5 flex items-center gap-2 text-xs tracking-[1.2px] text-[#986e2e]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#986e2e]" />
              {zh ? "你的公司研究空间" : "YOUR COMPANY RESEARCH SPACE"}
            </p>
            <h1 className="max-w-[560px] text-[36px] leading-[1.2] font-normal tracking-[-1.4px] md:text-[52px] md:leading-[1.1]">
              {zh ? "把问题交给研究，" : "Build your research."}
              <br />
              <span className="text-[#986e2e]">
                {zh ? "把结论交给证据。" : "Ground it in evidence."}
              </span>
            </h1>
            <p className="mt-6 max-w-[500px] text-base leading-7 text-[#5e594f] md:text-lg md:leading-8">
              {zh
                ? "关注公司、发起有边界的研究、阅读报告与来源。把财务、材料和论点连接起来，知道结论来自哪里，也知道还缺什么。"
                : "Follow companies, run bounded research and read reports with their sources. Connect financials, material and theses, with clear provenance and visible gaps."}
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/app"
                className="rounded-md bg-[#fdcc6a] px-6 py-3.5 text-sm font-medium hover:bg-[#f6be52]"
              >
                {zh ? "开始研究" : "Start researching"} →
              </Link>
              <a
                href="#demo"
                className="rounded-md border border-[#191816] px-6 py-3.5 text-sm font-medium hover:bg-[#e2ded1]"
              >
                {zh ? "探索产品演示" : "Explore the demo"}
              </a>
            </div>
            <p className="mt-4 text-xs leading-5 text-[#777065]">
              {zh
                ? "自有账户 · 本人研究 · 明确的数据与预算边界"
                : "Your account · your research · explicit data and budget boundaries"}
            </p>
          </div>
          <div id="demo" className="scroll-mt-6">
            <DemoPanel />
          </div>
        </section>
        <section className="border-y border-[#d9d5bf] bg-[#e7e3d7]">
          <div className="mx-auto flex max-w-[1360px] flex-wrap items-center justify-between gap-6 px-5 py-6 text-sm md:px-10">
            <p className="max-w-xl leading-6">
              {zh
                ? "研究可以是部分结果，证据缺口必须看得见。"
                : "Research can be partial. Evidence gaps should always be visible."}
            </p>
            <span className="flex items-center gap-2 text-xs text-[#777065]">
              <Fingerprint size={16} aria-hidden="true" />
              {zh
                ? "账户归属、来源、时间与质量始终保留"
                : "Ownership, provenance, timing and quality stay explicit"}
            </span>
          </div>
        </section>
        <section className="mx-auto max-w-[1360px] px-5 py-16 md:px-10 md:py-24">
          <p className="mb-3 text-xs tracking-widest text-[#986e2e]">
            {zh
              ? "一个研究平台，三种工作方式"
              : "ONE PLATFORM, THREE WAYS TO WORK"}
          </p>
          <h2 className="mb-10 max-w-2xl text-3xl leading-tight font-normal md:text-[40px]">
            {zh
              ? "从公司概览，到可核验的结论。"
              : "From company context to verifiable findings."}
          </h2>
          <div className="grid gap-5 lg:grid-cols-3">
            {modules.map((module) => (
              <article
                key={module.id}
                id={module.id}
                className="flex scroll-mt-6 flex-col rounded-2xl border border-[#d9d5bf] bg-[#fffdf8] p-6 md:p-8"
              >
                <div className="mb-7 flex items-center justify-between text-[#986e2e]">
                  <module.icon size={26} strokeWidth={1.5} aria-hidden="true" />
                  <span className="font-mono text-xs">{module.number}</span>
                </div>
                <h3 className="mb-4 text-xl font-medium">{module.title}</h3>
                <p className="mb-6 text-sm leading-7 text-[#777065]">
                  {module.description}
                </p>
                <p className="mt-auto mb-4 text-xs leading-5 text-[#986e2e]">
                  {module.status}
                </p>
                <Link
                  href={module.link}
                  className="flex items-center justify-between border-t border-[#e7e2d5] pt-4 text-sm font-medium"
                >
                  {module.label}
                  <ArrowUpRight size={17} aria-hidden="true" />
                </Link>
              </article>
            ))}
          </div>
        </section>
        <section
          id="workflow"
          className="scroll-mt-6 bg-[#262e3a] px-5 py-16 text-[#fffdf8] md:px-10 md:py-20"
        >
          <div className="mx-auto max-w-[1280px]">
            <p className="mb-3 text-xs tracking-widest text-[#d9b97a]">
              {zh ? "研究流程" : "THE RESEARCH WORKFLOW"}
            </p>
            <h2 className="mb-9 text-3xl font-normal md:text-[40px]">
              {zh
                ? "一个问题，一条清楚的研究路径。"
                : "One question. A clear research path."}
            </h2>
            <ol className="grid gap-8 md:grid-cols-3">
              {(zh
                ? [
                    [
                      "选择公司",
                      "从已接入的公司目录中找到对象，加入自己的关注。",
                    ],
                    [
                      "设定问题与预算",
                      "明确研究问题、时间范围和预算后提交任务。",
                    ],
                    [
                      "阅读结果与缺口",
                      "查看真实任务状态、部分报告、来源及尚未满足的条件。",
                    ],
                  ]
                : [
                    [
                      "Choose a company",
                      "Find a company in the connected directory and follow it.",
                    ],
                    [
                      "Set a question and budget",
                      "Submit a task with an explicit question, horizon and budget.",
                    ],
                    [
                      "Read findings and gaps",
                      "Review actual task state, partial reports, sources and unmet conditions.",
                    ],
                  ]
              ).map(([title, description], index) => (
                <li key={title} className="border-t border-[#4b525c] pt-5">
                  <span className="mb-4 block font-mono text-xs text-[#d9b97a]">
                    0{index + 1}
                  </span>
                  <h3 className="mb-3 text-lg">{title}</h3>
                  <p className="text-sm leading-7 text-[#b9bec5]">
                    {description}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        </section>
        <section
          id="data"
          className="mx-auto grid max-w-[1360px] scroll-mt-6 gap-8 px-5 py-16 md:grid-cols-2 md:px-10 md:py-24"
        >
          <div>
            <p className="mb-3 text-xs tracking-widest text-[#986e2e]">
              {zh ? "数据与边界" : "DATA & BOUNDARIES"}
            </p>
            <h2 className="text-3xl leading-tight font-normal">
              {zh
                ? "数据有来源，能力有范围。"
                : "Sources are explicit. Scope is clear."}
            </h2>
          </div>
          <div className="space-y-5 text-sm leading-7 text-[#777065]">
            <p>
              {zh
                ? "公司目录当前包含本地已接入的记录，不代表全市场覆盖或实时行情。首页演示使用虚构数据；登录后的公司与研究记录来自自有服务。"
                : "The directory contains locally connected records, not full-market coverage or a live price feed. Homepage demos use fictional data; signed-in company and research records come from our service."}
            </p>
            <p>
              {zh
                ? "真实模型研究默认关闭。报告可能只有部分结果，流程完成不等于完整分析；未知费用、来源限制和证据缺口会明确显示。"
                : "Model research is disabled by default. Reports may be partial; task completion is not complete analysis. Unknown cost, source restrictions and evidence gaps remain visible."}
            </p>
          </div>
        </section>
        <section className="mx-5 mb-16 rounded-2xl bg-[#fdcc6a] px-6 py-10 text-center md:mx-10 md:py-14">
          <h2 className="mb-4 text-3xl font-normal">
            {zh
              ? "从你想了解的公司开始。"
              : "Start with a company you want to understand."}
          </h2>
          <Link
            href="/register"
            className="mt-3 inline-block rounded-md bg-[#191816] px-7 py-3.5 text-sm font-medium text-[#fffdf8]"
          >
            {zh ? "创建研究账户" : "Create a research account"} →
          </Link>
        </section>
      </main>
      <footer className="border-t border-[#d9d5bf] px-5 py-7 md:px-10">
        <div className="mx-auto flex max-w-[1280px] flex-wrap items-center justify-between gap-4 text-xs text-[#777065]">
          <span>
            TradeAgent · {zh ? "个人研究空间" : "Your research space"}
          </span>
          <div className="flex flex-wrap gap-5">
            <Link href="/login">{zh ? "登录" : "Sign in"}</Link>
            <Link href="/app">{zh ? "研究门户" : "Research portal"}</Link>
            <a href="#data">{zh ? "数据说明" : "Data & sources"}</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
