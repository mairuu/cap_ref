import type { Landmark, ViewTransform } from '../../state/types'
import { worldToScreen } from './coords'
import { classColor } from '../../utils/colors'

const DOT_RADIUS = 6
const LABEL_OFFSET_Y = 14

export function drawLandmarks(
  ctx: CanvasRenderingContext2D,
  landmarks: Landmark[],
  view: ViewTransform,
) {
  ctx.font = '11px "JetBrains Mono", monospace'
  ctx.textAlign = 'center'

  for (const lm of landmarks) {
    const { sx, sy } = worldToScreen(lm.x, lm.y, view)
    const color = classColor(lm.class_label)
    const alpha = lm.stale ? 0.3 : 1.0

    ctx.globalAlpha = alpha

    // dot
    ctx.beginPath()
    ctx.arc(sx, sy, DOT_RADIUS, 0, Math.PI * 2)
    ctx.fillStyle = color
    ctx.fill()
    ctx.strokeStyle = 'rgba(0,0,0,0.5)'
    ctx.lineWidth = 1
    ctx.stroke()

    // label
    ctx.fillStyle = '#e8e8e8'
    ctx.fillText(lm.class_label, sx, sy + LABEL_OFFSET_Y)
  }

  ctx.globalAlpha = 1.0
}
