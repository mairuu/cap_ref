import type { HealthResponse, OccupancyGrid } from '../state/types'

// Where the bridge lives.
//
// DERIVED FROM THE BROWSER'S OWN ADDRESS BY DEFAULT, deliberately. The Jetson
// takes a DHCP lease and that address changes: this file's .env held three
// different literals on 16 Sep alone (172.20.10.2, then 192.168.160.106, then
// 10.228.103.105), and every stale one presents identically -- the UI loads
// and then sits on "connecting..." forever with nothing else wrong. Since Vite
// serves this page FROM the Jetson, the host the browser used to reach the UI
// is by definition the host the bridge is on, so deriving it is both correct
// and self-maintaining.
//
// VITE_BACKEND_URL still wins when set, for the case where the bridge and the
// UI are genuinely on different machines. Leave it unset unless that is true.
const derived = `${window.location.protocol}//${window.location.hostname}:8000`

export const BASE_URL = import.meta.env.VITE_BACKEND_URL || derived

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init)
  if (!res.ok) throw new Error(`${path} → ${res.status}`)
  return res.json() as Promise<T>
}

export const api = {
  health(): Promise<HealthResponse> {
    return apiFetch('/api/health')
  },

  map(): Promise<OccupancyGrid> {
    return apiFetch('/api/map')
  },

  clear(): Promise<void> {
    return apiFetch('/api/clear', { method: 'POST' })
  },
}
