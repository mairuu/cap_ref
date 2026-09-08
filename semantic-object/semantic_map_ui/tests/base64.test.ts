import { describe, it, expect } from 'vitest'
import { decodeBase64 } from '../src/utils/base64'

describe('decodeBase64', () => {
  it('decodes a known base64 string correctly', () => {
    // "ABC" in base64 is "QUJD"
    const decoded = decodeBase64('QUJD')
    expect(decoded).toBeInstanceOf(Uint8Array)
    expect(decoded[0]).toBe(65) // 'A'
    expect(decoded[1]).toBe(66) // 'B'
    expect(decoded[2]).toBe(67) // 'C'
  })

  it('decodes occupancy values correctly', () => {
    // encode bytes [0, 100, 255] — free, occupied, unknown
    const raw = new Uint8Array([0, 100, 255])
    const b64 = btoa(String.fromCharCode(...raw))
    const decoded = decodeBase64(b64)
    expect(decoded[0]).toBe(0)   // free
    expect(decoded[1]).toBe(100) // occupied
    expect(decoded[2]).toBe(255) // unknown (was -1 int8 → 255 uint8)
  })

  it('returns empty array for empty string', () => {
    expect(decodeBase64('').length).toBe(0)
  })
})
