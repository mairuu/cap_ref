import { useState } from 'react'
import { stackApi, type StackComponent } from '../../api/stack'

const DOT: Record<string, string> = {
  ready:    'bg-accent-green',
  starting: 'bg-accent-yellow animate-pulse',
  stopping: 'bg-accent-yellow animate-pulse',
  crashed:  'bg-accent-red',
  stopped:  'bg-text-dim',
}

function Btn({ label, onClick, danger, disabled, title }: {
  label: string; onClick: () => void
  danger?: boolean; disabled?: boolean; title?: string
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`px-1.5 py-0.5 text-[10px] font-mono border rounded transition-colors
        disabled:opacity-30 disabled:cursor-not-allowed
        ${danger
          ? 'border-accent-red/40 text-accent-red hover:border-accent-red'
          : 'border-bg-border text-text-secondary hover:border-text-secondary'}`}
    >
      {label}
    </button>
  )
}

export function ComponentRow({ c, selected, onSelect }: {
  c: StackComponent
  selected: boolean
  onSelect: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const running = c.state === 'starting' || c.state === 'ready' || c.state === 'stopping'

  async function act(fn: () => Promise<unknown>, confirmText?: string) {
    // A destructive action gets a sentence, not a generic "are you sure" --
    // the bridge already knows WHY each one is dangerous, so show that.
    if (confirmText && !window.confirm(confirmText)) return
    setBusy(true); setError(null)
    try { await fn() } catch (e) { setError((e as Error).message) }
    finally { setBusy(false) }
  }

  return (
    <div
      className={`px-2 py-1.5 border-b border-bg-border cursor-pointer
        ${selected ? 'bg-bg-elevated' : 'hover:bg-bg-elevated/50'}`}
      onClick={onSelect}
    >
      <div className="flex items-center gap-2">
        <span className={`inline-block w-2 h-2 rounded-full shrink-0 ${DOT[c.state] ?? 'bg-text-dim'}`} />
        <span className="font-mono text-xs text-text-primary w-20 shrink-0">{c.name}</span>
        <span className="font-mono text-[10px] text-text-dim flex-1 truncate">
          {c.state === 'crashed'
            ? `exit ${c.dead_status ?? '?'}`
            : c.uptime_s != null ? `${Math.round(c.uptime_s)}s` : ''}
        </span>

        {!c.managed ? (
          <span className="font-mono text-[10px] text-text-dim">external</span>
        ) : (
          <div className="flex gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
            {!running && (
              <Btn label="start" disabled={busy} onClick={() => act(() => stackApi.start(c.name))} />
            )}
            {running && (
              <Btn label="stop" danger disabled={busy}
                   title={c.warn ?? undefined}
                   onClick={() => act(() => stackApi.stop(c.name),
                     c.warn ? `Stop ${c.name}?\n\n${c.warn}` : undefined)} />
            )}
            <Btn
              label="restart"
              disabled={busy || !c.restartable || !running}
              title={c.restartable
                ? undefined
                : `${c.name} is deliberately not restartable from here. ${c.warn ?? ''}`}
              onClick={() => act(() => stackApi.restart(c.name))}
            />
          </div>
        )}
      </div>

      {/* Failing checks, inline. This is the difference between "nav is not
          ready" and "the BT navigator is not accepting goals yet". */}
      {selected && c.checks.length > 0 && (
        <div className="mt-1 pl-4 space-y-0.5">
          {c.checks.map((ck, i) => (
            <div key={i} className="font-mono text-[10px] leading-tight">
              <span className={ck.ok ? 'text-accent-green' : 'text-accent-red'}>
                {ck.ok ? '+' : '-'}
              </span>{' '}
              <span className="text-text-secondary">{ck.detail}</span>
              {!ck.ok && ck.why && (
                <div className="pl-3 text-text-dim">→ {ck.why}</div>
              )}
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="mt-1 pl-4 font-mono text-[10px] text-accent-red leading-tight">
          {error}
        </div>
      )}
    </div>
  )
}
