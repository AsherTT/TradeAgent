import {
  companySourceHeadingClassName,
  companySourceLinkClassName,
  companySourceParagraphClassName,
} from "../shared/company-source-styles";
import type {
  CompanyAnalysisModelContent,
  CompanyAnalysisParagraphPart,
} from "./types";

function renderParagraphParts(parts: readonly CompanyAnalysisParagraphPart[]) {
  return parts.map((part, index) => (
    typeof part === "string" ? part : (
      <a
        key={`${index}-${part.label}`}
        href={part.href}
        target="_blank"
        rel="noopener noreferrer nofollow"
        className={companySourceLinkClassName}
      >
        {part.label}
      </a>
    )
  ));
}

export function CompanyAnalysisModel({
  modelHeading,
  modelParagraph,
  teamDescription,
  industryHeading,
  industryParagraph,
}: CompanyAnalysisModelContent) {
  return (
    <>
      <h3 className={companySourceHeadingClassName}>{modelHeading}</h3>
      <p className={companySourceParagraphClassName}>
        {renderParagraphParts(modelParagraph)}
      </p>
      <p className={companySourceParagraphClassName}>{teamDescription}</p>
      <h3 className={companySourceHeadingClassName}>{industryHeading}</h3>
      <p className={companySourceParagraphClassName}>
        {renderParagraphParts(industryParagraph)}
      </p>
    </>
  );
}
