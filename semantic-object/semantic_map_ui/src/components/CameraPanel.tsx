import { useEffect, useRef, useState } from 'react'
import { createCameraWs } from '../api/websocket'
import { StatusIndicator } from './StatusIndicator'
import { ClearButton } from './ClearButton'
import { ObjectList } from './ObjectList'

export function CameraPanel() {
  const imgRef    = useRef<HTMLImageElement>(null)
  const prevUrl   = useRef<string | null>(null)
  // NO SIGNAL used to be rendered unconditionally -- the comment below it said
  // "placeholder when no frame has arrived yet" but nothing ever tracked that,
  // so it sat over a perfectly good feed forever. Reported 16 Sep. The camera
  // chain was fine throughout: /image/compressed at 15.3 Hz, bridge
  // ros_connected true.
  const [hasFrame, setHasFrame] = useState(false)

  useEffect(() => {
    const ws = createCameraWs((blob) => {
      const url = URL.createObjectURL(blob)
      if (imgRef.current) {
        imgRef.current.src = url
        // Revoke the previous URL after the image loads to avoid memory leaks
        imgRef.current.onload = () => {
          if (prevUrl.current) URL.revokeObjectURL(prevUrl.current)
          prevUrl.current = url
          setHasFrame(true)
        }
      } else {
        URL.revokeObjectURL(url)
      }
    })

    return () => {
      ws.destroy()
      if (prevUrl.current) URL.revokeObjectURL(prevUrl.current)
    }
  }, [])

  // overflow-hidden, not overflow-y-auto: CAMERA and STATUS stay put and the
  // OBJECTS list scrolls on its own. Scrolling the whole panel would push the
  // camera feed off-screen as landmarks accumulate, which is the wrong thing to
  // lose during a demo.
  return (
    <aside className="flex flex-col gap-4 w-full md:w-[340px] shrink-0 bg-bg-panel border-l border-bg-border p-4 overflow-hidden">
      {/* Camera feed */}
      <div className="shrink-0">
        <div className="font-mono text-xs text-text-secondary mb-2 tracking-wider">
          CAMERA
        </div>
        <div className="relative bg-bg-base border border-bg-border rounded overflow-hidden aspect-video flex items-center justify-center">
          <img
            ref={imgRef}
            alt="Camera feed"
            className="w-full h-full object-cover"
            onError={(e) => {
              // keep showing the last frame on decode error
              e.currentTarget.onerror = null
            }}
          />
          {/* Placeholder, ONLY until the first frame decodes. */}
          {!hasFrame && (
            <span className="absolute font-mono text-xs text-text-dim select-none">
              NO SIGNAL
            </span>
          )}
        </div>
      </div>

      {/* Status */}
      <div className="shrink-0">
        <div className="font-mono text-xs text-text-secondary mb-2 tracking-wider">
          STATUS
        </div>
        <StatusIndicator />
      </div>

      {/* Detected objects -- the only part of the panel that scrolls */}
      <ObjectList />

      {/* Controls */}
      <div className="shrink-0">
        <ClearButton />
      </div>
    </aside>
  )
}
