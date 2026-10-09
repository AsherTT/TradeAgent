import type { CompanyDataSourcesContent } from "./types";
import {
  companySourceHeadingClassName,
  companySourceLinkClassName as sourceLinkClassName,
  companySourceParagraphClassName as sourceParagraphClassName,
} from "../shared/company-source-styles";

const sourceSupClassName =
  "static top-auto align-super [font-size:smaller] leading-[1.5]";

export function CompanyDataSources({
  heading,
  introductionBeforeLink,
  provider,
  introductionAfterLink,
  columns,
  rows,
  footnote,
  financialPeriodDescription,
  learnMore,
}: CompanyDataSourcesContent) {
  return (
    <>
      <h3 className={companySourceHeadingClassName}>
        {heading}
      </h3>
      <p className={sourceParagraphClassName}>
        {introductionBeforeLink}
        <a href={provider.href} className={sourceLinkClassName}>
          {provider.label}
        </a>
        {introductionAfterLink}
      </p>
      <div
        role="region"
        aria-label={heading}
        tabIndex={0}
        className="overflow-x-auto pt-4"
      >
        <table className="w-full table-auto border-collapse border border-[var(--sws-company-border)] text-[13px] leading-[19.5px] font-normal text-white lg:text-[14px] lg:leading-[21px]">
          <thead className="bg-[var(--sws-company-table-header)]">
            <tr>
              {columns.map((column, index) => (
                <th
                  key={column}
                  scope="col"
                  className="px-4 py-2 text-left align-middle font-bold"
                >
                  {column}
                  {index === 3 && <sup className={sourceSupClassName}>*</sup>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.id}
                className="border border-[var(--sws-company-border)] last:border-0"
              >
                <td className="px-4 py-2 align-top">{row.packageLabel}</td>
                <td className="px-4 py-2 align-top">{row.timeframeLabel}</td>
                <td className="px-4 py-2 align-top">
                  <ul className="m-0 list-disc pl-4">
                    {row.data.map((item) => (
                      <li key={item} className="m-0 p-0">{item}</li>
                    ))}
                  </ul>
                </td>
                <td className="px-4 py-2 align-top">
                  <ul className="m-0 list-disc pl-4">
                    {row.sources.map((source) => (
                      <li key={source.label} className="m-0 p-0">
                        {source.href ? (
                          <a href={source.href} className={sourceLinkClassName}>
                            {source.label}
                          </a>
                        ) : source.label}
                      </li>
                    ))}
                  </ul>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 mb-4 text-right text-[11px] leading-[16.5px] text-white/70 lg:text-[12px] lg:leading-[18px]">
        <sup className={sourceSupClassName}>*</sup>
        {footnote}
      </p>
      <p className={sourceParagraphClassName}>
        {financialPeriodDescription}
        <a href={learnMore.href} className={sourceLinkClassName}>
          {learnMore.label}
        </a>
        .
      </p>
    </>
  );
}
