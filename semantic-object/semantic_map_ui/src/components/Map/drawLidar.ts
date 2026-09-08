import type { ScanData, ViewTransform, RobotPose } from '../../state/types'
import { worldToScreen } from './coords'

export function drawLidar(
  ctx: CanvasRenderingContext2D,
  scan: ScanData,
  pose: RobotPose,
  view: ViewTransform,
) {
  const { ranges, angle_min, angle_increment } = scan
  if (ranges.length === 0) return

  const MAX_RANGE = 30 // metres – clip infinite/invalid readings

  ctx.beginPath()

  let first = true
  for (let i = 0; i < ranges.length; i++) {
    const r = ranges[i]
    if (!isFinite(r) || r <= 0) continue
    const clampedR = Math.min(r, MAX_RANGE)

    // Scan angles are in the robot's frame; add robot yaw to get world angle
    const angle = pose.yaw + angle_min + i * angle_increment
    const wx = pose.x + clampedR * Math.cos(angle)
    const wy = pose.y + clampedR * Math.sin(angle)
    const { sx, sy } = worldToScreen(wx, wy, view)

    if (first) { ctx.moveTo(sx, sy); first = false }
    else ctx.lineTo(sx, sy)
  }

  ctx.closePath()
  ctx.fillStyle = 'rgba(74, 158, 255, 0.12)'
  ctx.fill()
  ctx.strokeStyle = 'rgba(74, 158, 255, 0.35)'
  ctx.lineWidth = 1
  ctx.stroke()
}
