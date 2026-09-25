import { useEffect, useState } from 'react'
import {
  createStackWs, stackApi,
  type ControlStatus, type StackSnapshot,
} from '../../api/stack'
import { ComponentRow } from './ComponentRow'
import { LogView } from './LogView'
import { DrivePad } from './DrivePad'

const CONTROL_POLL_MS = 2_000

export function OpsDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [snap, setSnap] = useState<StackSnapshot | null>(null)
  const [control, setControl] = useState<ControlStatus | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    const ws = createStackWs(setSnap)
    const poll = setInterval(
      () => stackApi.control().then(setControl).catch(() => setControl(null)),
      CONTROL_POLL_MS)
    stackApi.control().then(setControl).catch(() => setControl(null))
    return () => { ws.destroy(); clearInterval(poll) }
  }, [open])

  if (!open) return null

  const components = snap?.components ?? []
  const lastError = snap?.events.filter((e) => e.level === 'error').slice(-1)[0]

  async function run(fn: () => Promise<unknown>, confirmText?: string) {
    if (confirmText && !window.confirm(confirmText)) return
    setBusy(true); setError(null)
    try { await fn() } catch (e) { setError((e as Error).message) }
    finally { setBusy(false) }
  }

  return (
    <aside className="w-full md:w-96 shrink-0 flex flex-col border-l border-bg-border bg-bg-panel">
      <header className="flex items-center justify-between px-2 py-1.5 border-b border-bg-border">
        <span className="font-mono text-[10px] text-text-dim tracking-widest">STACK</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => run(() => stackApi.up('demo'))}
            disabled={busy}
            className="px-2 py-0.5 text-[10px] font-mono border border-accent-green/40
                       text-accent-green rounded hover:border-accent-green disabled:opacity-30"
          >START ALL</button>
          <button
            onClick={() => run(() => stackApi.down('demo'),
              'Stop the whole stack?\n\nThis stops every component it started, in reverse order. The map is not saved.')}
            disabled={busy}
            className="px-2 py-0.5 text-[10px] font-mono border border-bg-border
                       text-text-secondary rounded hover:border-text-secondary disabled:opacity-30"
          >STOP ALL</button>
          <button
            onClick={onClose}
            className="px-1.5 py-0.5 text-[10px] font-mono text-text-dim hover:text-text-secondary"
            title="close (O)"
          >✕</button>
        </div>
      </header>

      {/* The one red button. It does NOT publish a Twist -- it stops `nav`,
          which takes twist_mux and the speed guard with it and halts the
          wheels on diff_cont's cmd_vel_timeout. A designed-in safe state
          beats a message that can be overtaken. */}
      <button
        onClick={() => run(() => stackApi.estop(),
          'Stop navigation now?\n\nThis takes down Nav2, twist_mux and the speed guard. The wheels halt. Bringing it back is a restart of nav.')}
        disabled={busy || !control?.nav_ready}
        className="mx-2 my-1.5 py-1.5 text-[11px] font-mono tracking-widest rounded
                   border border-accent-red/50 text-accent-red bg-accent-red/10
                   hover:bg-accent-red/20 disabled:opacity-25 disabled:cursor-not-allowed"
      >
        ■ STOP NAVIGATION
      </button>

      <div className="overflow-y-auto max-h-[45%] border-y border-bg-border">
        {components.length === 0 && (
          <div className="px-2 py-3 font-mono text-[10px] text-text-dim">
            no stack console — is the bridge running on the robot?
          </div>
        )}
        {components.map((c) => (
          <ComponentRow
            key={c.name}
            c={c}
            selected={selected === c.name}
            onSelect={() => setSelected(selected === c.name ? null : c.name)}
          />
        ))}
      </div>

      {(error || lastError) && (
        <div className="px-2 py-1 font-mono text-[10px] text-accent-red border-b border-bg-border leading-tight">
          {error ?? lastError?.text}
        </div>
      )}

      <div className="flex items-center justify-between px-2 py-1 border-b border-bg-border">
        <span className="font-mono text-[10px] text-text-dim tracking-widest">
          {selected ? `LOG · ${selected}` : 'LOG'}
        </span>
        {snap?.readiness_age_s != null && (
          <span className="font-mono text-[10px] text-text-dim">
            checked {Math.round(snap.readiness_age_s)}s ago
          </span>
        )}
      </div>

      <LogView component={selected} />
      <DrivePad status={control} />
    </aside>
  )
}
