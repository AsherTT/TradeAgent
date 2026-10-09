import { readFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { setImmediate } from "node:timers/promises";
import { runInThisContext } from "node:vm";
import { JSDOM } from "jsdom";
import { act, createElement } from "react";
import ts from "typescript";

const require = createRequire(import.meta.url);
const sourceRoot = fileURLToPath(new URL("../src/", import.meta.url));
const modules = new Map();

// Compile the real application modules; only HTTP and router navigation are supplied by tests.
export function applicationModule(relativePath) {
  return load(resolve(sourceRoot, relativePath));
}

function load(path) {
  // Styles are verified in the browser; component behavior needs no CSS execution.
  if (path.endsWith(".css")) return {};
  if (path.endsWith(".json")) return JSON.parse(readFileSync(path, "utf8"));
  const file = [path, `${path}.tsx`, `${path}.ts`].find(existsSync);
  if (!file) throw new Error(`Application module not found: ${path}`);
  if (modules.has(file)) return modules.get(file).exports;
  const compiledModule = { exports: {} };
  modules.set(file, compiledModule);
  const compiled = ts.transpileModule(readFileSync(file, "utf8"), {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true,
      target: ts.ScriptTarget.ES2022,
    },
    fileName: file,
  }).outputText;
  const resolveImport = (name) => name.startsWith("@/")
    ? load(resolve(sourceRoot, name.slice(2)))
    : name.startsWith(".") ? load(resolve(dirname(file), name)) : require(name);
  runInThisContext(`(function(require,module,exports){${compiled}\n})`, { filename: file })(
    resolveImport, compiledModule, compiledModule.exports,
  );
  return compiledModule.exports;
}

export function deferred() {
  let resolve;
  const promise = new Promise((complete) => { resolve = complete; });
  return { promise, resolve };
}

export async function flush(action = () => {}) {
  await act(async () => { await action(); await setImmediate(); });
}

export async function mount(t, Component, props, fetch, locale = "en") {
  const dom = new JSDOM("<!doctype html><div id='root'></div>", { url: "http://localhost/app" });
  const originals = new Map();
  for (const [name, value] of Object.entries({
    window: dom.window, document: dom.window.document, Node: dom.window.Node,
    HTMLElement: dom.window.HTMLElement, navigator: dom.window.navigator,
    self: dom.window, fetch, IS_REACT_ACT_ENVIRONMENT: true,
  })) {
    originals.set(name, Object.getOwnPropertyDescriptor(globalThis, name));
    Object.defineProperty(globalThis, name, { configurable: true, writable: true, value });
  }
  const { createRoot } = await import("react-dom/client");
  const { AppRouterContext } = require("next/dist/shared/lib/app-router-context.shared-runtime");
  const { PathnameContext } = require("next/dist/shared/lib/hooks-client-context.shared-runtime");
  const { LanguageProvider } = applicationModule("components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider");
  const navigations = [];
  const router = {
    replace: (url) => navigations.push(url), push: (url) => navigations.push(url),
    refresh: () => {}, prefetch: () => {}, back: () => {}, forward: () => {},
  };
  const root = createRoot(dom.window.document.getElementById("root"));
  t.after(async () => {
    await flush(() => root.unmount());
    dom.window.close();
    for (const [name, original] of originals) {
      if (original) Object.defineProperty(globalThis, name, original);
      else delete globalThis[name];
    }
  });
  await flush(() => root.render(createElement(AppRouterContext.Provider, { value: router },
    createElement(PathnameContext.Provider, { value: "/app" },
      createElement(LanguageProvider, { initialLocale: locale }, createElement(Component, props)),
    ),
  )));
  return {
    document: dom.window.document, navigations,
    text: () => dom.window.document.body.textContent,
    click: (label) => {
      const button = [...dom.window.document.querySelectorAll("button")].find((node) => node.textContent === label);
      if (!button) throw new Error(`Button not found: ${label}`);
      return flush(() => button.click());
    },
    fill: (selector, value) => flush(() => {
      const input = dom.window.document.querySelector(selector);
      const prototype = input.tagName === "TEXTAREA"
        ? dom.window.HTMLTextAreaElement.prototype : dom.window.HTMLInputElement.prototype;
      Object.getOwnPropertyDescriptor(prototype, "value").set.call(input, value);
      input.dispatchEvent(new dom.window.Event("input", { bubbles: true }));
    }),
    submit: () => flush(() => dom.window.document.querySelector("form button").click()),
  };
}
