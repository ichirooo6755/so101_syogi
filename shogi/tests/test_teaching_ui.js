// Exercise the teaching choices without a browser, camera, or motor.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class Element {
  constructor(tag='div') {
    this.tag=tag; this.children=[]; this.value=''; this.hidden=false; this.disabled=false;
    this.open=false; this.textContent=''; this.style={}; this.classList={toggle(){}};
  }
  append(child) { this.children.push(child); if(this.tag==='select' && this.children.length===1) this.value=child.value; }
  replaceChildren(...children) { this.children=[...children]; if(this.tag==='select') this.value=children[0]?.value||''; }
  get options() { return this.children; }
  scrollIntoView() {}
}

async function main() {
  const elements=new Map();
  const selects=new Set(['side','cameraSource','usbPort','teachSquare','teachOperation','teachFollower','teachLeader']);
  const get=id=>{if(!elements.has(id))elements.set(id,new Element(selects.has(id)?'select':'div'));return elements.get(id)};
  get('side').value='white';get('cameraSource').value='usb';get('teachOperation').value='pick';
  const state={board:'9/9/9/9/9/9/9/9/9',game_over:false,ai_turn:false,auto:{status:'idle'},
    pending:null,teaching:{status:'idle'},simulation:{status:'idle'},
    learned_teaching:{side:'white',candidates:[{square:'9c',operation:'pick'}]}};
  const requests=[];
  const context={document:{querySelector:s=>get(s.slice(1)),createElement:tag=>new Element(tag)},
    location:{pathname:'/test-token'},confirm:()=>true,setTimeout:()=>0,
    fetch:async(_url,options)=>{
      const body=JSON.parse(options.body);requests.push(body);
      let data=state;
      if(body.action==='usb_ports')data={ports:[]};
      if(body.action==='teaching_ports')data={ports:[{device:'/dev/cu.f',description:'Follower'},{device:'/dev/cu.l',description:'Leader'}]};
      if(body.action==='auto_stop')state.auto={status:'paused'};
      if(body.action==='teach_begin')state.teaching={status:'recording',id:'sample',square:body.square,
        side:body.side,mode:body.mode,operation:body.operation,recorded:0,total:4,next:'姿勢'};
      return {ok:true,json:async()=>data};
    }};
  vm.createContext(context);
  const html=fs.readFileSync(path.join(__dirname,'../app/index.html'),'utf8');
  const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
  vm.runInContext(script,context);
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(get('learnedChoices').children.length,1);
  await get('learnedChoices').children[0].onclick();
  assert.equal(get('teachSquare').value,'9c');
  assert.equal(get('teachOperation').value,'pick');

  state.pending={usi:'9c9d',reach:'計画失敗',teach_suggestions:[{square:'9d',operation:'place'}]};
  context.render(state);
  const suggestion=get('choices').children.find(x=>x.textContent.includes('置き方'));
  assert.ok(suggestion);
  await suggestion.onclick();
  assert.equal(state.auto.status,'paused');
  assert.equal(get('teachSquare').value,'9d');
  assert.equal(get('teachOperation').value,'place');
  assert.equal(get('teaching').open,true);
  await get('teachBegin').onclick();
  const begin=requests.findLast(x=>x.action==='teach_begin');
  assert.equal(begin.mode,'leader');assert.equal(begin.square,'9d');assert.equal(begin.operation,'place');
  assert.equal(get('teachCapture').disabled,false);
  get('teachSquare').value='3c';get('teachSquare').onchange();
  assert.equal(get('teachCapture').disabled,true);
  console.log('Teaching UI choices and stale-session protection OK');
}
main().catch(e=>{console.error(e);process.exitCode=1});
