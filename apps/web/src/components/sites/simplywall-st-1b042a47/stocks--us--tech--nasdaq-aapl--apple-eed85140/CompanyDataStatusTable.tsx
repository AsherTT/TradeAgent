import "../shared/company-foundation.css";

import type { CompanyDataStatusTableProps } from "./types";

export function CompanyDataStatusTable({
  heading,
  dataColumn,
  updatedColumn,
  rows,
  children,
}: CompanyDataStatusTableProps) {
  return (
    <section className="sws-company-source rounded-[12px] bg-[var(--sws-company-surface)] p-4 md:p-8">
      <h2 className="m-0 font-[family-name:var(--font-sws-bureau-serif)] text-[24px] leading-[32px] font-medium text-white">
        {heading}
      </h2>
      <div className="overflow-x-auto pt-8">
        <table
          aria-label={heading}
          className="w-full table-auto border-collapse border border-[var(--sws-company-border)] text-[13px] leading-[19.5px] lg:text-[14px] lg:leading-[21px]"
        >
          <thead className="bg-[var(--sws-company-table-header)] text-white">
            <tr>
              <th scope="col" className="px-4 py-2 text-left font-bold">
                {dataColumn}
              </th>
              <th scope="col" className="px-4 py-2 text-right font-bold">
                {updatedColumn}
              </th>
            </tr>
          </thead>
          <tbody className="font-normal">
            {rows.map((row) => (
              <tr
                key={row.id}
                className="border-b border-[var(--sws-company-border)] last:border-[var(--sws-company-border-faint)]"
              >
                <td className="px-4 py-2 text-left">{row.label}</td>
                <td className="px-4 py-2 text-right">{row.updatedAtLabel}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {children}
    </section>
  );
}
