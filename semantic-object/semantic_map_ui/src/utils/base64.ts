import type { OccupancyGrid } from '../state/types'

// Occupancy values: -1 (unknown, stored as 255 in uint8), 0 (free), 100 (occupied)
const COLOR_UNKNOWN = [100, 100, 100, 255] as const
const COLOR_FREE    = [240, 240, 240, 255] as const
const COLOR_OCC     = [26,  26,  26,  255] as const

export function decodeBase64(b64: string): Uint8Array {
  const bin = atob(b64)
  const out = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i)
  return out
}

export function buildOffscreenCanvas(grid: OccupancyGrid): OffscreenCanvas {
  const { width, height, data: b64 } = grid
  const raw = decodeBase64(b64)

  const canvas = new OffscreenCanvas(width, height)
  const ctx = canvas.getContext('2d')!
  const img = ctx.createImageData(width, height)

  for (let i = 0; i < raw.length; i++) {
    const val = raw[i]
    // uint8 wrapping: -1 as signed int8 comes through as 255 in the uint8 array
    const color = val === 255 ? COLOR_UNKNOWN : val === 0 ? COLOR_FREE : COLOR_OCC
    const px = i * 4
    img.data[px]     = color[0]
    img.data[px + 1] = color[1]
    img.data[px + 2] = color[2]
    img.data[px + 3] = color[3]
  }

  ctx.putImageData(img, 0, 0)
  return canvas
}
