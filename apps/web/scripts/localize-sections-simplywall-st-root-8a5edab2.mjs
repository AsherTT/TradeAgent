import { readFile, readdir, writeFile } from "node:fs/promises";
import ts from "typescript";

const componentRoot = "src/components/sites/simplywall-st-1b042a47/root-8a5edab2";
const textInventory = "docs/research/simplywall-st-1b042a47/root-8a5edab2/locale-source-text.json";
const texts = new Set();
const listOnly = process.argv.includes("--list");

function className(element) {
  const attributes = ts.isJsxElement(element) ? element.openingElement.attributes : element.attributes;
  const attribute = attributes.properties.find((property) => ts.isJsxAttribute(property) && property.name.text === "className");
  if (!attribute?.initializer) return "";
  const value = ts.isJsxExpression(attribute.initializer) ? attribute.initializer.expression : attribute.initializer;
  return value && ts.isStringLiteral(value) ? value.text : "";
}

for (const filename of (await readdir(componentRoot)).filter((name) => name.endsWith(".tsx"))) {
  const path = `${componentRoot}/${filename}`;
  let content = (await readFile(path, "utf8")).replaceAll("\r\n", "\n");
  if (!listOnly) {
    content = content.replaceAll(/https:\/\/simplywall\.st\/register(?:\?[^"}]*)?/g, "/register")
      .replaceAll("https://simplywall.st/dashboard", "/login")
      .replaceAll("https://simplywall.st/watchlist", "/app")
      .replaceAll('"Try Simply Wall St free"', '"Create a TradeAgent account"')
      .replaceAll('"Start free"', '"Create a TradeAgent account"')
      .replaceAll('"Create free account"', '"Create a TradeAgent account"')
      .replaceAll('"No credit card required. Free forever."', '"Manage your watchlist in your own account."')
      .replaceAll('data-id={"dashboard-link"} href={"/login"}', 'data-id={"dashboard-link"} href={"/app"}')
      .replaceAll('href={"/login"} data-id={"dashboard-link"}', 'href={"/app"} data-id={"dashboard-link"}');
    // This is an explicitly authorized product account adaptation.
    await writeFile(path, content);
  }
  const source = ts.createSourceFile(filename, content, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const replacements = [];
  const imports = new Set();
  let navigationHook = false;
  function replace(node, text) {
    replacements.push({ start: node.getStart(source), end: node.end, text });
  }
  function visit(node) {
    if (ts.isJsxElement(node) && className(node) === "locales-wrapper-2 w-locales-list") {
      if (!listOnly) {
        replace(node, "<LanguageSwitcher />");
        imports.add("LanguageSwitcher");
      }
      return;
    }
    if (ts.isJsxSelfClosingElement(node) && node.tagName.getText(source) === "img") {
      if (!listOnly) {
        replace(node.tagName, "LocalizedImage");
        imports.add("LocalizedImage");
      }
    }
    if (ts.isJsxExpression(node) && !ts.isJsxAttribute(node.parent) && node.expression) {
      const expression = node.expression;
      if (ts.isStringLiteral(expression) && expression.text.trim()) {
        texts.add(expression.text);
        if (!listOnly) {
          replace(node, `<LocalizedText en={${expression.getText(source)}} />`);
          imports.add("LocalizedText");
        }
      } else if (expression.getText(source) === "tab.label" || expression.getText(source) === "tab.description") {
        if (!listOnly) {
          replace(node, `<LocalizedText en={${expression.getText(source)}} />`);
          imports.add("LocalizedText");
        }
      }
    }
    if (ts.isJsxText(node) && node.text.trim()) {
      const text = node.text.trim();
      texts.add(text);
      if (!listOnly) {
        replace(node, `<LocalizedText en={${JSON.stringify(text)}} />`);
        imports.add("LocalizedText");
      }
    }
    if (ts.isJsxAttribute(node) && ["alt", "aria-label", "en"].includes(node.name.getText(source)) && node.initializer) {
      const expression = ts.isJsxExpression(node.initializer) ? node.initializer.expression : node.initializer;
      if (expression && ts.isStringLiteral(expression) && expression.text.trim()) texts.add(expression.text);
      if (!listOnly && node.name.getText(source) === "aria-label" && filename === "SourceNavigation.tsx" && expression && ts.isStringLiteral(expression)) {
        replace(node.initializer, `{t(${JSON.stringify(expression.text)})}`);
        imports.add("useLanguage");
        navigationHook = true;
      }
    }
    if (ts.isCallExpression(node) && node.expression.getText(source) === "t" && node.arguments[0] && ts.isStringLiteral(node.arguments[0])) {
      texts.add(node.arguments[0].text);
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
  if (listOnly || replacements.length === 0) continue;
  for (const edit of replacements.sort((a, b) => b.start - a.start)) {
    content = content.slice(0, edit.start) + edit.text + content.slice(edit.end);
  }
  content = content.replace(/^\/\* eslint-disable @next\/next\/no-img-element[^\n]*\n/, "");
  if (navigationHook) content = content.replace("export function SourceNavigation() {", "export function SourceNavigation() {\n  const { t } = useLanguage();");
  const importLine = `import { ${[...imports].sort().join(", ")} } from "../shared/i18n/LanguageProvider";\n`;
  // Preserve the client boundary directive at the very beginning of the file.
  content = content.startsWith('"use client";')
    ? content.replace('"use client";\n', '"use client";\n\n' + importLine)
    : importLine + content;
  await writeFile(path, content);
}

const data = ts.createSourceFile("research-tabs.ts", await readFile(`${componentRoot}/research-tabs.ts`, "utf8"), ts.ScriptTarget.Latest, true);
function visitData(node) {
  if (ts.isPropertyAssignment(node) && ["label", "description", "alt"].includes(node.name.getText(data).replaceAll('"', "")) && ts.isStringLiteral(node.initializer)) {
    texts.add(node.initializer.text);
  }
  ts.forEachChild(node, visitData);
}
visitData(data);
if (listOnly) {
  await writeFile(textInventory, JSON.stringify([...texts], null, 2) + "\n");
  console.log(JSON.stringify([...texts], null, 2));
} else {
  console.log("Localized inspected text/media markup and replaced the unused source locale list.");
}
