"""Convert inspected evidence into reviewable JSX, never runtime HTML injection.

Only the previously captured page is read. Third-party executable embeds are
discarded; observed media must resolve through the checked local asset map.
"""
import hashlib
import json
import subprocess
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "docs/research/simplywall-st-1b042a47/root-8a5edab2"
COMPONENTS = ROOT / "src/components/sites/simplywall-st-1b042a47/root-8a5edab2"
SHARED = COMPONENTS.parent / "shared"
VOID = {"img", "input", "br", "hr", "link", "meta", "source", "wbr"}
NAMES = ["SourceNavigation", "HeroSection", "PlatformSection", "TrackingSection",
         "PortfolioAnalysisSection", "ResearchSection", "StockSearchSection",
         "DiscoverySection", "SmartUpdatesSection", "CommunitySection",
         "TestimonialsSection", "FinalCtaSection", "SourceFooter"]
ATTRS = {"class": "className", "tabindex": "tabIndex", "autoplay": "autoPlay",
         "playsinline": "playsInline", "stroke-width": "strokeWidth",
         "stroke-linecap": "strokeLinecap", "stroke-linejoin": "strokeLinejoin",
         "fill-rule": "fillRule", "clip-rule": "clipRule", "viewbox": "viewBox",
         "autocomplete": "autoComplete", "hreflang": "hrefLang"}


class Node:
    def __init__(self, tag, attrs):
        self.tag, self.attrs, self.children = tag, dict(attrs), []


