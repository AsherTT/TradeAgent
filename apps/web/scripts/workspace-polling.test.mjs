import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { runInNewContext } from "node:vm";
import { setImmediate } from "node:timers/promises";
import ts from "typescript";

function polling() {
  const compiledModule = { exports: {} };
  const source = readFileSync(new URL("../src/components/workspace/polling.ts", import.meta.url), "utf8");
  const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
  runInNewContext(compiled, { module: compiledModule, exports: compiledModule.exports, AbortController, setTimeout, clearTimeout });
  return compiledModule.exports.startWorkspacePolling;
}

test("a private response arriving after session invalidation cannot restore records or restart polling", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  let resolveRead;
  let signal;
  let reads = 0;
  const updates = [];
  const start = polling();
  const stop = start({
    load: (requestSignal) => {
      signal = requestSignal;
      reads++;
      return new Promise((resolve) => { resolveRead = resolve; });
    },
    onUpdate: (records) => { updates.push(records); return true; },
    onFailure: () => assert.fail("An invalidated read must stay silent"),
  });
  t.mock.timers.tick(200);
  assert.equal(reads, 1);
  stop();
  assert.equal(signal.aborted, true);
  resolveRead([{ privateRecord: "old account" }, []]);
  await setImmediate();
  t.mock.timers.tick(10000);
  assert.equal(updates.length, 0);
  assert.equal(reads, 1);
});

test("active research polls again, stops when complete, and pending refresh can be cancelled", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  let reads = 0;
  const start = polling();
  const stop = start({
    load: async () => { reads++; return [{ active_research_total: reads === 1 ? 1 : 0 }, []]; },
    onUpdate: ([snapshot]) => snapshot.active_research_total > 0,
    onFailure: () => assert.fail("No failure expected"),
  });
  t.mock.timers.tick(200);
  await setImmediate();
  t.mock.timers.tick(5000);
  await setImmediate();
  t.mock.timers.tick(10000);
  assert.equal(reads, 2);
  stop();
  const cancel = start({ load: async () => { assert.fail("Cancelled initial read"); }, onUpdate: () => true, onFailure: () => {} });
  cancel();
  t.mock.timers.tick(200);
});
