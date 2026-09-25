import { useEffect, useRef, useState } from 'react'
import { BASE_URL } from '../../api/client'
import type { ControlStatus } from '../../api/stack'

const SEND_HZ = 15

/**
 * Press-and-hold drive pad.
 *
 * PRESS-AND-HOLD, NOT CLICK-TO-TOGGLE, on purpose. Releasing must mean stop,
 * and a toggle leaves a robot driving because somebody looked away. Pointer
 * capture means a drag that leaves the pad still ends when the finger lifts.
 *
 * It sends at 15 Hz and the bridge stops the robot if it hears nothing for
 * 300 ms, so a dropped connection stops it too -- there is no "held command"
 * to get stuck. The bridge then RELEASES the channel rather than holding zero,
 * which is what keeps Nav2 from being locked out; see control_node.py.
 *
 * THIS IS NOT THE E-STOP. `make teleop-nav` on a keyboard is. This is a WiFi
 * joystick on a hotspot, and the UI says so.
 */
export function DrivePad({ status }: { status: ControlStatus | null }) {
  const [driving, setDriving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const cmd = useRef({ vx: 0, wz: 0 })
  const padRef = useRef<HTMLDivElement>(null)

  const maxLinear = status?.max_linear ?? 0.1
  const canDrive = !!status?.can_drive

  useEffect(() => () => wsRef.current?.close(), [])

  function open() {
    if (wsRef.current) return
    const ws = new WebSocket(`${BASE_URL.replace(/^http/, 'ws')}/ws/teleop`)
    wsRef.current = ws
    ws.onmessage = (ev) => {
      try {
        const d = JSON.parse(ev.data as string) as { error?: string }
        if (d.error) { setError(d.error); ws.close() }
      } catch { /* ignore */ }
    }
    ws.onopen = () => {
      setError(null)
      const tick = setInterval(() => {
        if (ws.readyState !== WebSocket.OPEN) return clearInterval(tick)
        ws.send(JSON.stringify(cmd.current))
      }, 1000 / SEND_HZ)
      ws.onclose = () => { clearInterval(tick); wsRef.current = null; setDriving(false) }
    }
    ws.onerror = () => setError('could not open the drive channel')
  }

  function update(e: React.PointerEvent) {
    const el = padRef.current
    if (!el) return
    const r = el.getBoundingClientRect()
    const nx = ((e.clientX - r.left) / r.width) * 2 - 1     // -1 left, +1 right
    const ny = ((e.clientY - r.top) / r.height) * 2 - 1     // -1 top,  +1 down
    cmd.current = {
      vx: +(-ny * maxLinear).toFixed(3),                    // up = forward
      wz: +(-nx * (status?.max_linear ? 0.5 : 0.5)).toFixed(3),
    }
  }

  function start(e: React.PointerEvent) {
    if (!canDrive) return
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
    update(e); open(); setDriving(true)
  }

  function end() {
    cmd.current = { vx: 0, wz: 0 }
    wsRef.current?.send(JSON.stringify({ stop: true }))
    wsRef.current?.close()
    wsRef.current = null
    setDriving(false)
  }

  return (
    <div className="p-2 border-t border-bg-border">
      <div className="flex items-center justify-between mb-1">
        <span className="font-mono text-[10px] text-text-dim tracking-widest">DRIVE</span>
        <span className="font-mono text-[10px] text-text-dim">
          {maxLinear.toFixed(2)} m/s
        </span>
      </div>

      <div
        ref={padRef}
        onPointerDown={start}
        onPointerMove={(e) => driving && update(e)}
        onPointerUp={end}
        onPointerCancel={end}
        className={`relative h-24 rounded border select-none touch-none
          ${canDrive
            ? driving
              ? 'border-accent-green bg-accent-green/10 cursor-grabbing'
              : 'border-bg-border bg-bg-base cursor-grab hover:border-text-dim'
            : 'border-bg-border bg-bg-base opacity-40 cursor-not-allowed'}`}
      >
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <span className="font-mono text-[10px] text-text-dim text-center px-2">
            {canDrive
              ? driving ? 'driving — release to stop' : 'press and hold'
              : `nav is ${status?.nav_state ?? 'unknown'} — the speed guard and twist_mux live there`}
          </span>
        </div>
      </div>

      {error && (
        <div className="mt-1 font-mono text-[10px] text-accent-red leading-tight">{error}</div>
      )}

      <div className="mt-1 font-mono text-[9px] text-text-dim leading-tight">
        Not the e-stop. <span className="text-text-secondary">make teleop-nav</span> is.
      </div>
    </div>
  )
}
