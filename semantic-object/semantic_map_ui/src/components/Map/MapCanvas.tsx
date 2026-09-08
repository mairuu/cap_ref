import { useEffect, useRef, useCallback } from 'react'
import { useStore } from '../../state/store'
import { zoomAt, lerp, lerpAngle, clamp } from './coords'
import { drawOccupancy } from './drawOccupancy'
import { drawLidar } from './drawLidar'
import { drawLandmarks } from './drawLandmarks'
import { drawRobot } from './drawRobot'

const WS_INTERVAL_MS = 200 // expected state WebSocket interval

function drawScaleBar(ctx: CanvasRenderingContext2D, scale: number) {
  // Pick a round metre length that fills roughly 80-120px
  const targetPx = 100
  const worldLen = targetPx / scale
  const rounded = Math.pow(10, Math.round(Math.log10(worldLen)))
  const barPx = rounded * scale

  const x = 20
  const y = ctx.canvas.height - 24
  const h = 4

  ctx.fillStyle = '#e8e8e8'
  ctx.fillRect(x, y, barPx, h)
  ctx.fillRect(x, y - 4, 2, h + 4)
  ctx.fillRect(x + barPx - 2, y - 4, 2, h + 4)

  ctx.font = '10px "JetBrains Mono", monospace'
  ctx.textAlign = 'left'
  ctx.fillStyle = '#e8e8e8'
  ctx.fillText(`${rounded} m`, x, y - 8)
}

export function MapCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef<number>(0)
  const dragRef = useRef<{ startX: number; startY: number; panX: number; panY: number } | null>(null)
  // ref snapshot of store for RAF — avoids React re-renders in the animation loop
  const storeRef = useRef(useStore.getState())

  useEffect(() => {
    return useStore.subscribe((s) => { storeRef.current = s })
  }, [])

  // RAF loop
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!

    let prevScan = storeRef.current.scan

    function frame() {
      const s = storeRef.current
      const { view, robotPose, prevRobotPose, poseReceivedAt, scan,
              landmarks, occupancyGrid, offscreenCanvas, followRobot } = s

      // Resize canvas to its CSS size
      const { width, height } = canvas!.getBoundingClientRect()
      if (canvas!.width !== width || canvas!.height !== height) {
        canvas!.width  = width
        canvas!.height = height
      }

      ctx.clearRect(0, 0, canvas!.width, canvas!.height)
      ctx.fillStyle = '#0d0d0d'
      ctx.fillRect(0, 0, canvas!.width, canvas!.height)

      // Interpolate robot pose for smooth motion at 60fps vs 5Hz updates
      const t = clamp((Date.now() - poseReceivedAt) / WS_INTERVAL_MS, 0, 1)
      const prev = prevRobotPose ?? robotPose
      let ix = 0, iy = 0, iyaw = 0
      if (robotPose && prev) {
        ix   = lerp(prev.x,   robotPose.x,   t)
        iy   = lerp(prev.y,   robotPose.y,   t)
        iyaw = lerpAngle(prev.yaw, robotPose.yaw, t)
      }

      // Auto-follow: keep robot centred
      let liveView = view
      if (followRobot && robotPose) {
        liveView = {
          ...view,
          panX: canvas!.width  / 2 - ix * view.scale,
          panY: canvas!.height / 2 + iy * view.scale,
        }
      }

      // Layer 1: occupancy grid
      if (occupancyGrid && offscreenCanvas) {
        drawOccupancy(ctx, occupancyGrid, offscreenCanvas, liveView)
      }

      // Layer 2: lidar halo (cache check via reference equality)
      if (scan && robotPose) {
        if (scan !== prevScan) prevScan = scan
        drawLidar(ctx, scan, { x: robotPose.x, y: robotPose.y, yaw: robotPose.yaw }, liveView)
      }

      // Layer 3: landmarks
      drawLandmarks(ctx, landmarks, liveView)

      // Layer 4: robot
      if (robotPose) {
        drawRobot(ctx, ix, iy, iyaw, liveView)
      }

      // Layer 5: scale bar (screen space, unaffected by pan/zoom)
      drawScaleBar(ctx, liveView.scale)

      rafRef.current = requestAnimationFrame(frame)
    }

    rafRef.current = requestAnimationFrame(frame)
    return () => cancelAnimationFrame(rafRef.current)
  }, [])

  // Pan: mouse drag
  const onMouseDown = useCallback((e: React.MouseEvent) => {
    const v = useStore.getState().view
    dragRef.current = { startX: e.clientX, startY: e.clientY, panX: v.panX, panY: v.panY }
  }, [])

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragRef.current) return
    const dx = e.clientX - dragRef.current.startX
    const dy = e.clientY - dragRef.current.startY
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
      useStore.getState().setFollowRobot(false)
    }
    useStore.getState().setView({
      ...useStore.getState().view,
      panX: dragRef.current.panX + dx,
      panY: dragRef.current.panY + dy,
    })
  }, [])

  const onMouseUp = useCallback(() => { dragRef.current = null }, [])

  // Zoom: scroll wheel
  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const rect = canvasRef.current!.getBoundingClientRect()
    const cursorSx = e.clientX - rect.left
    const cursorSy = e.clientY - rect.top
    const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1
    const newView = zoomAt(useStore.getState().view, cursorSx, cursorSy, factor)
    useStore.getState().setView(newView)
  }, [])

  // Keyboard shortcuts
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement) return
      const key = e.key.toLowerCase()

      if (key === 'r') {
        // Reset view to centre of canvas
        const canvas = canvasRef.current
        if (!canvas) return
        useStore.getState().setView({
          panX: canvas.width / 2,
          panY: canvas.height / 2,
          scale: 80,
        })
      }
      if (key === 'f') {
        const { followRobot, setFollowRobot } = useStore.getState()
        setFollowRobot(!followRobot)
      }
      if (key === 'c') {
        if (window.confirm('Clear all semantic memory?')) {
          import('../../api/client').then(({ api }) => {
            api.clear().then(() => useStore.getState().clearLandmarks())
          })
        }
      }
    }

    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full cursor-crosshair"
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
      onWheel={onWheel}
    />
  )
}

// Visible follow-robot toggle button, placed by the parent
export function FollowButton() {
  const followRobot = useStore((s) => s.followRobot)
  const setFollowRobot = useStore((s) => s.setFollowRobot)

  return (
    <button
      onClick={() => setFollowRobot(!followRobot)}
      className={`px-3 py-1 text-xs font-mono border rounded transition-colors ${
        followRobot
          ? 'border-accent-blue text-accent-blue bg-accent-blue/10'
          : 'border-bg-border text-text-secondary hover:border-text-secondary'
      }`}
      title="Toggle follow robot (F)"
    >
      {followRobot ? '⊙ FOLLOW' : '⊙ FREE'}
    </button>
  )
}
