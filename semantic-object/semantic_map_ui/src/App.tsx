import { useEffect, useState } from 'react'
import { api } from './api/client'
import { createStateWs } from './api/websocket'
import { buildOffscreenCanvas } from './utils/base64'
import { useStore } from './state/store'
import type { WsStateMessage } from './state/types'
import { MapCanvas, FollowButton } from './components/Map/MapCanvas'
import { CameraPanel } from './components/CameraPanel'
import { ConnectionBanner } from './components/ConnectionBanner'
import { OpsDrawer } from './components/Ops/OpsDrawer'

const HEALTH_POLL_MS = 5_000
// The map is FETCHED REPEATEDLY, not once. slam_toolbox keeps extending the
// grid for the whole session, so a map fetched at page load goes stale the
// moment the robot drives anywhere new: RViz shows the live map and the
// browser shows whatever existed when the tab was opened. Reported 16 Sep as
// "the map on the UI does not match the map RViz sees" -- the bridge was
// serving the correct grid all along (verified identical to /map: 249x216,
// origin -7.696,-9.237), the UI simply never asked again.
// Slower than health because the payload is the whole grid, not a status line.
const MAP_POLL_MS = 3_000

export function App() {
  const [opsOpen, setOpsOpen] = useState(false)
  const setWsConnected   = useStore((s) => s.setWsConnected)
  const setRosConnected  = useStore((s) => s.setRosConnected)
  const applyStateMessage = useStore((s) => s.applyStateMessage)
  const setOccupancyGrid = useStore((s) => s.setOccupancyGrid)

  // Bootstrap: fetch health + map, start WebSockets
  useEffect(() => {
    let healthInterval: ReturnType<typeof setInterval>
    let mapInterval: ReturnType<typeof setInterval>

    async function fetchHealth() {
      try {
        const h = await api.health()
        setRosConnected(h.ros_connected, h.mock ?? false)
      } catch {
        setRosConnected(false)
      }
    }

    async function fetchMap() {
      try {
        const grid = await api.map()
        const canvas = buildOffscreenCanvas(grid)
        setOccupancyGrid(grid, canvas)
      } catch {
        // non-fatal: map can be refreshed later
      }
    }

    fetchHealth()
    fetchMap()
    healthInterval = setInterval(fetchHealth, HEALTH_POLL_MS)
    mapInterval = setInterval(fetchMap, MAP_POLL_MS)

    const ws = createStateWs(
      (msg) => applyStateMessage(msg as WsStateMessage),
      () => setWsConnected(true),
      () => setWsConnected(false),
    )

    return () => {
      clearInterval(healthInterval)
      clearInterval(mapInterval)
      ws.destroy()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // O toggles the stack drawer, next to the existing R / F / C shortcuts.
  // Ignored while typing, so it cannot fire from a text field.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const el = e.target as HTMLElement | null
      if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA')) return
      if (e.key === 'o' || e.key === 'O') setOpsOpen((v) => !v)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return (
    <div className="flex flex-col h-screen bg-bg-base text-text-primary overflow-hidden">
      <ConnectionBanner />

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden flex-col md:flex-row">
        {/* Map area */}
        <div className="relative flex-1 flex flex-col overflow-hidden">
          {/* Map toolbar */}
          <div className="absolute top-3 right-3 z-10 flex gap-2">
            <FollowButton />
            <button
              onClick={() => {
                const canvas = document.querySelector('canvas')
                if (!canvas) return
                useStore.getState().setView({
                  panX: canvas.width / 2,
                  panY: canvas.height / 2,
                  scale: 80,
                })
              }}
              className="px-3 py-1 text-xs font-mono border border-bg-border text-text-secondary hover:border-text-secondary rounded transition-colors"
              title="Reset view (R)"
            >
              RESET
            </button>
          </div>

          <MapCanvas />

          {/* Map label */}
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 font-mono text-[10px] text-text-dim tracking-widest select-none pointer-events-none">
            LIVE SEMANTIC MAP
          </div>
        </div>

        {/* Camera / status panel */}
        <CameraPanel />

        {/* Operator console */}
        <OpsDrawer open={opsOpen} onClose={() => setOpsOpen(false)} />
      </div>

      {/* Footer: keyboard shortcuts */}
      <footer className="flex justify-center gap-6 py-2 border-t border-bg-border bg-bg-panel">
        {[
          ['R', 'reset view'],
          ['F', 'toggle follow'],
          ['C', 'clear map'],
          ['O', 'stack console'],
        ].map(([key, label]) => (
          <span key={key} className="font-mono text-[10px] text-text-dim">
            <kbd className="px-1 py-0.5 border border-bg-border rounded text-text-secondary mr-1">
              {key}
            </kbd>
            {label}
          </span>
        ))}
      </footer>
    </div>
  )
}
