# Homepage Chinese / English localization

Human request: report progress, then add Chinese and English to the current page ("中午" interpreted as the evident typo for "中文").
Fixed starting point: ed5501f.

- Add a visible 中文 / EN switcher in the desktop navigation and inside the mobile expanded menu; both controls must be keyboard-operable with visible focus and selected-state announcement.
- Default to Simplified Chinese for the first visit. Retain the chosen locale across reloads on this local origin. Validate stored values; unsupported values fall back to Chinese.
- Server-render in the remembered locale, with matching initial `<html lang>` and title; changing locale must update page text, accessible image descriptions, menu label and document language/title without navigating or resetting research selection.
- Cover all existing homepage text regions: navigation, headings, copy, CTAs, research-tab names/descriptions, testimonials and footer. Proper names may remain unchanged. Preserve exact English strings and original media.
- Image/video embedded English is source media, not editable page text; retain it and disclose this limit. External destination pages are outside this local locale preference.
- Do not add business routes, backend integration, branding adaptation or deploy. Prior source fidelity gates are still pending; bilingual functionality is an explicitly requested extension.
- Keep source markup/structure. Localized text is a fragment and localized images remain native img elements. Maintain original layout in English except the language control and space needed for it.
- At narrow desktop widths992–1199, hide the temporary header search to fit the added control and let the stock-search text column shrink to avoid horizontal overflow. At mobile widths the switch is inside the menu. Test both languages at1440/768/390 and inspect992.
- Use centralized local messages, no remote translation service or new package. Chinese uses system CJK fallbacks. The existing generator must reproduce localization rather than overwrite it.
- Verify translation coverage, English preservation, locale fallback, SSR cookie persistence, live switching, both-language responsive layout, retained video/menu/tab behavior, lint/typecheck/build and independent Standards/Spec review.
