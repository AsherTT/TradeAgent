"use client";

import { CompanyDataStatusTable } from "@/components/sites/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/CompanyDataStatusTable";
import { CompanyDataSources } from "@/components/sites/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/CompanyDataSources";
import { CompanyAnalysisModel } from "@/components/sites/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/CompanyAnalysisModel";
import { CompanyAnalystSources } from "@/components/sites/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/CompanyAnalystSources";
import { CompanySourceFrame } from "@/components/sites/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/CompanySourceFrame";
import type { CompanyAnalysisParagraphPart } from "@/components/sites/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/types";
import { LanguageSwitcher, useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import { sourceDataSources, sourceDataStatus } from "./source-fixture";
import { sourceAnalysisModel } from "./analysis-model-fixture";
import { sourceAnalystSources } from "./analyst-sources-fixture";

export function CompanySourcePreview() {
  const { t } = useLanguage();
  const translateParts = (parts: readonly CompanyAnalysisParagraphPart[]) =>
    parts.map((part) => typeof part === "string" ? t(part) : { ...part, label: t(part.label) });
  return (
    <div>
      <header className="mx-auto flex max-w-[1199px] flex-wrap items-center justify-between gap-4 px-4 py-4 lg:px-6">
          <h1 className="text-sm text-white/60">{t("Company source component preview")}</h1>
          <div className="[&_button[aria-pressed=true]]:text-[#191816]">
            <LanguageSwitcher appearance="account" />
          </div>
      </header>
      <CompanySourceFrame>
      <CompanyDataStatusTable
        {...sourceDataStatus}
        heading={t(sourceDataStatus.heading)}
        dataColumn={t(sourceDataStatus.dataColumn)}
        updatedColumn={t(sourceDataStatus.updatedColumn)}
        rows={sourceDataStatus.rows.map((row) => ({ ...row, label: t(row.label) }))}
      >
        <CompanyDataSources
          {...sourceDataSources}
          heading={t(sourceDataSources.heading)}
          introductionBeforeLink={t(sourceDataSources.introductionBeforeLink)}
          introductionAfterLink={t(sourceDataSources.introductionAfterLink)}
          columns={[t(sourceDataSources.columns[0]), t(sourceDataSources.columns[1]), t(sourceDataSources.columns[2]), t(sourceDataSources.columns[3])]}
          rows={sourceDataSources.rows.map((row) => ({
            ...row,
            packageLabel: t(row.packageLabel),
            timeframeLabel: t(row.timeframeLabel),
            data: row.data.map(t),
            sources: row.sources.map((item) => ({ ...item, label: t(item.label) })),
          }))}
          footnote={t(sourceDataSources.footnote)}
          financialPeriodDescription={t(sourceDataSources.financialPeriodDescription)}
          learnMore={{ ...sourceDataSources.learnMore, label: t(sourceDataSources.learnMore.label) }}
        />
        <CompanyAnalysisModel
          {...sourceAnalysisModel}
          modelHeading={t(sourceAnalysisModel.modelHeading)}
          modelParagraph={translateParts(sourceAnalysisModel.modelParagraph)}
          teamDescription={t(sourceAnalysisModel.teamDescription)}
          industryHeading={t(sourceAnalysisModel.industryHeading)}
          industryParagraph={translateParts(sourceAnalysisModel.industryParagraph)}
        />
        <CompanyAnalystSources
          {...sourceAnalystSources}
          heading={t(sourceAnalystSources.heading)}
          description={t(sourceAnalystSources.description)}
          columns={[t(sourceAnalystSources.columns[0]), t(sourceAnalystSources.columns[1])]}
        />
      </CompanyDataStatusTable>
      </CompanySourceFrame>
      <footer className="mx-auto max-w-[1199px] px-4 py-6 text-sm leading-6 text-white/60 lg:px-6">
        <p>{t("This preview uses static samples from the source website. It is not the complete company page and does not represent actual TradeAgent data.")}</p>
        <p>{t("The report columns and source section are restored here. The complete company report, charts and sidebar interactions are still pending. Sidebar links open the original website; market cap is a captured reference value.")}</p>
        <p>
          {t("Only the three publicly captured rows are shown. The source website requires sign-in to show the remaining 85 analysts; the expanded list has not been captured.")}
        </p>
      </footer>
    </div>
  );
}
