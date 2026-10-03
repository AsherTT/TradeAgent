# ADR-0017: Stage frontend design work in an isolated clone lab

Status: accepted

## Context

The architecture schedules the complete product frontend for Phase 10, after the research,
evidence, evaluation, and strict-backtest contracts are stable. Waiting until Phase 10 to explore
the interface would delay design feedback, while integrating a complete UI during Phase 5 would
couple it to contracts and capabilities that do not exist yet.

The selected visual workflow is the `clone-website` agent skill from
`https://github.com/JCodesMore/ai-website-cloner-template`. It uses Next.js 16, React 19,
TypeScript strict mode, Tailwind CSS v4, and shadcn/ui, which match the frozen frontend stack. Its
default scope reproduces visual layout, responsive behavior, assets, and observable interactions
with mock data; it does not supply the real backend, authentication, real-time behavior, financial
semantics, or accessibility qualification.

## Decision

Begin frontend design exploration during Phase 5 without declaring Phase 10 started or complete.
Create the first clone in a standalone sibling project, not in the TradeAgent repository. Pin and
review an exact upstream commit before running its skill or scripts. Preserve its research,
screenshots, component specifications, and visual-diff evidence as design inputs.

After the one-to-one emulation pass, replace unlicensed branding, copy, fonts, and media; then make
the user-directed product changes. Only reviewed components, design tokens, and licensed assets
may move into `apps/web`. Convert the result to the repository's pnpm workspace conventions and
keep TradeAgent domain behavior behind typed frontend contracts.

Integration is staged:

1. Phase 5: isolated clone lab, design tokens, component inventory, responsive and interaction
   prototypes using mock data.
2. After Gate C: integrate research submission, durable run status, budget, failure, and
   insufficient-evidence states through the real API.
3. Phases 6-9: add Evidence, Thesis, Forecast, Replay, Evaluation, and Backtest screens only after
   their contracts stabilize.
4. Phase 10: complete product integration, accessibility, performance, end-to-end tests, and
   production UI qualification.

## Consequences

- The clone lab cannot modify the current intentionally dirty backend working tree.
- A visual clone is not evidence that the target's backend behavior has been reproduced.
- The target URL must be user-approved and lawful to inspect; third-party trademarks, copy, and
  assets require ownership, permission, or replacement.
- Browser automation is required for the cloning workflow.
- The formal Phase 10 gate remains unchanged.
