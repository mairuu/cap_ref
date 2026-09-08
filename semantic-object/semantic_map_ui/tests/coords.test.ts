import { describe, it, expect } from 'vitest'
import {
  worldToScreen,
  screenToWorld,
  zoomAt,
  lerpAngle,
  lerp,
  normaliseAngle,
} from '../src/components/Map/coords'
import type { ViewTransform } from '../src/state/types'

const VIEW: ViewTransform = { panX: 400, panY: 300, scale: 100 }

describe('worldToScreen / screenToWorld roundtrip', () => {
  it('maps origin world point to pan position', () => {
    const { sx, sy } = worldToScreen(0, 0, VIEW)
    expect(sx).toBe(400)
    expect(sy).toBe(300)
  })

  it('x-right in world maps to x-right on screen', () => {
    const { sx } = worldToScreen(1, 0, VIEW)
    expect(sx).toBe(500)
  })

  it('y-up in world maps to y-up on screen (decreasing sy)', () => {
    const { sy } = worldToScreen(0, 1, VIEW)
    expect(sy).toBe(200) // panY - 1*scale
  })

  it('roundtrips any world point', () => {
    const wx = 3.7, wy = -1.2
    const screen = worldToScreen(wx, wy, VIEW)
    const world  = screenToWorld(screen.sx, screen.sy, VIEW)
    expect(world.wx).toBeCloseTo(wx)
    expect(world.wy).toBeCloseTo(wy)
  })
})

describe('zoomAt', () => {
  it('keeps the cursor world position fixed after zoom', () => {
    const cursorSx = 250, cursorSy = 150
    const before = screenToWorld(cursorSx, cursorSy, VIEW)
    const newView = zoomAt(VIEW, cursorSx, cursorSy, 2)
    const after  = screenToWorld(cursorSx, cursorSy, newView)
    expect(after.wx).toBeCloseTo(before.wx)
    expect(after.wy).toBeCloseTo(before.wy)
  })

  it('clamps scale to minimum 10', () => {
    const v = zoomAt(VIEW, 0, 0, 0.00001)
    expect(v.scale).toBe(10)
  })

  it('clamps scale to maximum 500', () => {
    const v = zoomAt(VIEW, 0, 0, 99999)
    expect(v.scale).toBe(500)
  })
})

describe('lerp', () => {
  it('returns start at t=0', () => expect(lerp(2, 10, 0)).toBe(2))
  it('returns end at t=1',   () => expect(lerp(2, 10, 1)).toBe(10))
  it('returns midpoint at t=0.5', () => expect(lerp(0, 10, 0.5)).toBe(5))
})

describe('normaliseAngle', () => {
  it('keeps 0 as 0', () => expect(normaliseAngle(0)).toBe(0))
  it('maps π+0.1 to a negative angle', () => {
    expect(normaliseAngle(Math.PI + 0.1)).toBeCloseTo(-Math.PI + 0.1)
  })
  it('maps -π-0.1 to a positive angle', () => {
    expect(normaliseAngle(-Math.PI - 0.1)).toBeCloseTo(Math.PI - 0.1)
  })
})

describe('lerpAngle', () => {
  it('takes the short path across 0', () => {
    // from -0.1 to 0.1 should go via 0, not the long way around
    const result = lerpAngle(-0.1, 0.1, 0.5)
    expect(result).toBeCloseTo(0)
  })

  it('takes the short path across ±π boundary', () => {
    // from π-0.1 to -(π-0.1) could go two ways; short path is ≈ 0.2 rad
    const a = Math.PI - 0.1
    const b = -(Math.PI - 0.1)
    const mid = lerpAngle(a, b, 0.5)
    // midpoint should be near ±π, not near 0
    expect(Math.abs(Math.abs(mid) - Math.PI)).toBeLessThan(0.15)
  })

  it('returns start at t=0', () => {
    expect(lerpAngle(1.2, 2.4, 0)).toBeCloseTo(1.2)
  })

  it('returns end at t=1', () => {
    expect(lerpAngle(1.2, 2.4, 1)).toBeCloseTo(2.4)
  })
})
