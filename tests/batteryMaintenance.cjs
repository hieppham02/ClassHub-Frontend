const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const component = fs.readFileSync(path.join(__dirname, '../src/views/admin/BatteryMaintenanceView.vue'), 'utf8');
const source = component.split('<script setup>')[1].split('</script>')[0].replace(/^import .*$/gm, '');
const deferred = () => { let resolve, reject; const promise = new Promise((a,b) => { resolve=a; reject=b; }); return {promise,resolve,reject}; };
const row = id => ({profile:{id,equipmentId:7,version:3,enabled:true,batteryType:'AA',batteryCount:2},equipmentName:'Micro',assessment:{priority:'UNKNOWN'}});
const emptyList = {items:[],total:0,inspectionFreshHours:168,assessedAtUtc:'2026-11-05T00:00:00Z'};
function setup(api) {
  const ctx = {api, URLSearchParams, Date, Number, String, Set,
    ref:value => ({value}), reactive:value => value, computed:fn => ({get value(){return fn();}}),
    onMounted:()=>{},onUnmounted:()=>{}};
  vm.createContext(ctx);
  vm.runInContext(source + '\nglobalThis.state={items,total,selected,needsReload,busy,modal,options,optionsReady,profileForm,profileNeedsReload,inspection,service,tagOptions};globalThis.actions={loadList,loadDetail,saveEntry,saveProfile,openProfile};',ctx);
  return ctx;
}
let checks=0;
function check(value,name){assert.ok(value,name);checks++;console.log('PASS: '+name);}
(async()=>{
  const first=deferred(),second=deferred();let calls=0;
  const c=setup({get:()=>++calls===1?first.promise:second.promise});
  const a=c.actions.loadList(1),b=c.actions.loadList(2);
  second.resolve({...emptyList,items:[row(2)],total:1});await b;
  first.resolve({...emptyList,items:[row(1)],total:1});await a;
  check(c.state.items.value[0].profile.id===2,'Stale list response cannot replace current filter/page');

  const pending={};
  const d=setup({get:url=>{pending[url]=deferred();return pending[url].promise;}});
  const da=d.actions.loadDetail(1),db=d.actions.loadDetail(2);
  for(const id of [2,1]) {
    pending['/admin/batteries/'+id].resolve(row(id));
    pending['/admin/batteries/'+id+'/inspections'].resolve({items:[],nextBefore:null});
    pending['/admin/batteries/'+id+'/services'].resolve({items:[],nextBefore:null});
    await (id===2?db:da);
  }
  check(d.state.selected.value.profile.id===2,'Stale detail cannot change the selected microphone');

  let posts=0;
  const e=setup({post:async()=>{posts++;throw new Error('network lost');}});
  e.state.selected.value=row(5);
  Object.assign(e.state.inspection,{at:'2026-11-05T08:00',batteryState:'LOW',operationState:'NORMAL',voltageV:'',batteryPercent:'',sessionId:''});
  await e.actions.saveEntry('inspections');
  check(e.state.needsReload.value,'Uncertain save requires history reload');
  await e.actions.saveEntry('inspections');
  check(posts===1,'Uncertain inspection is never automatically or repeatedly sent');

  const post=deferred();let payload;
  const f=setup({
    post:(url,body)=>{posts++;payload={url,body};return post.promise;},
    get:async url=>url.includes('?')?emptyList:url.endsWith('/inspections')||url.endsWith('/services')?{items:[],nextBefore:null}:row(9)
  });
  posts=0;f.state.selected.value=row(9);
  Object.assign(f.state.service,{at:'2026-11-05T08:00',action:'RECHARGE',rechargeCompleted:'false',outcome:'NORMAL',confirmedCause:'UNKNOWN',batteryCount:'2',batteryType:'AA',note:''});
  const save=f.actions.saveEntry('services');
  await f.actions.saveEntry('services');
  check(posts===1,'Concurrent clicks cannot duplicate service request');
  check(payload.url==='/admin/batteries/9/services'&&payload.body.version===3,'Service targets the selected profile and its current version');
  check(payload.body.rechargeCompleted===false,'Partial recharge remains explicitly incomplete');
  check(!('dataSource' in payload.body),'UI cannot mark generated evidence as real through a source field');
  post.resolve({});await save;
  check(f.state.selected.value.profile.id===9&&!f.state.needsReload.value,'Successful save reloads that microphone and releases controls');

  const g=setup({post:async()=>{throw new Error('lost response');}});
  g.state.optionsReady.value=true;g.state.modal.value=true;g.state.editing=false;
  Object.assign(g.state.profileForm,{equipmentId:7,assetCode:'MIC-001',currentRfidTagId:'',batteryCount:'',rechargeable:''});
  await g.actions.saveProfile();
  check(g.state.profileNeedsReload.value,'Uncertain profile creation requires verification before another submit');

  const h=setup({});
  h.state.selected.value=row(9);h.state.profileForm.equipmentId=7;
  h.state.options.value={equipment:[],tags:[
    {id:1,equipmentId:7,profileId:null},
    {id:2,equipmentId:8,profileId:null},
    {id:3,equipmentId:7,profileId:10},
    {id:4,equipmentId:7,profileId:9}
  ]};
  check(h.state.tagOptions.value.map(t=>t.id).join(',')==='1,4','RFID choices exclude other equipment and occupied profiles, retain current binding');
  console.log('PASS: '+checks+' battery UI workflow checks');
})().catch(error=>{console.error(error);process.exitCode=1;});
