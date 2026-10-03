# Frontend Strategy

## Objective

Use a high-fidelity reference implementation to establish TradeAgent's visual language and
interaction quality, then adapt it into an original research workbench backed by TradeAgent's own
contracts and APIs.

The approved starting workflow is the `clone-website` agent skill in
`https://github.com/JCodesMore/ai-website-cloner-template`. The upstream project is a source and
workflow reference, not a dependency that may overwrite this repository.

## Required workflow

1. Select user-approved target URLs and record the exact pages and states in scope.
2. Create a standalone sibling clone-lab project from a reviewed, pinned upstream commit.
3. Perform the pure emulation pass first:
   - desktop, tablet, and mobile screenshots;
   - fonts, colors, spacing, layout, assets, and computed styles;
   - click, hover, scroll, time-driven, loading, empty, and error states;
   - per-component specifications and visual comparison evidence.
4. Run the upstream lint, typecheck, and production build checks.
5. Perform a separate TradeAgent adaptation pass:
   - replace target branding, copy, and assets that are not owned or licensed;
   - map the visual system to original TradeAgent navigation and domain language;
   - preserve explicit insufficient-evidence, data-quality, maturity, integrity, and confidence
     states rather than hiding them for visual simplicity;
   - meet accessibility, performance, responsive, and frontend testing requirements.
6. Move only reviewed code and assets into `apps/web`, convert package management to the root pnpm
   workspace, and add typed clients for stable backend contracts.

## Integration gates

### Phase 5 design foundation

- Design references and component specifications may be produced now.
- Mock data may demonstrate the research submission and run-status experience.
- No mock result may be represented as real research, live market data, or investment advice.

### After Gate C

- Integrate `POST /research` and `GET /research/{research_run_id}`.
- Represent pending, running, complete, insufficient-evidence, budget-exhausted, and failed states.
- Surface research budgets, evidence availability, quality-gate decisions, and durable progress.

### Phases 6-9

- Add Evidence, Thesis, Forecast, Replay, Evaluation, and Backtest UI only when the corresponding
  domain contracts and persistence behavior are stable.

### Phase 10 productization

- Complete route integration, accessibility audit, performance budgets, visual regression,
  component tests, and end-to-end tests.
- Qualify the frontend against actual backend state transitions and failure modes.

## Non-negotiable boundaries

- Keep the initial clone outside this repository and away from the current dirty working tree.
- Do not copy authentication, tracking, proprietary backend behavior, or inaccessible states.
- Do not ship third-party logos, text, fonts, images, or video without the relevant rights.
- Do not let the reference site's terminology replace the domain vocabulary in `CONTEXT.md`.
- Do not let the frontend calculate financial indicators or reinterpret quality/integrity gates.
- Do not treat visual similarity as functional, accessibility, security, or performance
  qualification.
