// SPDX-License-Identifier: Apache-2.0
// Run the installed module through the installed host's actual result contract.
import fs from "node:fs";
const config = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
Object.defineProperty(globalThis, "crypto", {value: undefined, configurable: true});
const engine = await import(config.module);
const identity = await import(config.identity);
const {validateResult, makeOutcome} = await import(config.contract_module);
const library = await engine.start({});
const requests = JSON.parse(fs.readFileSync(0, "utf8"));
const results = [];
for (const request of requests) {
  if (Object.hasOwn(request, "hash")) {
    results.push({hash: identity.sha256(request.hash)}); continue;
  }
  let state;
  const began = performance.now();
  try {
    const job = {...config.job, namespace: request.namespace, binding: request.binding ?? {
      ...config.job.binding, seed: request.seed, options: request.options ?? {}}};
    state = await engine.load(library, request.seed, Object.hasOwn(request, "options") ? request.options : {});
    if (Object.hasOwn(request, "budget")) {
      try {
        engine.analyze(state.seed, JSON.parse(request.text), new engine.Budget(request.budget));
        results.push({budget_error: null});
      } catch (error) { results.push({budget_error: error.constructor.name}); }
      continue;
    }
    const raw = await engine.evaluate(state, request.text, request.context || {});
    if (request.data_patch) Object.assign(raw.data, request.data_patch);
    const result = validateResult(raw, job);
    const outcome = makeOutcome(result, [], job);
    let reuseRefused = false, disposalRefused = false;
    try { await engine.evaluate(state, request.text); } catch { reuseRefused = true; }
    await engine.dispose(state);
    try { await engine.evaluate(state, request.text); } catch { disposalRefused = true; }
    results.push({result, outcome, reuseRefused, disposalRefused, milliseconds: performance.now() - began});
  } catch (error) {
    results.push({load_or_contract_error: true, error: error.message});
  } finally {
    if (state) await engine.dispose(state);
  }
}
process.stdout.write(JSON.stringify(results));
