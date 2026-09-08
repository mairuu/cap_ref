import { useState } from 'react'
import { api } from '../api/client'
import { useStore } from '../state/store'

export function ClearButton() {
  const clearLandmarks = useStore((s) => s.clearLandmarks)
  const [loading, setLoading] = useState(false)

  async function handleClear() {
    if (!window.confirm('Clear all semantic memory? This cannot be undone.')) return
    setLoading(true)
    try {
      await api.clear()
      clearLandmarks()
    } catch {
      // backend may be unreachable; clear local state anyway
      clearLandmarks()
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleClear}
      disabled={loading}
      className="w-full py-2 font-mono text-xs tracking-wider border border-bg-border text-text-secondary
                 hover:border-accent-red hover:text-accent-red transition-colors rounded
                 disabled:opacity-40 disabled:cursor-not-allowed"
      title="Clear semantic memory (C)"
    >
      {loading ? 'CLEARING…' : '[CLEAR MAP]'}
    </button>
  )
}
