// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import {canonical, sha256} from "./identity.mjs";
import {sourceFor, answerFor} from "./validation.mjs";
import {Budget, inspectTree, snapshot, route, same, capacity, items, minimum, parentOf, verifyReplay} from "./tree.mjs";
export {Budget};

const difference = (a, b) => {
  for (let i = 0; i < Math.max(a.length, b.length); i++) if (a[i] !== b[i]) return i;
  return null;
};
const fail = (base, state, reason, checked, at, node) => ({...base,
  replay: {state, reason, checked_repairs: checked, at, node}});

// The engine consumes the same bounded iterator synchronously. Renderers can
// yield between steps and request owned snapshots without copying the algorithm.
export function analyze(seed, answer, budget = new Budget()) {
  const steps = analyzeSteps(seed, answer, budget);
  let result;
  do { result = steps.next(); } while (!result.done);
  return result.value;
}

export function* analyzeSteps(seed, answer, budget = new Budget(), capture = false) {
  sourceFor(seed);
  answerFor(seed, answer);
  const tree = inspectTree(seed.tree, seed, budget);
  const beforeKeys = [...tree.keys], beforeHeight = tree.height;
  yield capture ? {kind: "start", tree: snapshot(tree), pending: null} : null;
  const task = seed.task, kind = task.kind, key = kind === "range" ? task.lower : task.key;
  const expectedPath = route(tree, key, budget);
  const base = {format: 1, exercise: sha256(canonical(seed)), answer: sha256(canonical(answer)), operation: kind};
  const mismatch = difference(answer.path, expectedPath);
  if (mismatch !== null) return fail(base, "invalid", "wrong-path", 0, mismatch, expectedPath[mismatch] ?? null);
  const claims = {path: true, keys: null, separators: null, height: null};
  if (kind === "lookup" || kind === "range") {
    const leaves = [], keys = [];
    let id = expectedPath.at(-1);
    while (true) {
      const node = tree.nodes.get(id);
      budget.charge(1 + node.keys.length);
      leaves.push(id);
      for (const k of node.keys) if (kind === "lookup" ? k === key : key <= k && k <= task.upper) keys.push(k);
      yield null;
      if (kind === "lookup" || !node.keys.length || node.keys.at(-1) >= task.upper || node.next === null) break;
      id = node.next;
    }
    if (kind === "range") {
      const wrong = difference(answer.leaves, leaves);
      if (wrong !== null) return fail(base, "invalid", "wrong-scan", 0, wrong, leaves[wrong] ?? null);
    }
    claims.keys = same(answer.keys, keys);
    return {...base, replay: {state: "complete", checked_repairs: 0}, claims,
      read: {path: expectedPath, leaves, keys, page_visits: expectedPath.length + leaves.length - 1}};
  }

  const cap = node => capacity(node, seed), min = node => Math.ceil(cap(node) / 2);
  const target = tree.nodes.get(expectedPath.at(-1));
  const found = target.keys.indexOf(key);
  budget.charge(1 + target.keys.length);
  let pending = null;
  if (kind === "insert" && found < 0) {
    target.keys.push(key);
    target.keys.sort((a, b) => a - b);
    if (target.keys.length > cap(target)) pending = target.id;
  } else if (kind === "delete" && found >= 0) {
    target.keys.splice(found, 1);
    if (target.id !== tree.root && target.keys.length < min(target)) pending = target.id;
  }
  const expectedKeys = kind === "insert" ? [...new Set([...beforeKeys, key])].sort((a, b) => a - b) :
    beforeKeys.filter(k => k !== key);
  const counts = {splits: 0, borrows: 0, merges: 0};
  verifyReplay(tree, seed, pending, expectedKeys, budget);
  yield capture ? {kind: "edit", tree: snapshot(tree), pending} : null;
  for (const [i, repair] of answer.repairs.entries()) {
    budget.charge();
    if (pending === null) return fail(base, "invalid", "extra-repair", i, i, repair.node);
    const node = tree.nodes.get(pending);
    if (repair.node !== pending) return fail(base, "invalid", "wrong-pending-node", i, i, pending);
    const {parent, at} = parentOf(tree, pending, budget);
    const reason = {split: "illegal-split", borrow: "illegal-donor", merge: "illegal-merge"}[repair.op];
    if (repair.op === "split") {
      const contents = items(node), cut = repair.left_count;
      if (contents.length !== cap(node) + 1 || cut < min(node) || cut > cap(node) ||
          contents.length - cut < min(node) || contents.length - cut > cap(node)) {
        return fail(base, "invalid", reason, i, i, pending);
      }
      const boundary = node.kind === "leaf" ? node.keys[cut] : minimum(tree, node.children[cut], budget);
      if (boundary !== repair.separator) return fail(base, "invalid", "wrong-separator", i, i, pending);
      budget.charge(contents.length);
      const rightID = tree.next++;
      let right;
      if (node.kind === "leaf") {
        right = {id: rightID, kind: "leaf", keys: node.keys.splice(cut), next: node.next};
        node.next = rightID;
      } else {
        right = {id: rightID, kind: "internal", keys: [], children: node.children.splice(cut)};
      }
      tree.nodes.set(rightID, right);
      if (parent === null) {
        const rootID = tree.next++;
        tree.nodes.set(rootID, {id: rootID, kind: "internal", keys: [boundary], children: [node.id, rightID]});
        tree.root = rootID;
        pending = null;
      } else {
        parent.children.splice(at + 1, 0, rightID);
        pending = parent.children.length > cap(parent) ? parent.id : null;
      }
      counts.splits++;
    } else {
      if (parent === null || items(node).length !== min(node) - 1) {
        return fail(base, "invalid", reason, i, i, pending);
      }
      const side = parent.children.indexOf(repair.sibling);
      if (side < 0 || Math.abs(side - at) !== 1) return fail(base, "invalid", reason, i, i, pending);
      const sibling = tree.nodes.get(repair.sibling);
      if (repair.op === "borrow") {
        if (items(sibling).length <= min(sibling)) return fail(base, "invalid", reason, i, i, pending);
        budget.charge(1 + items(node).length + items(sibling).length);
        if (side < at) items(node).unshift(items(sibling).pop());
        else items(node).push(items(sibling).shift());
        pending = null;
        counts.borrows++;
      } else {
        if (items(node).length + items(sibling).length > cap(node)) return fail(base, "invalid", reason, i, i, pending);
        const [left, right] = side < at ? [sibling, node] : [node, sibling];
        budget.charge(items(left).length + items(right).length);
        items(left).push(...items(right));
        parent.children.splice(parent.children.indexOf(right.id), 1);
        tree.nodes.delete(right.id);
        if (parent.id === tree.root && parent.children.length === 1) {
          tree.root = parent.children[0];
          tree.nodes.delete(parent.id);
          pending = null;
        } else {
          pending = parent.id !== tree.root && parent.children.length < min(parent) ? parent.id : null;
        }
        counts.merges++;
      }
    }
    verifyReplay(tree, seed, pending, expectedKeys, budget);
    yield capture ? {kind: "repair", index: i, tree: snapshot(tree), pending} : null;
  }
  if (pending !== null) return fail(base, "incomplete", "missing-repair",
    answer.repairs.length, answer.repairs.length, pending);
  const checked = verifyReplay(tree, seed, null, expectedKeys, budget), final = snapshot(tree);
  const separators = final.nodes.filter(n => n.kind === "internal").map(n => ({node: n.id, keys: n.keys}));
  claims.separators = canonical(answer.separators) === canonical(separators);
  claims.height = answer.height === checked.height;
  return {...base, replay: {state: "complete", checked_repairs: answer.repairs.length}, claims, final,
    metrics: {height_before: beforeHeight, height_after: checked.height, leaf_count: checked.leaves.length, ...counts}};
}
