import { useEffect, useRef } from 'react'
import { createCameraWs } from '../api/websocket'
import { StatusIndicator } from './StatusIndicator'
import { ClearButton } from './ClearButton'

export function CameraPanel() {
  const imgRef    = useRef<HTMLImageElement>(null)
  const prevUrl   = useRef<string | null>(null)

  useEffect(() => {
    const ws = createCameraWs((blob) => {
      const url = URL.createObjectURL(blob)
      if (imgRef.current) {
        imgRef.current.src = url
        // Revoke the previous URL after the image loads to avoid memory leaks
        imgRef.current.onload = () => {
          if (prevUrl.current) URL.revokeObjectURL(prevUrl.current)
          prevUrl.current = url
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

  return (
    <aside className="flex flex-col gap-4 w-full md:w-[300px] shrink-0 bg-bg-panel border-l border-bg-border p-4 overflow-y-auto">
      {/* Camera feed */}
      <div>
        <div className="font-mono text-xs text-text-secondary mb-2 tracking-wider">
          CAMERA
        </div>
        <div className="bg-bg-base border border-bg-border rounded overflow-hidden aspect-video flex items-center justify-center">
          <img
            ref={imgRef}
            alt="Camera feed"
            className="w-full h-full object-cover"
            onError={(e) => {
              // keep showing the last frame on decode error
              e.currentTarget.onerror = null
            }}
          />
          {/* Placeholder when no frame has arrived yet */}
          <span className="absolute font-mono text-xs text-text-dim select-none">
            NO SIGNAL
          </span>
        </div>
      </div>

      {/* Status */}
      <div>
        <div className="font-mono text-xs text-text-secondary mb-2 tracking-wider">
          STATUS
        </div>
        <StatusIndicator />
      </div>

      {/* Controls */}
      <div className="mt-auto">
        <ClearButton />
      </div>
    </aside>
  )
}
