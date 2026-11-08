// SPDX-License-Identifier: Apache-2.0
// Operate the actual labelled controls. Answers are never injected as JSON.
const assert=require('node:assert/strict');
exports.actions=(page,w)=>{
 const editor=page.locator('.participant-input .rl-editor'),form=editor.locator('.rl-inspector');
 const click=label=>form.getByRole('button',{name:label,exact:true}).click();
 const choose=(label,value)=>form.getByLabel(label,{exact:true}).selectOption(value);
 async function start(table='books'){await choose(w.relation,table);await click(w.addTable);}
 const edit=()=>editor.getByRole('button',{name:w.edit,exact:true}).click();
 const inspect=()=>editor.getByRole('button',{name:w.result,exact:true}).click();
 async function add(op,table){await choose(w.operator,op);if(table)await choose(w.otherRelation,table);await click(w.addOperator);}
 async function condition(left,kind,value){
  const group=form.locator('.rl-condition').first();
  await group.getByLabel(w.left+' · '+w.attribute,{exact:true}).selectOption(left);
  await group.getByLabel(w.right+' · '+w.kind,{exact:true}).selectOption(kind);
  const input=group.getByLabel(w.right+' · '+(kind==='a'?w.attribute:w.value),{exact:true});
  if(kind==='a'||kind==='bool')await input.selectOption(String(value));else await input.fill(String(value));
  await click(w.apply);
 }
 async function select(path){await editor.locator('.rl-tree-row button[data-path="'+path.join('.')+'"]').click();}
 async function construction(){
  await start();await add('select');await condition('topic','text','db');
  await add('join','loans');await condition('book','a','item');
  await select([1]);await add('select');await condition('open','bool',true);
  await select([]);await add('join','members');await condition('borrower','a','member');
  await add('project');
  for(const input of await form.locator('.rl-node-form input[type=checkbox]').all())await input.uncheck();
  await form.getByLabel('name',{exact:true}).check();await click(w.apply);
 }
 async function rewrite(steps){for(const step of steps){await select(step.path);await choose(w.rule,step.rule);await click(w.applyRule);}}
 async function controls(save){
  const reset=async()=>{await editor.getByRole('button',{name:w.startOver,exact:true}).click();await start();};
  await start();await add('project');
  await form.getByLabel('book',{exact:true}).uncheck();await click(w.apply);
  assert(await save.isDisabled());await editor.getByText(w.errors['empty-project'],{exact:true}).waitFor();
  await click(w.discard);await reset();await add('select');
  await condition('book','int','1.5');assert(await save.isDisabled());
  await editor.getByText(w.errors.integer,{exact:true}).waitFor();
  await condition('book','int',999);await inspect();await editor.getByText(w.emptyRows,{exact:true}).waitFor();await edit();
  await reset();await add('rename');await form.getByLabel('book →',{exact:true}).fill('number');await click(w.apply);assert(!(await save.isDisabled()));
  await reset();await add('product','loans');assert(!(await save.isDisabled()));
  await reset();await add('union','loans');assert(await save.isDisabled());await editor.getByText(w.errors['incompatible-headers'],{exact:true}).first().waitFor();
  await select([1]);await choose(w.relation,'books');await click(w.apply);assert(!(await save.isDisabled()));
  await reset();await add('difference','books');await inspect();await editor.getByText(w.emptyRows,{exact:true}).waitFor();await edit();
  await form.getByText(w.replaceRelation,{exact:true}).first().click();
  await click(w.keepLeft);assert.equal(await editor.locator('.rl-tree-row').count(),1);
  await editor.getByRole('button',{name:w.undo,exact:true}).click();assert.equal(await editor.locator('.rl-tree-row').count(),3);
  await editor.getByRole('button',{name:w.startOver,exact:true}).click();
 }
 return {editor,form,start,add,condition,select,construction,rewrite,edit,inspect,controls};
};
