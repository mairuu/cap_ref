import { create } from 'zustand'
import type {
  RobotPose,
  Landmark,
  ScanData,
  OccupancyGrid,
  ViewTransform,
  WsStateMessage,
} from './types'

const DEFAULT_SCALE = 80 // pixels per metre

interface AppStore {
  // connection
  wsConnected: boolean
  wsDisconnectedAt: number | null
  rosConnected: boolean
  isMock: boolean
  landmarkCount: number
  lastUpdateAt: number | null

  // live robot state
  robotPose: RobotPose | null
  prevRobotPose: RobotPose | null
  poseReceivedAt: number

  scan: ScanData | null
  landmarks: Landmark[]

  // The landmark the object panel has selected, or null. Lives in the store
  // rather than in ObjectList's own state because the CANVAS needs it too, and
  // MapCanvas reads the store through a ref inside its requestAnimationFrame
  // loop -- so putting it here costs the render loop one field read and no
  // extra React work. Toggle-on-reclick is the row's job, not the store's.
  selectedLandmarkId: string | null

  // map
  occupancyGrid: OccupancyGrid | null
  offscreenCanvas: OffscreenCanvas | null

  // viewport
  view: ViewTransform
  followRobot: boolean

  // actions
  setWsConnected(v: boolean): void
  setRosConnected(v: boolean, isMock?: boolean): void
  setLandmarkCount(n: number): void
  applyStateMessage(msg: WsStateMessage): void
  setOccupancyGrid(grid: OccupancyGrid, canvas: OffscreenCanvas): void
  setView(t: ViewTransform): void
  setFollowRobot(v: boolean): void
  selectLandmark(id: string | null): void
  clearLandmarks(): void
}

export const useStore = create<AppStore>((set, get) => ({
  wsConnected: false,
  wsDisconnectedAt: null,
  rosConnected: false,
  isMock: false,
  landmarkCount: 0,
  lastUpdateAt: null,

  robotPose: null,
  prevRobotPose: null,
  poseReceivedAt: 0,

  scan: null,
  landmarks: [],
  selectedLandmarkId: null,

  occupancyGrid: null,
  offscreenCanvas: null,

  view: { panX: 0, panY: 0, scale: DEFAULT_SCALE },
  followRobot: true,

  setWsConnected(v) {
    set({
      wsConnected: v,
      wsDisconnectedAt: v ? null : Date.now(),
    })
  },

  setRosConnected(v, isMock = false) {
    set({ rosConnected: v, isMock })
  },

  setLandmarkCount(n) {
    set({ landmarkCount: n })
  },

  applyStateMessage(msg) {
    const prev = get().robotPose
    set({
      prevRobotPose: prev,
      robotPose: msg.robot_pose,
      poseReceivedAt: Date.now(),
      scan: msg.scan,
      landmarks: msg.landmarks,
      landmarkCount: msg.landmarks.length,
      lastUpdateAt: Date.now(),
    })
  },

  setOccupancyGrid(grid, canvas) {
    set({ occupancyGrid: grid, offscreenCanvas: canvas })
  },

  setView(t) {
    set({ view: t })
  },

  setFollowRobot(v) {
    set({ followRobot: v })
  },

  selectLandmark(id) {
    set({ selectedLandmarkId: id })
  },

  clearLandmarks() {
    // The selection goes with them: a selected id that no longer exists would
    // leave the panel showing a highlighted row for a landmark that is gone.
    set({ landmarks: [], landmarkCount: 0, selectedLandmarkId: null })
  },
}))
