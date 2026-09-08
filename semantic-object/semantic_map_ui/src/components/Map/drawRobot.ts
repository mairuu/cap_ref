import type { ViewTransform } from '../../state/types'
import { worldToScreen } from './coords'

const ROBOT_SIZE = 10 // screen pixels from centre to tip

export function drawRobot(
  ctx: CanvasRenderingContext2D,
  wx: number,
  wy: number,
  yaw: number,
  view: ViewTransform,
) {
  const { sx, sy } = worldToScreen(wx, wy, view)

  ctx.save()
  ctx.translate(sx, sy)
  // Canvas y is flipped vs world, so negate yaw for screen rotation
  ctx.rotate(-yaw)

  ctx.beginPath()
  // Triangle: tip forward (+x in robot frame = right on screen before rotation)
  ctx.moveTo(ROBOT_SIZE * 1.5, 0)
  ctx.lineTo(-ROBOT_SIZE, -ROBOT_SIZE)
  ctx.lineTo(-ROBOT_SIZE * 0.5, 0)
  ctx.lineTo(-ROBOT_SIZE, ROBOT_SIZE)
  ctx.closePath()

  ctx.fillStyle = '#ffffff'
  ctx.fill()
  ctx.strokeStyle = '#4a9eff'
  ctx.lineWidth = 2
  ctx.stroke()

  ctx.restore()
}
