// SPDX-License-Identifier: Apache-2.0
import {el,local,words,records} from "./lesson-ui.mjs";
import {modelView,previewModel} from "./diagram.mjs";
export function teachingView(ctx,teaching,{compact=false}={}) {
  const w=words(ctx.language), root=el("div");
  root.append(el("h3",w.worked));
  const grid=el("div",undefined,{class:"er-grid"});
  for (const [index,worked] of teaching.worked.entries()) {
    const card=el("article",undefined,{class:"er-card"});
    card.append(el("h3",String(index+1)),modelView(ctx.item,worked.model,ctx.language),
      el("p",local(worked.explanation,ctx.language)));
    grid.append(card);
  }
  root.append(grid,el("h3",w.counterexamples));
  const witnesses=el("div",undefined,{class:"er-grid"});
  for (const witness of teaching.counterexamples) {
    const card=el("article",undefined,{class:"er-card"});
    card.append(el("p",local(witness.explanation,ctx.language)));
    if (!compact) card.append(modelView(ctx.item,previewModel(ctx.item,witness.answer.choices),ctx.language));
    card.append(el("p",records(ctx.item,witness.snapshot,ctx.language),{class:"er-records"}));
    witnesses.append(card);
  }
  root.append(witnesses,el("p",w.finite,{class:"er-muted"})); return root;
}
export function teachingPanel(ctx,parent) {
  const w=words(ctx.language), details=el("details");
  details.append(el("summary",w.worked));const body=el("div");details.append(body);parent.append(details);
  let last;
  return teaching=>{
    details.hidden=!teaching;
    const next=JSON.stringify(teaching);
    if (last!==next) {body.replaceChildren(...(teaching?[teachingView(ctx,teaching)]:[]));last=next;}
  };
}

