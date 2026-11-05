import assert from 'node:assert/strict'
import { CameraFrames } from '../src/utils/cameraFrames.js'
const data = Uint8Array.from([4,0,0,0,255,216,255,217,4,0,0,0,255,216,255,217])
for (let split=0;split<=data.length;split++) {
  const decoder=new CameraFrames()
  const result=[...decoder.push(data.slice(0,split)),...decoder.push(data.slice(split))]
  assert.equal(result.length,2)
  assert.deepEqual([...result[0]],[255,216,255,217])
}
const decoder=new CameraFrames()
let count=0
for (const value of data) count+=decoder.push(Uint8Array.of(value)).length
assert.equal(count,2)
assert.throws(()=>new CameraFrames().push(Uint8Array.of(255,255,255,255)))
assert.throws(()=>new CameraFrames().push(Uint8Array.of(0,0,0,0)))
console.log('PASS: fragmented, combined, bytewise and malformed camera stream frames')
