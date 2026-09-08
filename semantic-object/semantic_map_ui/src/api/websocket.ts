import { BASE_URL } from './client'

type BinaryType = 'blob' | 'arraybuffer'

interface ReconnectingWsOptions<T> {
  path: string
  binaryType?: BinaryType
  onMessage(data: T): void
  onOpen?(): void
  onClose?(): void
}

const WS_BASE = BASE_URL.replace(/^http/, 'ws')

export class ReconnectingWs<T = unknown> {
  private ws: WebSocket | null = null
  private retries = 0
  private retryTimer: ReturnType<typeof setTimeout> | null = null
  private stopped = false

  constructor(private readonly opts: ReconnectingWsOptions<T>) {
    this.connect()
  }

  private connect() {
    if (this.stopped) return

    const ws = new WebSocket(`${WS_BASE}${this.opts.path}`)
    if (this.opts.binaryType) ws.binaryType = this.opts.binaryType
    this.ws = ws

    ws.onopen = () => {
      this.retries = 0
      this.opts.onOpen?.()
    }

    ws.onmessage = (ev) => {
      this.opts.onMessage(ev.data as T)
    }

    ws.onclose = () => {
      this.opts.onClose?.()
      this.scheduleRetry()
    }

    ws.onerror = () => {
      ws.close()
    }
  }

  private scheduleRetry() {
    if (this.stopped) return
    const delay = Math.min(30_000, 1_000 * 2 ** this.retries)
    this.retries++
    this.retryTimer = setTimeout(() => this.connect(), delay)
  }

  destroy() {
    this.stopped = true
    if (this.retryTimer !== null) clearTimeout(this.retryTimer)
    this.ws?.close()
    this.ws = null
  }
}

export function createStateWs(
  onMessage: (msg: unknown) => void,
  onOpen: () => void,
  onClose: () => void,
) {
  return new ReconnectingWs<string>({
    path: '/ws/state',
    onOpen,
    onClose,
    onMessage(raw) {
      try {
        onMessage(JSON.parse(raw))
      } catch {
        console.warn('malformd frame');
      }
    },
  })
}

export function createCameraWs(onBlob: (blob: Blob) => void) {
  return new ReconnectingWs<Blob>({
    path: '/ws/camera',
    binaryType: 'blob',
    onMessage: (raw) => {
      const imageBlob = new Blob([raw], { type: 'image/jpeg' })
      onBlob(imageBlob)
    },
  })
}
