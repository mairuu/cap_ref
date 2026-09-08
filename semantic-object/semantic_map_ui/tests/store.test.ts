import { describe, it, expect, beforeEach } from 'vitest'
import { useStore } from '../src/state/store'
import type { WsStateMessage } from '../src/state/types'

const POSE = { x: 1, y: 2, yaw: 0.5 }

const LANDMARK = {
  id: 'abc',
  class_label: 'chair',
  x: 3,
  y: 4,
  confidence: 0.9,
  seen_count: 3,
  stale: false,
}

const MSG: WsStateMessage = {
  timestamp: 1000,
  robot_pose: POSE,
  landmarks: [LANDMARK],
  scan: { angle_min: -1.57, angle_increment: 0.01, ranges: [2.0] },
}

beforeEach(() => {
  useStore.setState({
    robotPose: null,
    prevRobotPose: null,
    landmarks: [],
    landmarkCount: 0,
    scan: null,
    lastUpdateAt: null,
    wsConnected: false,
    wsDisconnectedAt: null,
    rosConnected: false,
    isMock: false,
    followRobot: true,
  })
})

describe('applyStateMessage', () => {
  it('sets robotPose and prevRobotPose correctly on first message', () => {
    useStore.getState().applyStateMessage(MSG)
    const s = useStore.getState()
    expect(s.robotPose).toEqual(POSE)
    expect(s.prevRobotPose).toBeNull() // was null before
  })

  it('shifts pose to prevRobotPose on second message', () => {
    useStore.getState().applyStateMessage(MSG)
    const POSE2 = { x: 2, y: 3, yaw: 1.0 }
    useStore.getState().applyStateMessage({ ...MSG, robot_pose: POSE2 })
    const s = useStore.getState()
    expect(s.robotPose).toEqual(POSE2)
    expect(s.prevRobotPose).toEqual(POSE)
  })

  it('replaces landmarks wholesale', () => {
    useStore.getState().applyStateMessage(MSG)
    const lm2 = { ...LANDMARK, id: 'xyz', class_label: 'bottle' }
    useStore.getState().applyStateMessage({ ...MSG, landmarks: [lm2] })
    const s = useStore.getState()
    expect(s.landmarks).toHaveLength(1)
    expect(s.landmarks[0].id).toBe('xyz')
  })

  it('updates landmarkCount', () => {
    useStore.getState().applyStateMessage({ ...MSG, landmarks: [LANDMARK, { ...LANDMARK, id: '2' }] })
    expect(useStore.getState().landmarkCount).toBe(2)
  })

  it('updates lastUpdateAt', () => {
    const before = Date.now()
    useStore.getState().applyStateMessage(MSG)
    const after = Date.now()
    const t = useStore.getState().lastUpdateAt!
    expect(t).toBeGreaterThanOrEqual(before)
    expect(t).toBeLessThanOrEqual(after)
  })
})

describe('setWsConnected', () => {
  it('clears wsDisconnectedAt when connected', () => {
    useStore.setState({ wsDisconnectedAt: 12345 })
    useStore.getState().setWsConnected(true)
    expect(useStore.getState().wsDisconnectedAt).toBeNull()
  })

  it('records disconnect time when disconnected', () => {
    const before = Date.now()
    useStore.getState().setWsConnected(false)
    const after = Date.now()
    const t = useStore.getState().wsDisconnectedAt!
    expect(t).toBeGreaterThanOrEqual(before)
    expect(t).toBeLessThanOrEqual(after)
  })
})

describe('clearLandmarks', () => {
  it('empties landmarks and resets count', () => {
    useStore.getState().applyStateMessage(MSG)
    useStore.getState().clearLandmarks()
    const s = useStore.getState()
    expect(s.landmarks).toHaveLength(0)
    expect(s.landmarkCount).toBe(0)
  })
})

describe('setRosConnected', () => {
  it('sets rosConnected and isMock', () => {
    useStore.getState().setRosConnected(true, true)
    const s = useStore.getState()
    expect(s.rosConnected).toBe(true)
    expect(s.isMock).toBe(true)
  })

  it('defaults isMock to false', () => {
    useStore.getState().setRosConnected(true)
    expect(useStore.getState().isMock).toBe(false)
  })
})
