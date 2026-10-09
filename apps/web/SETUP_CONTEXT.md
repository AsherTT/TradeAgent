# TradeAgent clone lab setup

Validated on 2026-10-04 (Asia/Shanghai).

- This is the actual clone lab for the approved TradeAgent V2-B frontend.
- Upstream: https://github.com/JCodesMore/ai-website-cloner-template.git
- Base commit: f50066df3f4bdca057d3b239be6f49f17724bb13 (template 0.5.1).
- The upstream origin remote was removed per README standalone setup guidance.
- Existing nvm environment retained: Node v24.21.0, npm 11.19.0.
- Node/npm command entry: C:\nvm4w\nodejs; existing cache: D:\Tools\npm-cache.
- Lockfile dependencies installed; package.json/package-lock.json unchanged.
- Two large packages were recovered through npm mirror; both exactly match the
  original lockfile SHA-512 integrity. No global registry or runtime changes.
- Local setup fix: same Geist/Geist Mono Latin fonts loaded with next/font/local
  to avoid Google font timeouts. Sources/license: src/app/fonts/README.md.
- npm run check passed after the fix (lint, typecheck, production build).
- Dev page, stylesheet and both font resources returned HTTP 200.
- Validation servers were stopped; no source website has been cloned yet.

Use the canonical .agents/skills/clone-website/SKILL.md and AGENTS.md for actual
cloning tasks. Match observed source design and behavior 1:1 before customization.
Save computed styles, screenshots, component specifications and visual QA results.

2026-10-06 continuation: source DOM/styles and screenshots were captured at
1440, 768 and 390px, and three real first-screen media assets were saved. A partial
scoped foundation now wires the two Bureau fonts, source tokens and two SVGs.
Lint, typecheck and production build passed; both compiled font resources returned
HTTP 200 with bytes matching the originals. Inter, full interaction sampling and
complete section specs are still pending. The root scaffold is unchanged, so this
is not a completed source clone. See
docs/research/simplywall-st-1b042a47/root-8a5edab2/PROGRESS_20261006.md.

Start local development:

    npm.cmd run dev -- --hostname 127.0.0.1 --port 3107

Current production config is output: standalone. For production serving follow
Next's standalone-server instructions rather than assuming npm start is final
packaging. No deployment setup was changed in this preparation.

TradeAgent baseline:
D:\桌面\Trade\TradeAgent\docs\07_前端与部署\FRONTEND_DESIGN_V2_B_BASELINE.md
Detailed setup/verification:
D:\桌面\Trade\TradeAgent\docs\07_前端与部署\CLONER_SETUP_20261003.md
