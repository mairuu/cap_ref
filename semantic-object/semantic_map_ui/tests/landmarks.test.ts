import { describe, it, expect } from 'vitest'
import { sortLandmarks, groupByClass, distance } from '../src/utils/landmarks'
import type { Landmark, RobotPose } from '../src/state/types'

function lm(over: Partial<Landmark> & { id: string }): Landmark {
  return {
    class_label: 'chair',
    x: 0,
    y: 0,
    confidence: 0.9,
    seen_count: 1,
    stale: false,
    ...over,
  }
}

const pose: RobotPose = { x: 0, y: 0, yaw: 0 }

describe('distance', () => {
  it('is euclidean', () => {
    expect(distance(0, 0, 3, 4)).toBe(5)
  })
})

describe('sortLandmarks', () => {
  it('orders by distance from the robot, nearest first', () => {
    const far = lm({ id: 'far', x: 5, y: 0 })
    const near = lm({ id: 'near', x: 1, y: 0 })
    const mid = lm({ id: 'mid', x: 0, y: 3 })

    expect(sortLandmarks([far, near, mid], pose).map((l) => l.id)).toEqual([
      'near',
      'mid',
      'far',
    ])
  })

  it('measures distance from the robot, not from the origin', () => {
    const atOrigin = lm({ id: 'origin', x: 0, y: 0 })
    const byRobot = lm({ id: 'by-robot', x: 9, y: 0 })

    const sorted = sortLandmarks([atOrigin, byRobot], { x: 10, y: 0, yaw: 0 })
    expect(sorted.map((l) => l.id)).toEqual(['by-robot', 'origin'])
  })

  it('falls back to seen_count then label when there is no pose', () => {
    const a = lm({ id: 'a', class_label: 'zebra', seen_count: 1 })
    const b = lm({ id: 'b', class_label: 'apple', seen_count: 9 })
    const c = lm({ id: 'c', class_label: 'apple', seen_count: 1 })

    expect(sortLandmarks([a, b, c], null).map((l) => l.id)).toEqual(['b', 'c', 'a'])
  })

  it('is total and stable with no pose and identical rows', () => {
    const a = lm({ id: 'a' })
    const b = lm({ id: 'b' })
    expect(sortLandmarks([b, a], null).map((l) => l.id)).toEqual(['a', 'b'])
  })

  it('does not mutate the input array', () => {
    const far = lm({ id: 'far', x: 5, y: 0 })
    const near = lm({ id: 'near', x: 1, y: 0 })
    const input = [far, near]

    sortLandmarks(input, pose)

    expect(input.map((l) => l.id)).toEqual(['far', 'near'])
  })

  it('handles an empty list', () => {
    expect(sortLandmarks([], pose)).toEqual([])
    expect(sortLandmarks([], null)).toEqual([])
  })
})

describe('groupByClass', () => {
  it('counts per class', () => {
    const groups = groupByClass([
      lm({ id: '1', class_label: 'chair' }),
      lm({ id: '2', class_label: 'chair' }),
      lm({ id: '3', class_label: 'laptop' }),
    ])

    expect(groups).toEqual([
      { label: 'chair', color: expect.any(String), count: 2 },
      { label: 'laptop', color: expect.any(String), count: 1 },
    ])
  })

  it('orders by count descending, then label', () => {
    const groups = groupByClass([
      lm({ id: '1', class_label: 'zebra' }),
      lm({ id: '2', class_label: 'apple' }),
      lm({ id: '3', class_label: 'cup' }),
      lm({ id: '4', class_label: 'cup' }),
    ])

    expect(groups.map((g) => g.label)).toEqual(['cup', 'apple', 'zebra'])
  })

  it('gives each class the colour the map draws it with', () => {
    const [chair] = groupByClass([lm({ id: '1', class_label: 'chair' })])
    expect(chair.color).toBe('#4a9eff')
  })

  it('handles an empty list', () => {
    expect(groupByClass([])).toEqual([])
  })
})
