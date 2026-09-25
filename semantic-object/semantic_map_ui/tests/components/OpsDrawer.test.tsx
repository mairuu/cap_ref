/**
 * The drawer renders, and the two claims that matter are visible: a component's
 * failing checks with their reasons, and a drive pad that refuses to drive when
 * nav is not ready.
 *
 * A compile is not a render. Everything here was type-correct while the panel
 * was still untested.
 */
import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { OpsDrawer } from '../../src/components/Ops/OpsDrawer'

// The drawer opens a WebSocket for live snapshots; jsdom has none.
class FakeWs {
  onopen: (() => void) | null = null
  onmessage: ((e: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  readyState = 1
  constructor(public url: string) { FakeWs.last = this }
  send() {}
  close() {}
  static last: FakeWs | null = null
}
vi.stubGlobal('WebSocket', FakeWs as unknown as typeof WebSocket)

const SNAPSHOT = {
  session: 'cap',
  readiness_age_s: 3,
  events: [],
  components: [
    {
      name: 'real', state: 'ready', ready: true, dead_status: null, pid: 111,
      uptime_s: 42, managed: true, restartable: false,
      warn: 'Stopping this resets the ESP32 over DTR.',
      devices: ['/dev/esp32'],
      checks: [{ ok: true, detail: '/scan: 11.7 Hz (want >= 3)', why: '' }],
    },
    {
      name: 'nav', state: 'starting', ready: false, dead_status: null, pid: 222,
      uptime_s: 5, managed: true, restartable: true, warn: null, devices: [],
      checks: [{
        ok: false,
        detail: 'action navigate_to_pose: no server',
        why: 'the BT navigator is not accepting goals yet',
      }],
    },
    {
      name: 'bridge', state: 'ready', ready: true, dead_status: null, pid: 333,
      uptime_s: 99, managed: false, restartable: true, warn: null,
      devices: [], checks: [],
    },
  ],
}

const CONTROL_NAV_DOWN = {
  enabled: true, available: true, nav_state: 'starting', nav_ready: false,
  explore_state: 'stopped', can_drive: false, can_goal: false, held: false,
  state: 'idle', max_linear: 0.1, hard_max_linear: 0.3, goal_active: false,
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => ({
    ok: true,
    json: async () => (String(url).includes('/api/control') ? CONTROL_NAV_DOWN : SNAPSHOT),
  })) as unknown as typeof fetch)
})

describe('OpsDrawer', () => {
  it('renders nothing when closed', () => {
    const { container } = render(<OpsDrawer open={false} onClose={() => {}} />)
    expect(container.firstChild).toBeNull()
  })

  it('lists components from the live snapshot', async () => {
    render(<OpsDrawer open onClose={() => {}} />)
    // seeded from the WS handshake frame
    FakeWs.last?.onmessage?.({ data: JSON.stringify(SNAPSHOT) })
    await waitFor(() => expect(screen.getByText('real')).toBeInTheDocument())
    expect(screen.getByText('nav')).toBeInTheDocument()
  })

  it('marks an unmanaged component external rather than offering buttons', async () => {
    render(<OpsDrawer open onClose={() => {}} />)
    FakeWs.last?.onmessage?.({ data: JSON.stringify(SNAPSHOT) })
    await waitFor(() => expect(screen.getByText('external')).toBeInTheDocument())
  })

  it('refuses to drive while nav is not ready, and says why', async () => {
    render(<OpsDrawer open onClose={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText(/the speed guard and twist_mux live there/i))
        .toBeInTheDocument())
  })

  it('never claims to be the e-stop', async () => {
    render(<OpsDrawer open onClose={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText(/Not the e-stop/i)).toBeInTheDocument())
    expect(screen.getByText(/make teleop-nav/)).toBeInTheDocument()
  })
})
