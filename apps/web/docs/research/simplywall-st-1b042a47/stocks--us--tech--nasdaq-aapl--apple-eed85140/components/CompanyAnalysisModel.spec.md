# CompanyAnalysisModel specification

2026-10-09. Source https://simplywall.st/stocks/us/tech/nasdaq-aapl/apple
Target src/components/sites/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/CompanyAnalysisModel.tsx
Screenshot docs/design-references/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/analysis-model-source-desktop.jpg
Evidence CompanyAnalysisModel.source-{desktop,tablet,mobile}.json.gz (9 nodes each, derived from overview bounded artifacts), source-fresh.json (fresh DOM/full outerHTML confirms link attributes, actual670px).

Static props-only component, no client state/network/models. Fragment in existing data status section after DataSources: h3 modelHeading; p mixed modelParagraph; p teamDescription; h3 industryHeading; p mixed industryParagraph. Native inline links, all external target=_blank rel="noopener noreferrer nofollow" exactly fresh source. Do not activate links during verification. Analyst Sources is separate, NOT part of this component.

Use CompanyAnalysisModelContent and CompanyAnalysisParagraphPart (string or {label,href}) from prepared types. Shared company-source-styles exports heading/paragraph/link exact classes; don't duplicate CSS. h3 margin32px0px16px,18/27/500 white lg20/30. p margin0 0 16px,14/23.8/400 white70% lg16/27.2. Links inherit font, gold#fdcb68, no underline -> hover/focus underline, transition none. No extra container/card/padding, no icons/media. Bureau Sans already loaded by lab page.

Verbatim model heading: Analysis Model and Snowflake
Model paragraph parts (spaces matter):
1. "Details of the analysis model used to generate this report is available on our "
2. link "Github page", href https://support.simplywall.st/hc/en-us/categories/360000146555
3. ", we also have "
4. link "guides", SAME support href
5. " on how to use our reports and "
6. link "tutorials on Youtube", SAME support href (source's link destination is unusual but preserve it)
7. "."
Team description: "Learn about the   who designed and built the Simply Wall St analysis model." The source has missing text at the triple space and NO hyperlink; preserve source bug in English, don't invent a team link/person. Chinese localization separately renders grammatical meaning without invented person.
Industry heading: Industry and Sector Metrics
Industry paragraph parts:
1. "Our industry and section metrics are calculated every 6 hours by Simply Wall St, details of our process are available on " (source says section, not sector)
2. link "Github", href https://github.com/SimplyWallSt/Company-Analysis-Model/blob/master/industry_averages.markdown
3. "."

1440 source content799.254; model paragraph54.398 high/team27.199/industry54.398. At768 content696.217/390 content358.377 all remain flow paragraphs; responsive exact fonts as above, no layout breakpoint other than1024 type size. Local lab retains800/704/358 documented framing differences. Below paragraphs wrap naturally; source source desktop region275.976 high from first heading to final p bottom (not including bottom margin).

Builder creates ONLY component and src/app/labs/r1-company-data-status/analysis-model-fixture.ts exporting sourceAnalysisModel:CompanyAnalysisModelContent. Parent integrates localized props via CompanySourcePreview after merge. No API/product route/metadata edits, no analyst fake85 rows/button. User authorized Chinese/English button for all pages, parent provides translated parts.
Builder verify lint/typecheck, commit Chinese; parent build, bilingual1440/768/390 checks, public provider/SSR tests, existing R1 incremental review. Source Analyst Sources expand clicked once: only3 rows remain and signup gate appears; unsupported full state remains pending, not passed.
