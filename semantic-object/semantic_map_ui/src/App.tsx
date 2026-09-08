import { useEffect } from 'react'
import { api } from './api/client'
import { createStateWs } from './api/websocket'
import { buildOffscreenCanvas } from './utils/base64'
import { useStore } from './state/store'
import type { WsStateMessage } from './state/types'
import { MapCanvas, FollowButton } from './components/Map/MapCanvas'
import { CameraPanel } from './components/CameraPanel'
import { ConnectionBanner } from './components/ConnectionBanner'

const HEALTH_POLL_MS = 5_000

export function App() {
  const setWsConnected   = useStore((s) => s.setWsConnected)
  const setRosConnected  = useStore((s) => s.setRosConnected)
  const applyStateMessage = useStore((s) => s.applyStateMessage)
  const setOccupancyGrid = useStore((s) => s.setOccupancyGrid)

  // Bootstrap: fetch health + map, start WebSockets
  useEffect(() => {
    let healthInterval: ReturnType<typeof setInterval>

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

    const ws = createStateWs(
      (msg) => applyStateMessage(msg as WsStateMessage),
      () => setWsConnected(true),
      () => setWsConnected(false),
    )

    return () => {
      clearInterval(healthInterval)
      ws.destroy()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
      </div>

      {/* Footer: keyboard shortcuts */}
      <footer className="flex justify-center gap-6 py-2 border-t border-bg-border bg-bg-panel">
        {[
          ['R', 'reset view'],
          ['F', 'toggle follow'],
          ['C', 'clear map'],
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
