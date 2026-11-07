// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
// Flat page-map implementation, independent of the Python nested-page model.
import {InputError, ResourceLimit, fields, object, list, int, requireInput as need} from "./validation.mjs";

export class Budget {
  constructor(limit = 20000) {
    if (!int(limit, 0, 20000)) throw new Error("Invalid work limit");
    this.remaining = limit;
  }
  charge(amount = 1) {
    this.remaining -= amount;
    if (this.remaining < 0) throw new ResourceLimit("work");
  }
}
export const same = (a, b) => a.length === b.length && a.every((v, i) => v === b[i]);
export const capacity = (page, seed) => page.kind === "leaf" ? seed.leaf_capacity : seed.internal_capacity;
export const items = page => page.kind === "leaf" ? page.keys : page.children;

export function inspectTree(raw, seed, budget, {initial = true, pending = null} = {}) {
  need(fields(raw, ["root", "nodes"]) && int(raw.root, 0, 63) && list(raw.nodes, 1, initial ? 31 : 35));
  const nodes = new Map();
  let prior = -1;
  for (const n of raw.nodes) {
    need(object(n) && int(n.id, 0, 63) && n.id > prior);
    prior = n.id;
    need(n.kind === "leaf" || n.kind === "internal");
    need(fields(n, n.kind === "leaf" ? ["id", "kind", "keys", "next"] : ["id", "kind", "keys", "children"]));
    need(list(n.keys, 0, 7) && n.keys.every(k => int(k, -9999, 9999)));
    if (n.kind === "leaf") {
      need(n.next === null || int(n.next, 0, 63));
      nodes.set(n.id, {...n, keys: [...n.keys]});
    } else {
      need(list(n.children, 1, 7) && n.children.every(id => int(id, 0, 63)));
      nodes.set(n.id, {...n, keys: [...n.keys], children: [...n.children]});
    }
  }
  const visited = new Set(), preorder = [], leaves = [], depths = new Set(), violations = [];
  function visit(id, depth) {
    need(nodes.has(id) && !visited.has(id) && depth <= (initial ? 2 : 3));
    visited.add(id);
    preorder.push(id);
    const node = nodes.get(id), entries = items(node);
    budget.charge(1 + node.keys.length + (node.kind === "leaf" ? 0 : node.children.length));
    need(node.keys.every((k, i) => i === 0 || node.keys[i - 1] < k));
    const cap = capacity(node, seed);
    const min = id === raw.root ? (node.kind === "leaf" ? 0 : 2) : Math.ceil(cap / 2);
    if (entries.length < min || entries.length > cap) {
      const allowed = entries.length === cap + 1 || (id !== raw.root && entries.length === min - 1);
      need(!initial && id === pending && allowed);
      violations.push(id);
    }
    if (node.kind === "leaf") {
      leaves.push(id); depths.add(depth);
      return [...node.keys];
    }
    need(node.keys.length === node.children.length - 1);
    const childKeys = node.children.map(child => visit(child, depth + 1));
    need(childKeys.every(group => group.length > 0));
    need(childKeys.every((group, i) => i === 0 || childKeys[i - 1].at(-1) < group[0]));
    need(same(node.keys, childKeys.slice(1).map(group => group[0])));
    return childKeys.flat();
  }
  const keys = visit(raw.root, 0);
  need(visited.size === nodes.size && depths.size === 1 && keys.length <= (initial ? 40 : 41));
  need(same(violations, pending === null ? [] : [pending]));
  need(leaves.every((id, i) => nodes.get(id).next === (leaves[i + 1] ?? null)));
  if (initial) need(raw.root === 0 && same(preorder, Array.from({length: nodes.size}, (_, i) => i)));
  return {root: raw.root, nodes, keys, leaves, height: [...depths][0],
    next: Math.max(...nodes.keys()) + 1};
}

export function snapshot(tree) {
  return {root: tree.root, nodes: [...tree.nodes.values()].sort((a, b) => a.id - b.id).map(n =>
    n.kind === "leaf" ? {...n, keys: [...n.keys]} : {...n, keys: [...n.keys], children: [...n.children]})};
}

export function refresh(tree, budget) {
  const leaves = [];
  function visit(id) {
    const n = tree.nodes.get(id);
    budget.charge(1 + items(n).length);
    if (n.kind === "leaf") {
      leaves.push(id);
      return n.keys[0];
    }
    const minima = n.children.map(visit);
    n.keys = minima.slice(1);
    return minima[0];
  }
  visit(tree.root);
  leaves.forEach((id, i) => { tree.nodes.get(id).next = leaves[i + 1] ?? null; });
}

export function minimum(tree, id, budget) {
  let node = tree.nodes.get(id);
  while (node.kind !== "leaf") {
    budget.charge();
    node = tree.nodes.get(node.children[0]);
  }
  budget.charge();
  return node.keys[0];
}

export function route(tree, key, budget) {
  const path = [];
  let id = tree.root;
  while (true) {
    const node = tree.nodes.get(id);
    budget.charge(1 + items(node).length);
    path.push(id);
    if (node.kind === "leaf") return path;
    let i = 0;
    while (i < node.keys.length && key >= node.keys[i]) i++;
    id = node.children[i];
  }
}

export function parentOf(tree, id, budget) {
  if (id === tree.root) return {parent: null, at: null};
  for (const node of tree.nodes.values()) {
    budget.charge(1 + items(node).length);
    if (node.kind !== "internal") continue;
    const at = node.children.indexOf(id);
    if (at >= 0) return {parent: node, at};
  }
  throw new Error("Replay page is unreachable");
}

export function verifyReplay(tree, seed, pending, expectedKeys, budget) {
  refresh(tree, budget);
  try {
    const checked = inspectTree(snapshot(tree), seed, budget, {initial: false, pending});
    if (!same(checked.keys, expectedKeys)) throw new InputError("key-conservation");
    return checked;
  } catch (error) {
    if (error instanceof InputError) throw new Error("Replay invariant");
    throw error;
  }
}
