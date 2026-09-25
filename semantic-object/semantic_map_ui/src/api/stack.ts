import { BASE_URL } from './client'
import { ReconnectingWs } from './websocket'

export type ComponentState =
  | 'stopped' | 'starting' | 'ready' | 'crashed' | 'stopping'

export interface Check { ok: boolean; detail: string; why: string }

export interface StackComponent {
  name: string
  state: ComponentState
  ready: boolean
  dead_status: number | null
  pid: number | null
  uptime_s: number | null
  managed: boolean
  restartable: boolean
  warn: string | null
  devices: string[]
  checks: Check[]
}

export interface StackEvent { t: number; level: string; text: string }

export interface StackSnapshot {
  session: string
  components: StackComponent[]
  events: StackEvent[]
  readiness_age_s: number | null
}

export interface ControlStatus {
  enabled: boolean
  available: boolean
  nav_state: string
  nav_ready: boolean
  explore_state: string
  can_drive: boolean
  can_goal: boolean
  held: boolean
  state?: 'idle' | 'active' | 'zeroing'
  max_linear?: number
  hard_max_linear?: number
  goal_active?: boolean
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init)
  const body = await res.json().catch(() => ({}))
  // The bridge answers 409 with a sentence explaining WHY the stack is not in
  // a state where the request makes sense ("nav is stopped, not ready...").
  // That sentence is the whole value of the endpoint, so surface it rather
  // than a status code.
  if (!res.ok) throw new Error((body as { detail?: string }).detail ?? `${path} → ${res.status}`)
  return body as T
}

export const stackApi = {
  state:    () => call<StackSnapshot>('/api/stack'),
  control:  () => call<ControlStatus>('/api/control'),
  start:    (n: string) => call(`/api/stack/${n}/start`,   { method: 'POST' }),
  stop:     (n: string) => call(`/api/stack/${n}/stop`,    { method: 'POST' }),
  restart:  (n: string) => call(`/api/stack/${n}/restart`, { method: 'POST' }),
  up:       (p = 'demo') => call(`/api/stack/up?profile=${p}`,   { method: 'POST' }),
  down:     (p = 'demo') => call(`/api/stack/down?profile=${p}`, { method: 'POST' }),
  estop:    () => call('/api/estop', { method: 'POST' }),
  goal:     (x: number, y: number, yaw = 0) =>
    call('/api/goal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ x, y, yaw }),
    }),
  cancelGoal: () => call('/api/goal/cancel', { method: 'POST' }),
}

export function createStackWs(onSnapshot: (s: StackSnapshot) => void) {
  return new ReconnectingWs<string>({
    path: '/api/stack/ws',
    onMessage(raw) {
      try { onSnapshot(JSON.parse(raw) as StackSnapshot) } catch { /* ignore */ }
    },
  })
}

export function createLogWs(component: string, onText: (t: string) => void) {
  return new ReconnectingWs<string>({
    path: `/api/stack/ws/logs?component=${encodeURIComponent(component)}`,
    onMessage(raw) {
      try {
        const d = JSON.parse(raw) as { text?: string }
        if (typeof d.text === 'string') onText(d.text)
      } catch { /* ignore */ }
    },
  })
}
