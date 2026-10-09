# SourceStockSearch preview specification

Target: src/components/sites/simplywall-st-1b042a47/root-8a5edab2/SourceStockSearch.tsx.
Source: navigation root0 in computed-full-20261006-1440.json, actual search widget descendants.
Captured outer wrapper height38px, radius6px, background#fafafa, width100% of the responsive `.search` container.
The original input gives the widget intrinsic width245.6px at desktop. Preserve that width in the temporary anchor; the existing search container can still clip when space is constrained. Confirmed in source-metrics-1440-comparison.json.
Captured icon24×24px, left12px; text left48px, BureauSans13px, normal line-height.
Icon fill is measured #9e7333, independent of text color; use shared SolidSearchIcon.
The original input's autocomplete results/service have not been inspected. This preview intentionally uses the already observed source search URL as an anchor; it is an explicit partial interaction, not a working local stock search.
Source `.search` hides the widget at the measured mobile breakpoint; existing source styles provide that behavior.
All appearance comes from captured values; the input-to-link interaction deviation and missing suggestions block final fidelity acceptance.
