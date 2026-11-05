import assert from 'node:assert/strict'
import { createDemoStatuses } from '../src/utils/iotDemoStatus.js'
const metrics=[{key:'temperature'},{key:'humidity'},{key:'current'}]
const node=(id,t,status='ONLINE')=>({id,dataSource:'MOCK',status,readings:[{metric:'temperature',quality:'GOOD',value:t},{metric:'humidity',quality:'GOOD',value:60}]})
const map=createDemoStatuses([node(1,28),node(2,36),node(3,41),node(4,41,'OFFLINE')],[],metrics)
assert.equal(map.get('1:temperature'),'stable')
assert.equal(map.get('2:temperature'),'warning')
assert.equal(map.get('3:temperature'),'critical')
assert.equal(map.has('4:temperature'),false)
assert.equal(map.get('1:humidity'),'stable')
assert.equal(map.get('1:current'),undefined)
console.log('PASS: displayed telemetry status follows temperature/humidity values and freshness, not random node placement')
