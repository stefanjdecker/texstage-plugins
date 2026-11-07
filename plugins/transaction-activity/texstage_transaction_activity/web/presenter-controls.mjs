// SPDX-License-Identifier: Apache-2.0
import {words,el,button,field,option,shell,answersView,aggregateView,setText,key,commandError,delivered} from './layout.mjs';
export function mount(ctx){const w=words(ctx.language),root=shell(ctx,'tx-controls'),details=el('details'),panel=el('div',undefined,{class:'tx-panel'});details.append(el('summary',w.controls),panel);root.append(details);
 const phase=el('p','',{class:'tx-phase','data-tx':'phase'}),counts=el('div'),error=el('p','',{role:'alert','data-tx':'control-error'}),waiting=el('p','',{role:'status'}),actions=el('div',undefined,{class:'tx-actions'});
 let current=null,busy=false,receipt=null,alive=true,generation=0,rosterKey='',selectedKey='',confirming=false;
 const advance=button(w.advance,()=>send('advance-phase'),ctx.signal,{'data-tx':'advance'}),resume=button(w.resume,()=>send('resume-phase'),ctx.signal,{'data-tx':'resume'});
 const reset=button(w.reset,()=>{confirming=true;confirmBox.hidden=false;paint();confirm.focus();},ctx.signal,{'data-tx':'reset'});
 const confirmBox=el('div',undefined,{class:'tx-conflict'}),confirm=button(w.confirm,()=>{confirming=false;confirmBox.hidden=true;send('_reset');},ctx.signal,{'data-tx':'confirm-reset'}),cancel=button(w.cancel,()=>{confirming=false;confirmBox.hidden=true;paint();reset.focus();},ctx.signal);confirmBox.append(el('p',w.confirmReset),confirm,cancel);confirmBox.hidden=true;
 actions.append(advance,resume,reset);
 const stepping=el('div',undefined,{class:'tx-actions'}),previous=button(w.previous,()=>send('seek-step',{cursor:current.data.cursor-1}),ctx.signal,{'data-tx':'previous'}),next=button(w.next,()=>send('seek-step',{cursor:current.data.cursor+1}),ctx.signal,{'data-tx':'next'}),cursor=el('select',undefined,{'data-tx':'cursor'});
 for(let i=0;i<=ctx.item.exercise.schedule.length;i++)cursor.append(option(i,String(i)));cursor.addEventListener('change',()=>send('seek-step',{cursor:Number(cursor.value)}),{signal:ctx.signal});stepping.append(previous,next,field(w.jump,cursor));
 const roster=el('select',undefined,{'data-tx':'roster'}),page=el('p','',{role:'status'}),pageActions=el('div',undefined,{class:'tx-actions'});
 const prevPage=button(w.prevPage,()=>send('roster-page',{page:current.data.roster.page-1}),ctx.signal,{'data-tx':'page-previous'}),nextPage=button(w.nextPage,()=>send('roster-page',{page:current.data.roster.page+1}),ctx.signal,{'data-tx':'page-next'});pageActions.append(prevPage,page,nextPage);
 roster.addEventListener('change',paint,{signal:ctx.signal});
 const selection=el('div',undefined,{class:'tx-private','data-tx':'selection'}),select=button(w.select,()=>{const row=current.data.roster.rows.find(r=>r.actor===roster.value);if(row)send('select-answer',{actor:row.actor,record_version:row.summary.version});},ctx.signal,{'data-tx':'select'});
 const clear=button(w.clearSelection,()=>send('select-answer',{actor:'',record_version:0}),ctx.signal),share=button(w.share,()=>{const s=current.data.selected;if(s)send('share-answer',{actor:s.actor,record_version:s.version});},ctx.signal,{'data-tx':'share'}),unshare=button(w.clearShare,()=>send('clear-share'),ctx.signal,{'data-tx':'clear-share'});
 const selectActions=el('div',undefined,{class:'tx-actions'});selectActions.append(select,clear,share,unshare);
 panel.append(phase,counts,actions,confirmBox,stepping,error,waiting,pageActions,field(w.roster,roster),selectActions,selection);
 function paint(){if(!current)return;const d=current.data,locked=busy||confirming||!d.active;setText(phase,w.phase+': '+w[d.phase]);setText(waiting,busy?w.waiting:'');
  advance.disabled=locked||d.phase==='reveal';resume.hidden=!d.paused;resume.disabled=locked||!d.paused;reset.disabled=locked;
  stepping.hidden=d.phase!=='inspect';previous.disabled=locked||d.cursor===0;next.disabled=locked||d.cursor>=ctx.item.exercise.schedule.length;cursor.disabled=locked;if(document.activeElement!==cursor)cursor.value=String(d.cursor);
  counts.replaceChildren(el('p',w.count+': '+d.count));for(const[p,c]of Object.entries(d.counts))counts.append(el('p',w[p]+': '+c.submitted+' · '+w.analysisPending+': '+c.pending+' · '+w.analysisUnavailable+': '+c.unavailable));
  if(d.outcomes)counts.append(aggregateView(d.outcomes,w));
  const signature=key(d.roster);if(signature!==rosterKey){rosterKey=signature;const selected=roster.value;roster.replaceChildren(option('',w.choose));for(const row of d.roster.rows)roster.append(option(row.actor,'#'+row.number+' · '+['prediction','diagnosis','repair'].map(p=>w[p]+': '+w[row.summary[p]]).join(' · ')));if(d.roster.rows.some(r=>r.actor===selected))roster.value=selected;}
  setText(page,w.page+' '+(d.roster.page+1)+' / '+d.roster.pages);prevPage.disabled=locked||d.roster.page===0;nextPage.disabled=locked||d.roster.page+1>=d.roster.pages;roster.disabled=locked;
  select.disabled=locked||!roster.value;clear.disabled=locked||!d.selected;share.disabled=locked||!d.selected||d.phase!=='reveal';unshare.disabled=locked||!d.shared;
  const selected=key(d.selected);if(selected!==selectedKey){selectedKey=selected;selection.replaceChildren(el('h3',w.private),el('p',w.snapshot),answersView(d.selected,w));selection.hidden=!d.selected;}
 }
 async function send(op,payload={}){if(!current||busy||!alive)return;const token=generation;busy=true;receipt=null;error.textContent='';paint();try{const r=await ctx.dispatch(op,op==='_reset'?{}:{control_version:current.data.control_version,...payload});if(!alive||token!==generation)return;receipt=r;if(delivered(current,r)){busy=false;receipt=null;}}
  catch(e){if(!alive||token!==generation)return;busy=false;receipt=null;setText(error,commandError(e,w));}paint();}
 return{update(next){if(!alive)return;if(current&&current.epoch!==next.epoch){generation++;busy=false;receipt=null;confirming=false;confirmBox.hidden=true;error.textContent='';}current=next;if(delivered(next,receipt)){busy=false;receipt=null;}paint();},destroy(){alive=false;generation++;root.remove();}};
}
