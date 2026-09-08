export interface RobotPose {
  x: number
  y: number
  yaw: number
}

export interface Landmark {
  id: string
  class_label: string
  x: number
  y: number
  confidence: number
  seen_count: number
  stale: boolean
}

export interface ScanData {
  angle_min: number
  angle_increment: number
  ranges: number[]
}

export interface OccupancyGrid {
  width: number
  height: number
  resolution: number
  origin: { x: number; y: number; yaw: number }
  data: string
}

export interface ViewTransform {
  panX: number
  panY: number
  scale: number
}

export interface WsStateMessage {
  timestamp: number
  robot_pose: RobotPose
  landmarks: Landmark[]
  scan: ScanData
}

export interface HealthResponse {
  ros_connected: boolean
  last_landmark_msg: string | null
  landmark_count: number
  robot_pose: RobotPose | null
  mock?: boolean
}
