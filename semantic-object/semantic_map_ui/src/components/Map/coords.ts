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

// Pan the view so a world point sits at the centre of the canvas, keeping the
// current zoom. Note the sign difference between the two axes -- it is the same
// y flip as worldToScreen, and getting it wrong centres on the mirror image of
// the point, which looks plausible near the origin and very wrong away from it.
//
// Callers must turn followRobot OFF first. The RAF loop recomputes panX/panY
// from the robot pose on EVERY frame while follow is on, so a view set here
// would be overwritten before it was ever painted -- the click would appear to
// do nothing at all.
export function centreViewOn(
  v: ViewTransform,
  canvasWidth: number,
  canvasHeight: number,
  wx: number,
  wy: number,
): ViewTransform {
  return {
    scale: v.scale,
    panX: canvasWidth / 2 - wx * v.scale,
    panY: canvasHeight / 2 + wy * v.scale,
  }
}
