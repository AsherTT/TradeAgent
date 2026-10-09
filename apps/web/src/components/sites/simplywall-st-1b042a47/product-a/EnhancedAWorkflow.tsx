"use client";

import { useLanguage } from "../shared/i18n/LanguageProvider";


export function EnhancedAWorkflow() {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  return (
    <section className={"p-[40px] text-center"} data-section={"narratives"} id="workflow">
      <div className={"mx-auto max-w-[1062px] px-[40px] pt-[20px]"}>
        <h2 className={"heading-40 source-inline-b1f22df6"}>
          {zh ? "提出问题。" : "Ask a question. "}
          <span className={"serif"}>
            {zh ? "沿证据研究。" : "Follow the evidence."}
          </span>
        </h2>
        <p className={"mt-[10px] min-h-[38px] font-[family-name:var(--ui)] text-[15px] leading-[19px]"}>
          {zh ? "把公司、研究问题与来源连接起来，保留每次研究的范围与结果。" : "Connect the company, question and sources. Keep the scope and results of each research task."}
          <br />
        </p>
        <h3 className={"mt-[21px] pb-[40px] font-[family-name:var(--serif)] text-[24px] font-light leading-[28.8px]"}>
          {zh ? "从公司出发的三个步骤" : "Three steps, starting with a company"}
        </h3>
        <div className={"relative mt-[32px] flex gap-[16px]"}>
          <div className={"absolute inset-x-[162px] top-[4px] h-[24px] bg-[rgba(152,110,46,0.25)] max-[991px]:hidden"}>

          </div>
          <ul className={"relative z-[1] flex flex-1 max-[640px]:flex-col max-[640px]:gap-[24px]"}>
            <li className={"flex flex-1 flex-col items-center gap-[18px] px-[16px]"}>
              <div className={"flex h-[32px] w-[32px] items-center justify-center rounded-full bg-[var(--bronze)] font-[family-name:var(--ui)] text-[16px] text-white"}>
                {zh ? "1" : "1"}
              </div>
              <div className={"font-[family-name:var(--serif)] text-[18px] font-light leading-[32px]"}>
                {zh ? "选择公司" : "Choose a company"}
              </div>
            </li>
            <li className={"flex flex-1 flex-col items-center gap-[18px] px-[16px]"}>
              <div className={"flex h-[32px] w-[32px] items-center justify-center rounded-full bg-[var(--bronze)] font-[family-name:var(--ui)] text-[16px] text-white"}>
                {zh ? "2" : "2"}
              </div>
              <div className={"font-[family-name:var(--serif)] text-[18px] font-light leading-[32px]"}>
                {zh ? "提出研究问题" : "Ask a research question"}
              </div>
            </li>
            <li className={"flex flex-1 flex-col items-center gap-[18px] px-[16px]"}>
              <div className={"flex h-[32px] w-[32px] items-center justify-center rounded-full bg-[var(--bronze)] font-[family-name:var(--ui)] text-[16px] text-white"}>
                {zh ? "3" : "3"}
              </div>
              <div className={"font-[family-name:var(--serif)] text-[18px] font-light leading-[32px]"}>
                {zh ? "核对结论与来源" : "Check findings and sources"}
              </div>
            </li>
          </ul>
        </div>
        <div className={"mt-[55px] flex flex-col items-center gap-[12px]"}>
          <a href={"/register"} className={"btn btn--lg"}>
            {zh ? "创建研究账户" : "Create a research account"}
          </a>
          <p className={"font-[family-name:var(--ui)] text-[14px] leading-[26px] text-[rgba(25,24,22,0.7)]"}>
            {zh ? "在自己的账户内管理公司与研究。" : "Manage companies and research in your own account."}
          </p>
        </div>
      </div>
    </section>
  );
}
