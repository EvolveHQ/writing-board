// Exercise the actual offline board script; this complements rendered browser review.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const read = file => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
const plain = value => JSON.parse(JSON.stringify(value));
const html = fs.readFileSync(path.join(root, 'web/board.html'), 'utf8');
const schemaText = html.match(/<script id="packet-schema" type="application\/json">([\s\S]*?)<\/script>/)[1];
assert.deepEqual(JSON.parse(schemaText), read('schemas/story.schema.json'), 'embedded schema must match its source');
const script = html.match(/<script>\r?\n([\s\S]*?)<\/script>/)[1];
new vm.Script(script);
const pure = script.slice(0, script.indexOf("$('open').addEventListener"));
const base = read('examples/rainy-day/stories/pip-and-the-rain-map.json');
base.extensions.test_metadata = {nested:['keep', {accent:'č · á'}]};
const project = {bundle_version:1, base_revision:1, project:read('examples/rainy-day/project.json'), guidelines:read('examples/rainy-day/guidelines.json'), bible:read('examples/rainy-day/bible.json'), stories:[base]};
project.project.extensions.user_metadata = {preserve:true};

class NodeStub {
  constructor(tag='text',text=''){this.tag=tag;this.text=text;this.children=[];this.attributes={};this.classList={add(){},toggle(){}};}
  append(...children){this.children.push(...children);}
  setAttribute(key,value){this.attributes[key]=value;}
  addEventListener(){}
  replaceChildren(...children){this.children=children;}
}
function session(data=base,bundle=null){
  const markers={'packet-schema':schemaText,'embedded-packets':'[]','embedded-project':JSON.stringify(bundle||{})};
  const context=vm.createContext({document:{getElementById:id=>({textContent:markers[id]||'',classList:{toggle(){}},replaceChildren(){},setAttribute(){}}),querySelector:()=>null,querySelectorAll:()=>[],createElement:tag=>new NodeStub(tag),createTextNode:text=>new NodeStub('text',text)},JSON,Number,Map,Set,Array,Object,String,RegExp,Node:NodeStub,Blob,URL,setTimeout,window:{confirm:()=>true}});
  vm.runInContext(pure,context);context.input=plain(data);
  vm.runInContext("render=()=>{};updateHeading=()=>{};message=(text,kind)=>{globalThis.lastMessage=text;globalThis.lastKind=kind;};refreshBoardPicker=()=>{};download=(data,name)=>{globalThis.result=clone(data);globalThis.filename=name;};",context);
  vm.runInContext(bundle?'setupBoards()':"loadPacket(input,'probe.json')",context);
  return {run:code=>vm.runInContext(code,context),state:context,export(){vm.runInContext('exportPacket()',context);return plain(context.result);}};
}

const origin=base.revision;
const draft=session();draft.run("touch();packet.beats[0].action='An edited action';");
const downloaded=draft.export();
assert.equal(downloaded.revision,origin+1);assert.equal(downloaded.extensions.workbench_base_revision,origin);
assert.deepEqual(downloaded.extensions.test_metadata,base.extensions.test_metadata);
assert(downloaded.reviews.every(r=>r.status==='stale'));assert(downloaded.proofs.every(r=>r.status==='stale'));assert.equal(downloaded.page_plan.status,'needs_review');
const resume=session(downloaded);assert.deepEqual(resume.export(),downloaded);
resume.run("touch();packet.beats[0].consequence='A later change';touch();");
assert.equal(resume.export().revision,origin+1,'resuming a downloaded draft does not rebase it');
for(const invalid of [0,-1,1.5,'1',origin+2]){const bad=plain(downloaded);bad.extensions.workbench_base_revision=invalid;assert.throws(()=>session(bad),/Invalid workbench base revision/);}
const overlarge=plain(base);overlarge.page_plan.interior_pages=2001;assert.throws(()=>session(overlarge),/2,000 interior pages/);
const maxRevision=plain(base);maxRevision.revision=Number.MAX_SAFE_INTEGER;delete maxRevision.extensions.workbench_base_revision;
const limit=session(maxRevision);assert.throws(()=>limit.run('touch()'),/Revision limit/);assert.equal(limit.run('dirty'),false);

const order=session();const chronology=base.beats.map(b=>[b.id,b.chronology]);
order.run('moveBeat(packet.beats[0].id,1)');
const moved=order.export();assert.deepEqual(moved.beats.map(b=>[b.id,b.chronology]).sort(),chronology.sort());
assert.deepEqual(moved.page_plan.story_spreads.flatMap(s=>s.beat_ids),moved.beats.map(b=>b.id));
assert.equal(order.run('structuralChecks().issues.length'),0);
order.run("applyPurposeEdit({...purposeValues(),teaching_goal:'Follow a visible clue',theme:'Trying together'})");
assert.equal(order.export().purpose.teaching_goal,'Follow a visible clue');assert.equal(order.export().premise.theme,'Trying together');

