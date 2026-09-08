import { useEffect, useState } from 'react'
import { useStore } from '../state/store'

const BANNER_DELAY_MS = 5_000

export function ConnectionBanner() {
  const wsConnected    = useStore((s) => s.wsConnected)
  const wsDisconnectedAt = useStore((s) => s.wsDisconnectedAt)
  const rosConnected   = useStore((s) => s.rosConnected)

  const [showReconnecting, setShowReconnecting] = useState(false)

  useEffect(() => {
    if (wsConnected) {
      setShowReconnecting(false)
      return
    }
    if (wsDisconnectedAt === null) return
    const elapsed = Date.now() - wsDisconnectedAt
    const remaining = BANNER_DELAY_MS - elapsed
    if (remaining <= 0) {
      setShowReconnecting(true)
      return
    }
    const t = setTimeout(() => setShowReconnecting(true), remaining)
    return () => clearTimeout(t)
  }, [wsConnected, wsDisconnectedAt])

  if (wsConnected && rosConnected) return null

  if (!wsConnected && showReconnecting) {
    return (
      <div className="absolute top-0 left-0 right-0 z-50 flex items-center justify-center py-2 bg-accent-yellow/20 border-b border-accent-yellow/40">
        <span className="text-accent-yellow font-mono text-xs tracking-wider">
          ⚠ RECONNECTING…
        </span>
      </div>
    )
  }

  if (wsConnected && !rosConnected) {
    return (
      <div className="absolute top-0 left-0 right-0 z-50 flex items-center justify-center py-2 bg-accent-red/20 border-b border-accent-red/40">
        <span className="text-accent-red font-mono text-xs tracking-wider">
          ✕ ROBOT NOT CONNECTED
        </span>
      </div>
    )
  }

  return null
}
