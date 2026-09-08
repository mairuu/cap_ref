import type { ViewTransform } from '../../state/types'

export interface ScreenPoint { sx: number; sy: number }
export interface WorldPoint  { wx: number; wy: number }

// World: x-right, y-up (metres)
// Screen: x-right, y-down (pixels), origin at canvas top-left
//
//   sx = panX + wx * scale
//   sy = panY - wy * scale     ← y flip

export function worldToScreen(wx: number, wy: number, v: ViewTransform): ScreenPoint {
  return {
    sx: v.panX + wx * v.scale,
    sy: v.panY - wy * v.scale,
  }
}

export function screenToWorld(sx: number, sy: number, v: ViewTransform): WorldPoint {
  return {
    wx: (sx - v.panX) / v.scale,
    wy: (v.panY - sy) / v.scale,
  }
}

// Zoom centred on a screen-space cursor position.
// Returns a new ViewTransform that keeps the cursor's world point fixed.
export function zoomAt(
  v: ViewTransform,
  cursorSx: number,
  cursorSy: number,
  factor: number,
): ViewTransform {
  const newScale = Math.max(10, Math.min(500, v.scale * factor))
  const ratio = newScale / v.scale
  return {
    scale: newScale,
    panX: cursorSx - ratio * (cursorSx - v.panX),
    panY: cursorSy - ratio * (cursorSy - v.panY),
  }
}

// Normalises angle to [-π, π]
export function normaliseAngle(a: number): number {
  while (a > Math.PI)  a -= 2 * Math.PI
  while (a < -Math.PI) a += 2 * Math.PI
  return a
}

// Spherical lerp for yaw – handles wrap-around correctly
export function lerpAngle(a: number, b: number, t: number): number {
  return a + normaliseAngle(b - a) * t
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t
}

export function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v))
}
