// Length-prefixed JPEG frames; chunks may split a header or contain several frames.
export class CameraFrames {
  constructor() { this.bytes = new Uint8Array(0) }
  push(chunk) {
    const next = new Uint8Array(this.bytes.length + chunk.length)
    next.set(this.bytes); next.set(chunk, this.bytes.length); this.bytes = next
    const frames = []
    while (this.bytes.length >= 4) {
      const length = new DataView(this.bytes.buffer, this.bytes.byteOffset, 4).getUint32(0, true)
      if (length < 4 || length > 640 * 480 * 2) throw new Error('Khung camera không hợp lệ.')
      if (this.bytes.length < length + 4) break
      frames.push(this.bytes.slice(4, length + 4)); this.bytes = this.bytes.slice(length + 4)
    }
    return frames
  }
}
