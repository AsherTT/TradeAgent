import type { ReactNode } from "react";

export interface CompanyDataStatusRow {
  id: string;
  label: string;
  updatedAtLabel: string;
}

export interface CompanyDataStatusContent {
  heading: string;
  dataColumn: string;
  updatedColumn: string;
  rows: readonly CompanyDataStatusRow[];
}

export interface CompanyDataStatusTableProps extends CompanyDataStatusContent {
  children?: ReactNode;
}

export interface CompanyDataSourceItem {
  label: string;
  href?: string;
}

export interface CompanyDataSourceRow {
  id: string;
  packageLabel: string;
  timeframeLabel: string;
  data: readonly string[];
  sources: readonly CompanyDataSourceItem[];
}

export interface CompanyDataSourcesContent {
  heading: string;
  introductionBeforeLink: string;
  provider: CompanyDataSourceItem & { href: string };
  introductionAfterLink: string;
  columns: readonly [string, string, string, string];
  rows: readonly CompanyDataSourceRow[];
  footnote: string;
  financialPeriodDescription: string;
  learnMore: CompanyDataSourceItem & { href: string };
}

export type CompanyAnalysisParagraphPart = string | (CompanyDataSourceItem & { href: string });

export interface CompanyAnalysisModelContent {
  modelHeading: string;
  modelParagraph: readonly CompanyAnalysisParagraphPart[];
  teamDescription: string;
  industryHeading: string;
  industryParagraph: readonly CompanyAnalysisParagraphPart[];
}

export interface CompanyAnalystSourceRow {
  id: string;
  analyst: string;
  institution: string;
}

export interface CompanyAnalystSourcesContent {
  heading: string;
  description: string;
  columns: readonly [string, string];
  rows: readonly CompanyAnalystSourceRow[];
}
