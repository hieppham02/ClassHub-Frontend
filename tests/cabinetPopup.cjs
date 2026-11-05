const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),{spawn}=require('node:child_process'),assert=require('node:assert/strict');
const root=path.resolve('dist'),out=path.resolve('.codex-temp/cabinet-popup-preview');
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
const health={receivedAtUtc:new Date().toISOString(),ageSeconds:5,quality:'CLOCK_SYNCED',metrics:{firmwareId:'DEMO-FIRMWARE',firmwareVersion:'1',rssi:-45,heapFree:600000,heapLargest:580000,psramFree:5900000,doorOpen:false,readerInitialized:true,cameraRecentFrame:true,cameraFps100:1250,securityProvisioned:true,lastError:'CAMERA_NO_RECENT_FRAME',lastErrorAtUtc:new Date(Date.now()-60000).toISOString()}};
const fixture=[
{id:1,roomId:'DEMO201',name:'DEMO-201',building:'Tòa nhà thử nghiệm',floor:'Tầng 2',isOnline:true,status:'Trống',doorCondition:'Đóng',lockStatus:'LOCKED',borrower:'---',health},
{id:2,roomId:'DEMO202',name:'DEMO-202',building:'Tòa nhà thử nghiệm',floor:'Tầng 2',isOnline:false,status:'Đang mượn',doorCondition:'Mở',lockStatus:'LOCKED',borrower:'Người dùng thử',health:{...health,ageSeconds:600,metrics:{...health.metrics,doorOpen:true}}},
{id:3,roomId:'DEMO203',name:'DEMO-203',building:'Tòa nhà thử nghiệm',floor:'Tầng 2',isOnline:false,status:'Trống',doorCondition:'Đóng',lockStatus:'LOCKED',borrower:'---',health:null}
];
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
   const isList=request.method==='GET'&&route==='/api/admin/cabinets';
   let body=isList?fixture:{}, status=isList?200:404;
   if(route.endsWith('/rfid/options')){body={stock:[{id:10,name:'Remote test',quantity:3,version:1}],bindings:[]};status=200;}
   if(route.endsWith('/rfid/latest')){body={state:'READY',scan:{uid:'E3940127',selectionToken:'fixture-selection',expiresAtUtc:new Date(Date.now()+120000).toISOString()}};status=200;}
   if(route.endsWith('/camera/stream')){body={message:'Camera chưa được kết nối với máy chủ.'};status=503;}
   if(request.method==='POST'&&route.endsWith('/rfid/bind')){body={message:'Đã chuyển 1 thiết bị vào tủ và gắn thẻ RFID.'};status=200;boundRequest=JSON.parse(request.postData);}
   const headers=[{name:'Content-Type',value:'application/json'},{name:'Access-Control-Allow-Origin',value:origin},{name:'Access-Control-Allow-Headers',value:'authorization,content-type,x-signalr-user-agent'},{name:'Access-Control-Allow-Credentials',value:'true'},{name:'Access-Control-Allow-Methods',value:'GET,POST,OPTIONS'}];
   call('Fetch.fulfillRequest',{requestId,responseCode:request.method==='OPTIONS'?204:status,responseHeaders:headers,body:Buffer.from(request.method==='OPTIONS'?'':JSON.stringify(body)).toString('base64')}).catch(()=>{});
  }
 };
 await call('Page.enable');await call('Runtime.enable');
 await call('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
 await call('Page.addScriptToEvaluateOnNewDocument',{source:"sessionStorage.setItem('classhub-token','LOCAL-TEST-ONLY');sessionStorage.setItem('classhub-user',JSON.stringify({role:'ADMIN',name:'Kiểm tra giao diện'}));"});
 await call('Emulation.setDeviceMetricsOverride',{width:1360,height:900,deviceScaleFactor:1,mobile:false});
 await call('Page.navigate',{url:origin+'/admin/cabinets'});
 async function evaluate(expression){const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.text);return r.result.value;}
 async function until(expression){for(let n=0;n<100;n++){if(await evaluate(expression))return;await wait(100);}throw Error('Browser wait failed: '+expression);}
 await until("document.querySelectorAll('tbody tr').length===3&&document.body.innerText.includes('DEMO-201')");
 assert.equal(await evaluate("document.querySelectorAll('[role=dialog]').length"),0);
 assert.equal(await evaluate("document.body.innerText.includes('Sức khỏe thiết bị')"),false);
 assert.equal(await evaluate("Array.from(document.querySelectorAll('button[aria-haspopup=dialog]')).map(x=>x.textContent.trim()).join(',')"),'DEMO-201,DEMO-202,DEMO-203');
 assert.equal(await evaluate("document.body.innerText.includes('Dữ liệu cũ/mất liên lạc')||document.body.innerText.includes('Chưa có telemetry')"),false);
 const before=await evaluate("Array.from(document.querySelectorAll('tbody tr')).map(x=>x.getBoundingClientRect().height)");
 assert.ok(await evaluate("document.querySelectorAll('tbody tr')[1].innerText.includes('Đang mượn')&&document.querySelectorAll('tbody tr')[1].innerText.includes('Mở')"));
 assert.ok(await evaluate("document.querySelectorAll('tbody tr')[2].innerText.includes('Đóng')"));
 fs.writeFileSync(path.join(out,'table.png'),Buffer.from((await call('Page.captureScreenshot',{format:'png'})).data,'base64'));
 await evaluate("Array.from(document.querySelectorAll('button')).find(x=>x.getAttribute('aria-haspopup')==='dialog').click()");
 await until("!!document.querySelector('[role=dialog]')");
 assert.ok(await evaluate("document.querySelector('[role=dialog]').innerText.includes('DEMO-201')"));
 assert.equal(await evaluate("document.querySelectorAll('[role=dialog] section[aria-label]').length"),3);
 assert.ok(await evaluate("document.querySelector('[role=dialog]').innerText.includes('Lỗi gần nhất đã ghi nhận')"));
 assert.equal(await evaluate("document.querySelector('[role=dialog]').innerText.includes('MiB')"),false);
 await evaluate("Array.from(document.querySelectorAll('button')).find(x=>x.textContent.trim()==='Thiết bị & RFID').click()");
 await until("Array.from(document.querySelectorAll('button')).some(x=>x.textContent.trim()==='Chọn thẻ này')");
 assert.ok(await evaluate("Array.from(document.querySelectorAll('button')).find(x=>x.textContent.includes('Xác nhận ·')).disabled"));
 await evaluate("Array.from(document.querySelectorAll('button')).find(x=>x.textContent.trim()==='Chọn thẻ này').click()");
 await evaluate("(()=>{const x=document.querySelector('select[id^=stock-]');x.value='10';x.dispatchEvent(new Event('change',{bubbles:true}));})()");
 await until("!Array.from(document.querySelectorAll('button')).find(x=>x.textContent.includes('Xác nhận ·')).disabled");
 await evaluate("Array.from(document.querySelectorAll('button')).find(x=>x.textContent.includes('Xác nhận ·')).click()");
 await until("document.querySelector('[role=dialog]').innerText.includes('Đã chuyển 1 thiết bị')");
 assert.deepEqual(boundRequest,{selectionToken:'fixture-selection',stockEquipmentId:10,stockVersion:1});
 fs.writeFileSync(path.join(out,'rfid-desktop.png'),Buffer.from((await call('Page.captureScreenshot',{format:'png'})).data,'base64'));
 await evaluate("Array.from(document.querySelectorAll('button')).find(x=>x.textContent.trim()==='Tổng quan').click()");
 await evaluate("Array.from(document.querySelectorAll('button')).find(x=>x.textContent.trim()==='Xem camera').click()");
 await until("document.querySelector('[role=dialog]').innerText.includes('Camera chưa được kết nối với máy chủ.')");
 await evaluate("Array.from(document.querySelectorAll('button')).find(x=>x.textContent.trim()==='Đóng camera').click()");
 assert.deepEqual(await evaluate("Array.from(document.querySelectorAll('tbody tr')).map(x=>x.getBoundingClientRect().height)"),before);
 fs.writeFileSync(path.join(out,'popup-desktop.png'),Buffer.from((await call('Page.captureScreenshot',{format:'png'})).data,'base64'));
 await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape'});
 await until("!document.querySelector('[role=dialog]')");
 assert.equal(await evaluate("document.activeElement.textContent.trim()"),'DEMO-201');
 await evaluate("Array.from(document.querySelectorAll('button')).filter(x=>x.getAttribute('aria-haspopup')==='dialog')[2].click()");
 await until("!!document.querySelector('[role=dialog]')");
 assert.ok(await evaluate("document.querySelector('[role=dialog]').innerText.includes('Chưa có thông tin thiết bị')"));
 await evaluate("document.querySelector('[aria-label=\"Đóng hộp thoại\"]').click()");
 await until("!document.querySelector('[role=dialog]')");
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 await evaluate("Array.from(document.querySelectorAll('button')).find(x=>x.getAttribute('aria-haspopup')==='dialog').click()");
 await until("!!document.querySelector('[role=dialog]')");
 assert.ok(await evaluate("(()=>{const r=document.querySelector('[role=dialog]').getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight})()"));
 fs.writeFileSync(path.join(out,'popup-mobile.png'),Buffer.from((await call('Page.captureScreenshot',{format:'png'})).data,'base64'));
 console.log('PASS: headless browser: clickable cabinet names without extra health links; grouped metrics without memory, camera errors, explicit RFID selection and stock confirmation, error history, compact rows, Escape/focus return, no-data popup and mobile bounds.');
 console.log('Screenshots: '+out);
}finally{
 if(call)await call('Browser.close').catch(()=>{});
 if(ws)ws.close();
 edge.kill();server.closeAllConnections();await new Promise(r=>server.close(r));
}
})().catch(e=>{console.error(e);process.exitCode=1;});
