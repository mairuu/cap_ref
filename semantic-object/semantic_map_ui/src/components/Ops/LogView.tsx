import { useEffect, useRef, useState } from 'react'
import { createLogWs } from '../../api/stack'

export function LogView({ component }: { component: string | null }) {
  const [text, setText] = useState('')
  const boxRef = useRef<HTMLPreElement>(null)
  const pinned = useRef(true)

  useEffect(() => {
    setText('')
    if (!component) return
    const ws = createLogWs(component, setText)
    return () => ws.destroy()
  }, [component])

  // Follow the tail, but stop fighting the operator the moment they scroll up
  // to read something -- which is exactly when a log is worth reading.
  useEffect(() => {
    const el = boxRef.current
    if (el && pinned.current) el.scrollTop = el.scrollHeight
  }, [text])

  if (!component) {
    return (
      <div className="flex-1 flex items-center justify-center font-mono text-[10px] text-text-dim">
        select a component
      </div>
    )
  }

  return (
    <pre
      ref={boxRef}
      onScroll={(e) => {
        const el = e.currentTarget
        pinned.current = el.scrollHeight - el.scrollTop - el.clientHeight < 24
      }}
      className="flex-1 overflow-auto px-2 py-1 font-mono text-[10px] leading-snug
                 text-text-secondary whitespace-pre-wrap break-words"
    >
      {text || `waiting for output from ${component}…`}
    </pre>
  )
}
