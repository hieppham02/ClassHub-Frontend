const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),{spawn}=require('node:child_process'),assert=require('node:assert/strict');
const root=path.resolve('dist'),out=path.resolve('.codex-temp/iot-analysis-preview');
fs.mkdirSync(out,{recursive:true});
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const server=http.createServer((req,res)=>{
  const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  let file=path.resolve(root,'.'+pathname);
  if(!file.startsWith(root+path.sep)&&file!==root){res.writeHead(403);return res.end();}
  if(!fs.existsSync(file)||fs.statSync(file).isDirectory())file=path.join(root,'index.html');
  const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.png':'image/png','.svg':'image/svg+xml'};
  res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream'});res.end(fs.readFileSync(file));
});
let analysis={state:'ANOMALY',summary:'Cần kiểm tra phòng',source:'MOCK',usageContext:'AFTER_USE',measuredAt:new Date().toISOString(),contextBasis:'Ngữ cảnh tool',modelVersion:'test',sampleId:1,limitation:'Mô hình dữ liệu tổng hợp',findings:[{code:'POWER_AFTER_USE',severity:'warning',title:'Có dấu hiệu còn thiết bị sử dụng điện',detail:'Kiểm tra tải điện tổng phòng.',score:98},{code:'HIGH_TEMPERATURE',severity:'critical',title:'Nhiệt độ cao bất thường',detail:'Kiểm tra thông gió.',score:99}]};
(async()=>{
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const origin='http://127.0.0.1:'+server.address().port;
const profile=path.join(out,'edge-profile-'+Date.now());
const edge=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
let ws,call,boundRequest;
try{
 const portFile=path.join(profile,'DevToolsActivePort');
 for(let n=0;n<100&&!fs.existsSync(portFile);n++)await wait(100);
 assert.ok(fs.existsSync(portFile),'Headless Edge started');
 const port=fs.readFileSync(portFile,'utf8').split('\n')[0];
 const targets=await (await fetch('http://127.0.0.1:'+port+'/json/list')).json();
 const target=targets.find(t=>t.type==='page');
 ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
 let id=0;const pending=new Map();
 call=(method,params={})=>new Promise((resolve,reject)=>{
  const current=++id;const timer=setTimeout(()=>{pending.delete(current);reject(Error('CDP timeout '+method));},30000);
  pending.set(current,{resolve,reject,timer});ws.send(JSON.stringify({id:current,method,params}));
 });
 ws.onmessage=event=>{
  const message=JSON.parse(event.data);
  if(message.id){const p=pending.get(message.id);if(p){clearTimeout(p.timer);pending.delete(message.id);message.error?p.reject(Error(message.error.message)):p.resolve(message.result);}return;}
  if(message.method==='Fetch.requestPaused'){
   const {requestId,request}=message.params;
   if(request.url.startsWith(origin+'/')){call('Fetch.continueRequest',{requestId}).catch(()=>{});return;}
   const route=new URL(request.url).pathname;
   let body={items:[],samples:[],totalItems:0};
   if(route.endsWith('/admin/assets')) body={rooms:[{id:'R1',name:'Phòng demo',locationType:'ROOM',buildingId:'B1',building:'Tòa A',floor:1}],catalogs:[],equipment:[],nodes:[{id:1,nodeCode:'DEMO_R1',roomId:'R1',name:'Node demo',needsAttention:true,dataSource:'MOCK',status:'ONLINE',lastSeenAt:new Date().toISOString(),readings:[{metric:'temperature',value:41,quality:'GOOD'},{metric:'humidity',value:48,quality:'GOOD'},{metric:'current',value:12,quality:'GOOD'}]}]};
   if(route.endsWith('/damage-reports'))body=[];
   if(route.endsWith('/power'))body={state:'MOCK'};
   if(route.endsWith('/analysis')) body=analysis;
   call('Fetch.fulfillRequest',{requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'},{name:'Access-Control-Allow-Origin',value:'*'},{name:'Access-Control-Allow-Headers',value:'*'}],body:Buffer.from(JSON.stringify(body)).toString('base64')}).catch(()=>{});
  }
 };

 await call('Page.enable');await call('Runtime.enable');
 await call('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
 await call('Page.addScriptToEvaluateOnNewDocument',{source:"sessionStorage.setItem('classhub-token','LOCAL-TEST-ONLY');sessionStorage.setItem('classhub-user',JSON.stringify({role:'ADMIN',name:'Test'}));"});
 async function evaluate(expression){const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.text);return r.result.value;}
 async function until(expression){for(let n=0;n<100;n++){if(await evaluate(expression))return;await wait(100);}throw Error('Browser wait failed: '+expression);}
 for(const width of [1360,390]){
  await call('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<500});
  await call('Page.navigate',{url:origin+'/admin/assets?tab=iot'});
  await until("document.body.innerText.includes('Nhiệt độ cao bất thường')");
  assert.ok(await evaluate("document.body.innerText.includes('Có dấu hiệu còn thiết bị sử dụng điện')"));
  assert.ok(await evaluate("Array.from(document.querySelectorAll('.iot-status-tile')).some(x=>x.innerText.includes('Cảnh báo')&&x.innerText.includes('1'))"));
  await evaluate("Array.from(document.querySelectorAll('.iot-status-tile')).find(x=>x.innerText.includes('Cảnh báo')&&x.getAttribute('aria-pressed')!=='true')?.click()");
  await until("document.querySelector('.iot-status-tile[aria-pressed=true]')?.innerText.includes('Cảnh báo')");
  assert.ok(await evaluate("document.querySelector('.iot-node-card').innerText.includes('Nhiệt độ cao bất thường')"));
  assert.equal(await evaluate("/mô phỏng|giả định|thử nghiệm/i.test(document.body.innerText)"),false);
  assert.ok(await evaluate("document.documentElement.scrollWidth<=innerWidth+2"));
  fs.writeFileSync(path.join(out,'iot-'+width+'.png'),Buffer.from((await call('Page.captureScreenshot',{format:'png'})).data,'base64'));
 }
 analysis={state:'UNAVAILABLE',reason:'Chưa có số đo mới và đồng bộ thời gian để phân tích.'};
 await call('Page.reload');
 await until("document.body.innerText.includes('Chưa có số đo mới và đồng bộ thời gian để phân tích.')");
 assert.equal(await evaluate("document.body.innerText.includes('Cần kiểm tra phòng')"),false);
 console.log('PASS AI panel shows both anomalies, warning count/filter, simplified labels, stale state; desktop/mobile no horizontal overflow.');
}finally{if(ws)ws.close();edge.kill();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
