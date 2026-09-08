import type { HealthResponse, OccupancyGrid } from '../state/types'

export const BASE_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000'

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