class Tree(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node("root", [])
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


inline_rules = {}
captures = json.loads((RESEARCH / "computed-full-20261006-1440.json").read_text(encoding="utf-8"))
responsive = {width: json.loads((RESEARCH / f"computed-full-20261006-{width}.json").read_text(encoding="utf-8")) for width in (768, 390)}
manifest = json.loads((RESEARCH / "downloaded-media-20261006.json").read_text(encoding="utf-8"))
media = {entry["url"] for entry in manifest["assets"]}


def descendants(node, tag):
    found = []
    for child in node.children:
        if isinstance(child, Node):
            if child.tag == tag:
                found.append(child)
            found.extend(descendants(child, tag))
    return found


def text_content(node):
    return "".join(child if isinstance(child, str) else text_content(child) for child in node.children)


research_tree = Tree(captures[5]["nodes"][0]["html"]).root
tab_nodes = [node for node in descendants(research_tree, "div") if node.attrs.get("class") in {"tab", "tab is-active"}]
figure_nodes = descendants(research_tree, "figure")
tab_entries = []
for tab_node, figure_node in zip(tab_nodes, figure_nodes, strict=True):
    image = descendants(figure_node, "img")[0]
    tab_entries.append({"label": text_content(descendants(tab_node, "h4")[0]),
                        "description": text_content(descendants(tab_node, "p")[0]),
                        "icon": descendants(tab_node, "img")[0].attrs["src"],
                        "src": image.attrs["src"], "alt": image.attrs["alt"]})
(COMPONENTS / "research-tabs.ts").write_text('import type { SourceImage } from "../shared/types";\n\ninterface ResearchTab extends SourceImage {\n  label: string;\n  description: string;\n  icon: string;\n}\n\nexport const researchTabs: readonly ResearchTab[] = ' + json.dumps(tab_entries, ensure_ascii=False, indent=2) + ';\n', encoding="utf-8")


def quoted(value):
    return json.dumps(value, ensure_ascii=False)


def render(node, section, depth=3, counters=None):
    counters = counters if counters is not None else {"tab": 0, "figure": 0}
    indent = "  " * depth
    if isinstance(node, str):
        return indent + "{" + quoted(node) + "}" if node.strip() or node == " " else ""
    attrs = node.attrs.copy()
    classes = attrs.get("class", "")
    if node.tag in {"script", "style", "link", "iframe"} or classes == "section-11":
        return ""
    if section == 1 and node.tag == "video":
        return indent + "<HeroMedia />"
    if section == 1 and classes.startswith("flex h-[575px]"):
        return indent + "<HeroMedia />"
    if section == 1 and classes.startswith("hero__review "):
        return indent + "<HeroReviews />"
    if section == 0 and attrs.get("data-sws-embed") == "nav-search":
        return indent + "<SourceStockSearch />"
    if section == 5 and classes == "w-[350px] flex-none pr-[24px] max-[991px]:w-full":
        return indent + '''<div className="w-[350px] flex-none pr-[24px] max-[991px]:w-full">
          {researchTabs.map((tab, index) => (
            <div key={tab.label} className={activeIndex === index ? "tab is-active" : "tab"} role="button" tabIndex={0} aria-pressed={activeIndex === index} onClick={() => setActiveIndex(index)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setActiveIndex(index); } }}>
              <img src={getSourceAsset(tab.icon)} alt="" />
              <div>
                <h4 className="tab__name">{tab.label}</h4>
                <p className="tab__desc">{tab.description}</p>
              </div>
            </div>
          ))}
        </div>'''
    extra = []
    if section == 0:
        if classes == "dropdown-2 w-dropdown":
            extra += ['onMouseEnter={() => setFeaturesOpen(true)}', 'onMouseLeave={() => setFeaturesOpen(false)}']
        if classes == "dropdown-toggle w-dropdown-toggle":
            attrs.pop("aria-expanded", None)
            extra += ['aria-expanded={featuresOpen}']
        if classes == "dropdown-content-wrapper w-dropdown-list":
            attrs.pop("class", None)
            extra += ['className={`dropdown-content-wrapper w-dropdown-list${featuresOpen ? " w--open" : ""}`}']
        if classes == "nav-menu w-nav-menu":
            extra += ['data-nav-menu-open={menuOpen ? "" : undefined}']
        if classes == "menu-button w-nav-button":
            attrs.pop("aria-expanded", None)
            attrs.pop("class", None)
            extra += ['className={`menu-button w-nav-button${menuOpen ? " w--open" : ""}`}']
            extra += ['aria-expanded={menuOpen}', 'onClick={() => setMenuOpen(!menuOpen)}',
                      'onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setMenuOpen(!menuOpen); } }}']
    if section == 5 and node.tag == "figure":
        index = counters["figure"]
        counters["figure"] += 1
        if index > 0:
            return ""
        return indent + '''{researchTabs.map((tab, index) => (
          <figure key={tab.label} className={activeIndex === index ? "is-active" : ""}>
            <img src={getSourceAsset(tab.src)} alt={tab.alt} className="h-auto w-full" />
          </figure>
        ))}'''
    if "style" in attrs:
        declaration = attrs.pop("style")
        style_class = "source-inline-" + hashlib.sha256(declaration.encode()).hexdigest()[:8]
        inline_rules[style_class] = declaration
        attrs["class"] = (attrs.get("class", "") + " " + style_class).strip()
    for name, value in attrs.items():
        if name.startswith("on") or name.startswith("data-track"):
            continue
        if name == "src":
            if value not in media:
                raise ValueError(f"Unmapped observed media: {value}")
            extra.append(f'src={{getSourceAsset({quoted(value)})}}')
            continue
        if name == "href" and value.startswith("/"):
            value = "https://simplywall.st" + value
        if name in {"muted", "loop", "autoplay", "playsinline"}:
            extra.append(ATTRS.get(name, name))
        elif name == "tabindex":
            extra.append(f'tabIndex={{{int(value)}}}')
        else:
            extra.append(f'{ATTRS.get(name, name)}={{{quoted(value or "")}}}')
    opening = indent + "<" + node.tag + (" " + " ".join(extra) if extra else "")
    if node.tag in VOID:
        return opening + " />"
    children = [render(child, section, depth + 1, counters) for child in node.children]
    return opening + ">\n" + "\n".join(child for child in children if child) + "\n" + indent + "</" + node.tag + ">"


for section, name in enumerate(NAMES):
    parsed = Tree(captures[section]["nodes"][0]["html"])
    jsx = render(parsed.root.children[0], section)
    client = section in (0, 5)
    imports = ['/* eslint-disable @next/next/no-img-element -- Preserve the inspected source DOM and intrinsic media dimensions. */'] if "<img " in jsx else []
    if client:
        imports += ['"use client";', '', 'import { useState } from "react";']
    if "getSourceAsset(" in jsx:
        imports += ['import { getSourceAsset } from "../shared/assets";']
    if section == 1:
        imports += ['import { HeroMedia } from "./HeroMedia";', 'import { HeroReviews } from "./HeroReviews";']
    if section == 0:
        imports += ['import { SourceStockSearch } from "./SourceStockSearch";']
    if section == 5:
        imports += ['import { researchTabs } from "./research-tabs";']
    state = ""
    if section == 0:
        imports = [line.replace('import { useState }', 'import { useEffect, useState }') for line in imports]
        state = '''  const [featuresOpen, setFeaturesOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setFeaturesOpen(false);
        setMenuOpen(false);
      }
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);
'''
    if section == 5:
        state = '  const [activeIndex, setActiveIndex] = useState(0);\n'
    (COMPONENTS / f"{name}.tsx").write_text("\n".join(imports) + f"\n\nexport function {name}() {{\n" + state + "  return (\n" + jsx + "\n  );\n}\n", encoding="utf-8")
    spec = [f"# {name} specification", "", f"Target: src/components/sites/simplywall-st-1b042a47/root-8a5edab2/{name}.tsx", "",
            "DOM, verbatim content, child media, and every computed style are recorded in",
            f"`computed-full-20261006-1440.json`, root index {section}. This record is the exact specification; no estimated values.",
            "Responsive child records: same root index in `computed-full-20261006-768.json` and `computed-full-20261006-390.json`.",
            "Screenshots: corresponding viewport captures under docs/design-references/simplywall-st-1b042a47/root-8a5edab2/.", "",
            "## Container computed styles", "```json", json.dumps(captures[section]["nodes"][0]["styles"], indent=2), "```", "",
            "## Responsive container bounds", "```json", json.dumps({str(w): responsive[w][section]["nodes"][0]["rect"] for w in responsive}, indent=2), "```", "",
            "## Assets and content", "Actual URLs resolve via shared/assets.ts and downloaded-media-20261006.json. All source text remains verbatim.", "",
            "## States and remaining QA"]
    if section == 0:
        spec += ["Desktop Features hover and Escape are captured in desktop-features-hover-open.json. White dropdown, 6px radius; existing source CSS implements w--open.",
                 "Mobile opened layout captured in mobile-menu-open.json: menu top72px, margins0 12px, padding0 24px, display block and white background. Open button receives w--open. Opening/closing transition still needs comparison.",
                 "Search field default appearance uses captured dimensions. Preview link goes to source search; remote suggestions/authentication are not implemented."]
    elif section == 5:
        spec += ["Click-driven: Risks & Rewards activation is captured in research-risks-active.json. Selected tab aria-pressed=true and is-active; selected figure opacity1, others0, transition opacity .3s ease-in-out.",
                 "All eight contents and images are captured in the default DOM. Remaining source states and keyboard behavior require QA; local Enter/Space activation supports testing."]
    else:
        spec += ["Static section except source links and real hero video. Link destinations remain the observed source URL until matching routes exist locally.",
                 "Source stylesheet defines button hover brightness(.94), filter/opacity .15s ease. Live hover measurement and full visual comparison remain pending."]
    (RESEARCH / "components" / f"{name}.spec.md").write_text("\n".join(spec) + "\n", encoding="utf-8")

(SHARED / "captured-overrides.css").write_text("\n".join(f":where(.sws-source) .{name} {{ {rule} }}" for name, rule in sorted(inline_rules.items())) + "\n", encoding="utf-8")
print(f"Prepared {len(NAMES)} explicit JSX sections and their specification records.")
subprocess.run(["node", "scripts/localize-sections-simplywall-st-root-8a5edab2.mjs"], cwd=ROOT, check=True)
