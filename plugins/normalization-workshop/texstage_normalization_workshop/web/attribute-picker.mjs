// SPDX-License-Identifier: Apache-2.0
import {el,local} from "./lesson-ui.mjs";
// The empty set is an intentional value, used by constant dependencies.
export function picker(ctx, caption, initial, change) {
  const root=el("fieldset"),legend=el("legend",caption),choices=el("div",undefined,{class:"nw-pickers"});
  let value=initial;
  for(const [i,a] of ctx.item.attributes.entries()){
    const input=el("input",undefined,{type:"checkbox","aria-label":a.id,"aria-description":local(a.label,ctx.language)}),label=el("label");
    input.checked=Boolean(value & (1<<i));
    input.addEventListener("change",()=>{value=input.checked?value|(1<<i):value&~(1<<i);change(value);},{signal:ctx.signal});
    label.append(input,document.createTextNode(a.id));choices.append(label);
  }
  root.append(legend,choices);return root;
}
