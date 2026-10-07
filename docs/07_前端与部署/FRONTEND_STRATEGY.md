# Frontend Strategy

## Confirmed product scope (2026-10-08, Asia/Shanghai)

Adopt the approved [enhanced-A design](FRONTEND_DESIGN_ENHANCED_A_20261008.md).
It supersedes V2-B visual unification: preserve observed source pages/internal navigation,
regional typography, controls, density and interaction; unify product identity, account,
company context and cross-region operations. Shared navigation placement, themes, concrete
menu destinations and Agent extension layout still require page observation/confirmation.
Simply Wall St supplies portal/company
organization, Fiscal supplies multi-period financial layout and Quartr supplies
report/source-verification interaction; these must become functional TradeAgent modules.
The user deferred real portfolio/return/dividend tracking and screening until later.
The source homepage is still a prototype with original-site feature links, not a
completed three-source product. Accounts and bounded account-owned research exist;
financial depth, evidence source reading and thesis product integration remain open.

Implementation order and maintained task IDs: [development plan](../01_项目总览/DEVELOPMENT_PLAN.md).
Routes, shared modules, source isolation, API ownership and acceptance:
[frontend architecture](FRONTEND_ARCHITECTURE.md). Start with the own-product homepage,
portal and company-object queries; preserve source reproduction separately. Unimplemented
product buttons must not redirect to a reference site's product as if they were implemented.
Explicit external evidence-source links remain allowed.

This resolves the earlier wait for user frontend scope without marking full P10 complete
or waiving data/provider, asset-rights, migration or release gates. Keep the source observation,
emulation and original adaptation records distinct; unobserved Fiscal/Quartr states
cannot be claimed as faithful reproductions. The workflow below remains the design method.

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
   - retain regional source design and internal navigation; add a lightweight product entrance
     and use TradeAgent domain language without silently removing source controls;
   - preserve explicit insufficient-evidence, data-quality, maturity, integrity, and confidence
     states rather than hiding them for visual simplicity;
   - meet accessibility, performance, responsive, and frontend testing requirements.
6. Integrate existing account contracts and implement missing first-release capabilities in
   bounded increments within the sibling frontend. First confirm representative company,
   financial and reading pages; compare reference and adapted states separately. Move only
   reviewed code/assets into `apps/web` after product acceptance, then convert to root pnpm.

## Backend gap-filling authorization

The user authorized borrowing publicly observable workflow logic to complete own backend
capabilities, not assuming access to third-party private services or subscribing to their APIs.
Map each page/control/state to its local destination, existing contract, missing data/API/
qualification and acceptance evidence. Fill gaps rather than treating hidden controls or demo
data as completed functionality. Portal/company projections, versioned multi-period financials
and source locations, account-authorized material/snippet lookup and bounded search, and account
thesis/forecast commands follow the [overall architecture](../02_架构与契约/ARCHITECTURE.md)
and existing R1-R6 task IDs. Frontend period choices must be explicitly supported by the submission
contract before they can affect research inputs; never change the persisted cutoff through a
display parameter. Source company scores are not evidence-quality scores.

## Integration gates

### Phase 5 design foundation

- Design references and component specifications may be produced now.
- Mock data may demonstrate the research submission and run-status experience.
- No mock result may be represented as real research, live market data, or investment advice.

### After Gate C

- Integrate authenticated `POST /workspace/research`, `GET /workspace/research`,
  `GET /workspace/research/options`, `GET /workspace/research/{run_id}`,
  `POST /workspace/research/{run_id}/cancel` and
  `GET /workspace/research/{run_id}/report` through the exact account BFF allowlist.
- Legacy `/research` paths remain internal-development interfaces; they are not exposed
  by the account BFF and cannot read or cancel account-owned runs.
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
