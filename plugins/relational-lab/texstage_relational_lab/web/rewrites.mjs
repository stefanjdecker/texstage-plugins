// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import {CHILDREN, DomainError, InputError, ResourceLimit, infer} from "./validation.mjs";

// Rebuild only from a checked source tree and named rule. No replacement AST is trusted.
export function rewriteTree(exercise, tree, step) {
  const headers = infer(tree, exercise.relations, exercise.task.allowed_operators);
  let selected = tree.length - 1;
  for (const child of step.path) {
    const positions = CHILDREN[tree[selected][0]];
    if (child >= positions.length) throw new DomainError("rule-path");
    selected = tree[selected][positions[child]];
  }
  const fail = reason => { throw new DomainError(reason, selected); };
  if (!exercise.task.allowed_rules.includes(step.rule)) fail("rule-not-allowed");
  // Temporary references are expression objects; serialize fresh postorder indices below.
  const expressions = tree.map(node => ({node, inputs:[]}));
  for (const expression of expressions) expression.inputs = CHILDREN[expression.node[0]].map(p => expressions[expression.node[p]]);
  const original = expressions[selected], op = original.node[0], inner = original.inputs[0];
  const unary = (kind, input, argument) => ({node:[kind,0,argument], inputs:[input]});
  let replacement;
  switch (step.rule) {
    case "split-select":
      if (op !== "select" || original.node[2].length < 2) fail("rule-not-applicable");
      replacement = unary("select", unary("select", inner, original.node[2].slice(1)), original.node[2].slice(0,1));
      break;
    case "push-select-left":
    case "push-select-right": {
      if (op !== "select" || !["join","product"].includes(inner.node[0])) fail("rule-not-applicable");
      const side = step.rule.endsWith("left") ? 0 : 1;
      const available = new Set(headers[inner.node[side + 1]].map(c => c[0]));
      const needed = original.node[2].flatMap(a => a.slice(1)).filter(t => t[0] === "a").map(t => t[1]);
      if (needed.some(n => !available.has(n))) fail("attribute-side-condition");
      replacement = {node:inner.node, inputs:[...inner.inputs]};
      replacement.inputs[side] = unary("select", inner.inputs[side], original.node[2]);
      break;
    }
    case "product-to-join":
      if (op !== "select" || inner.node[0] !== "product") fail("rule-not-applicable");
      replacement = {node:["join",0,0,original.node[2]], inputs:inner.inputs};
      break;
    case "collapse-project":
      if (op !== "project" || inner.node[0] !== "project") fail("rule-not-applicable");
      if (original.node[2].some(n => !inner.node[2].includes(n))) fail("projection-side-condition");
      replacement = unary("project", inner.inputs[0], original.node[2]);
      break;
    default: fail("rule-not-allowed");
  }
  const output = [];
  const emit = (expression, substitute = true) => {
    if (substitute && expression === original) return emit(replacement, false);
    const row = structuredClone(expression.node);
    CHILDREN[row[0]].forEach((position, i) => { row[position] = emit(expression.inputs[i], substitute); });
    output.push(row);
    return output.length - 1;
  };
  emit(expressions.at(-1));
  try { infer(output, exercise.relations, exercise.task.allowed_operators); }
  catch (error) { if (error instanceof InputError) throw new ResourceLimit("derived-tree"); throw error; }
  return output;
}
