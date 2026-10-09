import {
  companySourceHeadingClassName,
  companySourceParagraphClassName,
} from "../shared/company-source-styles";
import type { CompanyAnalystSourcesContent } from "./types";

export function CompanyAnalystSources({
  heading,
  description,
  columns,
  rows,
}: CompanyAnalystSourcesContent) {
  return (
    <>
      <h3 className={companySourceHeadingClassName}>{heading}</h3>
      <p className={companySourceParagraphClassName}>{description}</p>
      <div
        role="region"
        aria-label={heading}
        tabIndex={0}
        className="overflow-x-auto pt-4"
      >
        <table className="w-full table-auto border-collapse border border-[var(--sws-company-border)]">
          <thead className="bg-[var(--sws-company-table-header)] text-[13px] leading-[19.5px] text-white lg:text-[14px] lg:leading-[21px]">
            <tr>
              <th scope="col" className="px-4 py-2 text-left font-bold">
                {columns[0]}
              </th>
              <th scope="col" className="px-4 py-2 text-right font-bold">
                {columns[1]}
              </th>
            </tr>
          </thead>
          <tbody className="text-[13px] leading-[19.5px] font-normal text-white lg:text-[14px] lg:leading-[21px]">
            {rows.map((row) => (
              <tr key={row.id} className="border border-[var(--sws-company-border)]">
                <td className="px-4 py-2 text-left">{row.analyst}</td>
                <td className="px-4 py-2 text-right">{row.institution}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
