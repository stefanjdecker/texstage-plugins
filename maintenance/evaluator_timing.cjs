// SPDX-License-Identifier: Apache-2.0
// Optional test instrumentation. It observes messages without changing their
// payload, worker policy, evaluation deadlines or scheduling.
function observeEvaluatorTiming() {
  const NativeWorker = window.Worker;
  window.__texstageEvaluationTimings = [];
  window.Worker = class extends NativeWorker {
    constructor(url, options) {
      const start = performance.now();
      super(url, options);
      if (String(url).endsWith('/plugin-evaluator-worker.js')) {
        this.__timing = {created:start,constructed:performance.now(),messages:[]};
        window.__texstageEvaluationTimings.push(this.__timing);
        this.addEventListener('message',event => this.__timing.messages.push({
          direction:'received',type:event.data?.t,at:performance.now()}));
      }
    }
    postMessage(message, ...options) {
      if (this.__timing) {
        if (message.t === 'init') this.__timing.job = message.job.id;
        this.__timing.messages.push({direction:'sent',type:message.t,at:performance.now()});
      }
      return super.postMessage(message,...options);
    }
    terminate() {
      if (this.__timing) this.__timing.terminated = performance.now();
      return super.terminate();
    }
  };
}
function summarizeEvaluatorTiming(rows, stats) {
  const values = rows.map(row => {
    const at = (type,direction) => row.messages.find(m=>m.type===type && m.direction===direction)?.at;
    return {constructor_ms:row.constructed-row.created,
      before_init_ms:at('init','sent')-row.constructed,
      init_ms:at('ready','received')-at('init','sent'),
      evaluate_ms:at('result','received')-at('eval','sent'),
      total_ms:row.terminated-row.created};
  });
  if (!values.length || values.some(row=>Object.values(row).some(v=>!Number.isFinite(v))))
    throw new Error('Incomplete evaluator timing observations');
  return Object.fromEntries(Object.keys(values[0]).map(key=>[key,stats(values.map(row=>row[key]))]));
}
module.exports = {observeEvaluatorTiming,summarizeEvaluatorTiming};
