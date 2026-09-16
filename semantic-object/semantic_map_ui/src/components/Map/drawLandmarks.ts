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

    // Label: white with a dark halo, because the canvas has BOTH light and
    // dark regions and one flat colour cannot serve both. The old '#e8e8e8'
    // scored 1.08:1 against mapped free space (#f0f0f0) -- invisible -- while
    // reading fine at 4.83:1 over unknown grey (#646464). The effect was that
    // class labels disappeared exactly where the robot had already mapped,
    // which is most of the map by the end of a run. Reported 16 Sep as markers
    // showing without their class. Stroke first, then fill over it.
    ctx.lineJoin = 'round'
    ctx.miterLimit = 2
    ctx.lineWidth = 3
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.85)'
    ctx.strokeText(lm.class_label, sx, sy + LABEL_OFFSET_Y)
    ctx.fillStyle = '#ffffff'
    ctx.fillText(lm.class_label, sx, sy + LABEL_OFFSET_Y)
  }

  ctx.globalAlpha = 1.0
}
