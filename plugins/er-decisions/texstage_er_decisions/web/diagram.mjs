// SPDX-License-Identifier: Apache-2.0
// Preview uses public choices only. It does not grade or infer missing choices.
import {el,names,words,bounds} from "./lesson-ui.mjs";
export function previewModel(item,choices) {
  const graph=structuredClone(item.model), rel=graph.relationship, chosen=new Map(choices);
  for (const d of item.decisions) {
    const option=d.options.find(o=>o.id===chosen.get(d.id));
    if (!option) continue;
    if (d.kind==="role-bounds") Object.assign(rel.roles.find(r=>r.id===d.target),option.value);
    else if (d.kind==="attribute-owner") rel.attributes.find(a=>a.id===d.target).owner=option.value;
    else Object.assign(rel,option.value);
  }
  return graph;
}
export function constraints(item,graph,language) {
  const w=words(language), n=names(item,language), rel=graph.relationship;
  const rows=rel.roles.map(r=>w.de ?
    "Jede einzelne Entität "+n.entities[r.entity]+" nimmt an "+bounds(r)+" Verknüpfungen teil." :
    "Each individual "+n.entities[r.entity]+" participates in "+bounds(r)+" links.");
  for (const a of rel.attributes) {
    const owner=a.owner===null?w.undecided:a.owner==="relationship"?n.relationship:
      n.entities[rel.roles.find(r=>r.id===a.owner).entity];
    rows.push(n.attributes[a.id]+": "+(w.de?"ein Wert pro ":"one value per ")+owner+".");
  }
  rows.push(rel.pair_unique===null?w.undecided:rel.pair_unique?w.unique:w.duplicates);
  return rows;
}
export function modelView(item,graph,language) {
  const w=words(language), n=names(item,language), rel=graph.relationship;
  const root=el("div",undefined,{class:"er-model"});
  // All schematic information is repeated in the adjacent accessible list.
  const diagram=el("div",undefined,{class:"er-diagram","aria-hidden":"true"});
  const entity=r=>{const box=el("div",n.entities[r.entity],{class:"er-node"});box.append(el("small",w.bounds+": "+bounds(r)));return box;};
  const middle=el("div",n.relationship,{class:"er-node "+(rel.form==="association-entity"?"er-association":"er-relation")});
  middle.append(el("small",rel.form===null?w.undecided:rel.form==="relationship"?w.relationship:w.entity));
  diagram.append(entity(rel.roles[0]),el("span","—",{class:"er-link"}),middle,el("span","—",{class:"er-link"}),entity(rel.roles[1]));
  const list=el("ul",undefined,{"aria-label":w.constraints});
  list.append(el("li",n.relationship+": "+(rel.form===null?w.undecided:rel.form==="relationship"?w.relationship:w.entity)));
  for (const line of constraints(item,graph,language)) list.append(el("li",line));
  root.append(diagram,list);return root;
}

