import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement } from "react";
import { applicationModule, flush, mount } from "./component-harness.mjs";

const key = (ui, target, value, options = {}) => {
  const event = new ui.document.defaultView.KeyboardEvent("keydown", { key: value, bubbles: true, cancelable: true, ...options });
  return flush(() => target.dispatchEvent(event)).then(() => event);
};

test("app shell search shortcut uses the real directory and never intercepts editing or modal input", async (t) => {
  const { AppShell } = applicationModule("components/workspace/AppShell");
  const ui = await mount(t, AppShell, { children: createElement("div", null,
    createElement("input", { "aria-label": "Question" }),
    createElement("div", { contentEditable: true, suppressContentEditableWarning: true }, createElement("span", null, "notes")),
  ) }, async () => { throw new Error("Shell must not request data"); });
  const search = ui.document.querySelector('header a[href="/app/company-search"]');
  assert.ok(search);
  const input = ui.document.querySelector("input");
  const editable = ui.document.querySelector("[contenteditable] span");
  for (const target of [input, editable]) assert.equal((await key(ui, target, "/")).defaultPrevented, false);
  await key(ui, ui.document.body, "/", { ctrlKey: true });
  await key(ui, ui.document.body, "/", { repeat: true });
  await key(ui, ui.document.body, "/", { isComposing: true });
  assert.deepEqual(ui.navigations, []);
  assert.equal((await key(ui, ui.document.body, "/")).defaultPrevented, true);
  assert.deepEqual(ui.navigations, ["/app/company-search"]);
  const dialog = ui.document.createElement("section");
  dialog.setAttribute("role", "dialog");
  dialog.setAttribute("aria-modal", "true");
  ui.document.body.append(dialog);
  await key(ui, ui.document.body, "/");
  assert.deepEqual(ui.navigations, ["/app/company-search"]);
});

test("mobile navigation contains focus, restores scrolling and never reopens after route or breakpoint changes", async (t) => {
  const { AppShell } = applicationModule("components/workspace/AppShell");
  const ui = await mount(t, AppShell, { children: createElement("p", null, "Research content") }, async () => Response.json({}), "en", { desktop: false, bodyOverflow: "scroll" });
  const open = ui.document.querySelector('button[aria-label="Open navigation"]');
  await flush(() => open.click());
  const panel = ui.document.getElementById("workbench-navigation");
  const close = panel.querySelector('button[aria-label="Close navigation"]');
  assert.equal(panel.getAttribute("aria-modal"), "true");
  assert.equal(ui.document.activeElement, close);
  assert.equal(ui.document.body.style.overflow, "hidden");
  assert.ok(ui.document.querySelector("header").parentElement.hasAttribute("inert"));
  const first = panel.querySelector('a[href]');
  await flush(() => first.focus());
  await key(ui, first, "Tab", { shiftKey: true });
  assert.ok(panel.contains(ui.document.activeElement));
  assert.notEqual(ui.document.activeElement, close);
  await key(ui, ui.document.activeElement, "Tab");
  assert.equal(ui.document.activeElement, first);
  await key(ui, close, "Escape");
  assert.equal(panel.getAttribute("aria-modal"), null);
  assert.equal(ui.document.activeElement, open);
  assert.equal(ui.document.body.style.overflow, "scroll");
  await flush(() => open.click());
  await ui.resizeDesktop(true);
  assert.equal(panel.getAttribute("aria-modal"), null);
  assert.equal(ui.document.body.style.overflow, "scroll");
  assert.equal(ui.document.activeElement.getAttribute("href"), "/app/company-search");
  await ui.resizeDesktop(false);
  assert.equal(panel.getAttribute("aria-modal"), null);
  await flush(() => open.click());
  await ui.navigatePathname("/app/research/test-run");
  assert.equal(panel.getAttribute("aria-modal"), null);
  assert.equal(panel.querySelector('[aria-current="page"]').getAttribute("href"), "/app/research");
  await ui.navigatePathname("/app");
  assert.equal(panel.getAttribute("aria-modal"), null);
});

test("shared chrome switches language without clearing fields or duplicating the legacy account header", async (t) => {
  const { AppShell } = applicationModule("components/workspace/AppShell");
  const { AccountShell } = applicationModule("components/accounts/AccountShell");
  const ui = await mount(t, AppShell, { children: createElement(AccountShell, null,
    createElement("input", { defaultValue: "Saved research question" }),
  ) }, async () => Response.json({}), "zh");
  assert.equal(ui.document.querySelectorAll("header").length, 1);
  await ui.click("EN");
  assert.equal(ui.document.querySelector("input").value, "Saved research question");
  assert.equal(ui.document.getElementById("workbench-navigation").querySelector('[aria-current="page"]').textContent, "Portal");
  assert.equal(ui.document.querySelector('a[href="/app#account"]').textContent, "Account");
});
