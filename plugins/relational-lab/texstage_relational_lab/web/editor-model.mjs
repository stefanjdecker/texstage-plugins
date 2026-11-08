// SPDX-License-Identifier: Apache-2.0
// Pure tree edits. Node paths are an implementation detail, never an input field.
import {answerFor, CHILDREN, infer, InputError} from './validation.mjs';
import {rewriteTree} from './rewrites.mjs';
export const clone = value => structuredClone(value);
export function unpack(tree) {
  if (!tree.length) return null;
  answerFor({mode:'construct',tree});
  const nodes=[];
  for (const [index,row] of tree.entries()) {
    const positions=CHILDREN[row[0]];
    if (positions.some(p=>row[p]>=index)) throw new InputError('child-index');
    nodes.push({row:clone(row),children:positions.map(p=>nodes[row[p]])});
  }
  return nodes.at(-1);
}
export function pack(root) {
  const tree=[];
  function visit(node,depth=0) {
    if (depth>=8 || tree.length>=16) throw new InputError('tree-size');
    const row=clone(node.row);
    CHILDREN[row[0]].forEach((p,i)=>{row[p]=visit(node.children[i],depth+1);});
    tree.push(row); return tree.length-1;
  }
  if(root)visit(root);
  if(tree.length)answerFor({mode:'construct',tree});
  return tree;
}
export function at(root,path) {
  let node=root;
  for(const side of path){if(!node?.children[side])throw new InputError('node-path');node=node.children[side];}
  return node;
}
export function replace(tree,path,node) {
  if(!path.length)return pack(node);
  const root=unpack(tree),parent=at(root,path.slice(0,-1));
  parent.children[path.at(-1)]=node;
  return pack(root);
}
export function branch(tree,path) {return pack(at(unpack(tree),path));}
export function treeFor(item,answer) {
  answerFor(answer);
  if(answer.mode==='construct')return clone(answer.tree);
  let tree=clone(item.baseline_tree);
  for(const step of answer.steps)tree=rewriteTree(item,tree,step);
  return tree;
}
export function nodesOf(tree) {
  if(!tree.length)return [];
  unpack(tree);const output=[],seen=new Set();
  function walk(index,path) {
    if(path.length>=8||seen.has(index))throw new InputError('not-a-tree');
    seen.add(index);
    output.push({index,path,row:tree[index]});
    CHILDREN[tree[index][0]].forEach((p,side)=>walk(tree[index][p],[...path,side]));
  }
  walk(tree.length-1,[]);if(seen.size!==tree.length)throw new InputError('not-a-tree');return output;
}
export function columnsFor(item,tree,path,child) {
  try{
    const node=at(unpack(tree),path),selected=child===undefined?node:node.children[child];
    return infer(pack(selected),item.relations,item.task.allowed_operators).at(-1);
  }catch{return [];}
}
export function starter(item) {
  return item.mode==='rewrite'?{mode:'rewrite',steps:[]}:{mode:'construct',tree:clone(item.initial_tree||[])};
}
export function structuralError(item,answer) {
  try{const tree=treeFor(item,answer);infer(tree,item.relations,item.task.allowed_operators);return null;}
  catch(error){return error;}
}
export class History {
  constructor(answer){this.reset(answer);}
  reset(answer){this.values=[clone(answer)];this.index=0;}
  get value(){return clone(this.values[this.index]);}
  push(answer){this.values=this.values.slice(0,this.index+1);this.values.push(clone(answer));if(this.values.length>40)this.values.shift();this.index=this.values.length-1;}
  undo(){if(this.index>0)this.index--;return this.value;}
  redo(){if(this.index+1<this.values.length)this.index++;return this.value;}
}
