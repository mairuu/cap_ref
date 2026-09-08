import type { OccupancyGrid, ViewTransform } from '../../state/types'
import { worldToScreen } from './coords'

export function drawOccupancy(
  ctx: CanvasRenderingContext2D,
  grid: OccupancyGrid,
  offscreen: OffscreenCanvas,
  view: ViewTransform,
) {
  // The offscreen canvas has one pixel per grid cell.
  // Cell (0,0) corresponds to world position (origin.x, origin.y).
  // Cell (col, row) → world (origin.x + col*res, origin.y + row*res)
  // BUT the grid's row=0 is the bottom row in world space (y-up),
  // while canvas row=0 is the top — so we flip vertically.

  const { origin, resolution, width, height } = grid
  const { sx: x0, sy: y0 } = worldToScreen(origin.x, origin.y, view)

  const pxW = width * resolution * view.scale
  const pxH = height * resolution * view.scale

  ctx.save()
  // Translate to where origin (bottom-left of grid in world) maps on screen
  ctx.translate(x0, y0)
  // Grid rows go bottom-up in world, but canvas rows go top-down —
  // draw flipped vertically so row 0 of the image lands at the bottom
  ctx.scale(1, -1)
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(offscreen, 0, 0, pxW, pxH)
  ctx.imageSmoothingEnabled = true;
  ctx.restore()
}
