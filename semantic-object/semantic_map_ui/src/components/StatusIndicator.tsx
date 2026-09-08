import { useEffect, useState } from 'react'
import { useStore } from '../state/store'

function useTimeAgo(ts: number | null): string {
  const [, tick] = useState(0)

  useEffect(() => {
    const id = setInterval(() => tick((n) => n + 1), 1_000)
    return () => clearInterval(id)
  }, [])

  if (ts === null) return '—'
  const s = Math.floor((Date.now() - ts) / 1_000)
  if (s < 60) return `${s}s ago`
  const m = Math.floor(s / 60)
  return `${m}m ${s % 60}s ago`
}

export function StatusIndicator() {
  const rosConnected  = useStore((s) => s.rosConnected)
  const landmarkCount = useStore((s) => s.landmarkCount)
  const lastUpdateAt  = useStore((s) => s.lastUpdateAt)
  const isMock        = useStore((s) => s.isMock)
  const wsConnected   = useStore((s) => s.wsConnected)

  const timeAgo = useTimeAgo(lastUpdateAt)

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span
          className={`inline-block w-2 h-2 rounded-full ${
            rosConnected ? 'bg-accent-green' : 'bg-accent-red'
          }`}
        />
        <span className="font-mono text-xs text-text-secondary">
          {rosConnected ? 'connected' : 'disconnected'}
        </span>
        {isMock && (
          <span className="font-mono text-xs bg-accent-yellow/20 text-accent-yellow border border-accent-yellow/30 px-1.5 py-0.5 rounded">
            MOCK
          </span>
        )}
      </div>

      <div className="flex items-center gap-2">
        <span
          className={`inline-block w-2 h-2 rounded-full ${
            wsConnected ? 'bg-accent-green' : 'bg-accent-yellow'
          }`}
        />
        <span className="font-mono text-xs text-text-secondary">
          {wsConnected ? 'ws live' : 'ws offline'}
        </span>
      </div>

      <div className="font-mono text-xs text-text-secondary">
        <span className="text-text-primary">{landmarkCount}</span> objects
      </div>

      <div className="font-mono text-xs text-text-dim">
        updated {timeAgo}
      </div>
    </div>
  )
}