const bundle=plain(project);const second=plain(base);second.id='second-story';second.title='Second story';bundle.stories.push(second);
const ui=session(base,bundle);
assert.equal(ui.run('boards.size'),2);assert.equal(ui.run('contextDirty'),false);
ui.run("touch();packet.beats[0].action='First board change';selectBoard('board-2');touch();packet.beats[0].action='Second board change';selectBoard('board-1');");
assert.equal(ui.run('packet.beats[0].action'),'First board change');assert.equal(ui.run('hasUnsavedBoards()'),true);
ui.run("applyContextPart('guidelines',{...projectBundle.guidelines,voice:['A revised voice']})");
assert.equal(ui.run('contextDirty'),true);
const contextExport=plain(ui.run('bundleForExport()'));
assert.equal(contextExport.base_revision,1);assert.equal(contextExport.project.revision,1);
assert.equal(contextExport.stories[1].beats[0].action,'Second board change');
assert(contextExport.stories.every(s=>s.reviews.every(r=>r.status==='stale')&&s.proofs.every(p=>p.status==='stale')&&s.page_plan.status==='needs_review'));
assert.deepEqual(contextExport.project.extensions.user_metadata,{preserve:true});
ui.export();assert.equal(ui.run('contextDirty'),true,'saving a packet cannot mark shared context exported');
ui.run('exportProject()');assert.equal(ui.run('contextDirty'),false);assert.equal(ui.run('hasUnsavedBoards()'),false);
assert.equal(ui.state.result.stories.length,2);
const beforeNoop=JSON.stringify(ui.run('bundleForExport()'));
ui.run("applyContextPart('guidelines',clone(projectBundle.guidelines))");
assert.equal(ui.run('contextDirty'),false);assert.equal(JSON.stringify(ui.run('bundleForExport()')),beforeNoop);

const emptyBundle=plain(project);emptyBundle.stories=[];emptyBundle.bible.characters=[];emptyBundle.bible.relationships=[];emptyBundle.bible.timeline=[];
const empty=session(base,emptyBundle);assert.equal(empty.run('packet'),null);assert.equal(empty.run('boards.size'),0);
empty.run("applyCharacterEdit(null,{id:'hero',name:'Hero',summary:'A curious child',appearance:'',backstory:'',want:'',need:'',voice:'',speech_mode:'unspecified',facts:[],extensions:{keep:'yes'}})");
assert.equal(empty.run('projectBundle.bible.characters.length'),1);assert.equal(empty.run('contextDirty'),true);
empty.run("applyCharacterEdit('hero',{...projectBundle.bible.characters[0],backstory:'Collects interesting leaves.'})");
assert.equal(empty.run("projectBundle.bible.characters[0].extensions.keep"),'yes');
const beforeBad=JSON.stringify(empty.run('projectBundle'));
assert.throws(()=>empty.run("applyCharacterEdit('hero',{...projectBundle.bible.characters[0],facts:[{id:'claim',statement:'A claim',status:'established',source_ref:null}]})"),/source reference/);
assert.equal(JSON.stringify(empty.run('projectBundle')),beforeBad,'invalid context edits are atomic');
assert.throws(()=>empty.run("applyCharacterEdit('hero',{...projectBundle.bible.characters[0],id:'renamed'})"),/stable/);
empty.run('exportProject()');assert.equal(empty.state.result.stories.length,0);assert.equal(empty.state.result.bible.characters[0].backstory,'Collects interesting leaves.');

ui.run("importPacket(clone(input),'duplicate.json')");
assert.equal(ui.run('boards.size'),3,'packet imports never overwrite a managed board');
assert.throws(()=>ui.run('bundleForExport()'),/Two open boards share ID/);
assert.throws(()=>ui.run("importPacket({},'malformed.json')"),/Cannot open/);assert.equal(ui.run('boards.size'),3);
ui.run('removeImportedBoard()');assert.equal(ui.run('boards.size'),2);assert.equal(ui.run('bundleForExport().stories.length'),2);

const unsupported=plain(base);unsupported.user_added_unknown={nested:'preserve'};
const unknown=session(unsupported);unknown.run('touch()');assert.deepEqual(unknown.export().user_added_unknown,{nested:'preserve'});
assert(unknown.run('structuralChecks().unknown.length')>0,'unknown fields are visible, not discarded');
const hostile='<img src=x onerror=alert(1)></script><script>attack()</script>';
unknown.state.hostile=hostile;const node=unknown.run("e('p',{},hostile)");assert.equal(node.children.length,1);assert.equal(node.children[0].tag,'text');assert.equal(node.children[0].text,hostile);
assert.throws(()=>unknown.run("parseJSON('{\"n\":9007199254740993}')"),/Unsafe number/);
assert(!/\b(?:localStorage|sessionStorage|indexedDB|fetch)\s*[.(]/.test(script));assert(!/\.innerHTML\s*=/.test(script));
assert(html.includes("connect-src 'none'"));

async function saveChecks(){
  const save=session();save.run('touch()');await save.run('savePacket()');assert.equal(save.run('dirty'),false);assert.equal(save.run('saveNote'),'Download requested');
  save.run("touch();window.showSaveFilePicker=async()=>{throw Object.assign(new Error('cancel'),{name:'AbortError'})}");await save.run('savePacket()');assert.equal(save.run('dirty'),true);
  save.run("window.showSaveFilePicker=async()=>({createWritable:async()=>({write:async()=>{throw new Error('disk full')},close:async()=>{},abort:async()=>{globalThis.aborted=true}})})");await save.run('savePacket()');assert.equal(save.run('dirty'),true);assert.equal(save.state.aborted,true);
  save.run("window.showSaveFilePicker=async()=>({name:'chosen.json',createWritable:async()=>({write:async text=>{globalThis.savedText=text},close:async()=>{}})})");await save.run('savePacket()');assert.equal(save.run('dirty'),false);assert.equal(JSON.parse(save.state.savedText).extensions.workbench_base_revision,origin);
  save.run("touch();window.showSaveFilePicker=async()=>({createWritable:async()=>({write:async()=>{packet.beats[0].action='Edit during save';touch()},close:async()=>{}})})");await save.run('savePacket()');assert.equal(save.run('dirty'),true,'a later edit must not be marked saved by an earlier write');
  console.log('PASS: offline board state, context edits, empty workspace, bundles, stable IDs, stale evidence, unknown metadata, secure text rendering, and explicit save failure/concurrency paths.');
}
saveChecks().catch(error=>{console.error(error);process.exitCode=1;});
