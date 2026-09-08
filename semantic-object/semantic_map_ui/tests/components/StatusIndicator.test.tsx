import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { useStore } from '../../src/state/store'
import { StatusIndicator } from '../../src/components/StatusIndicator'

beforeEach(() => {
  useStore.setState({
    rosConnected: false,
    wsConnected: false,
    isMock: false,
    landmarkCount: 0,
    lastUpdateAt: null,
  })
})

describe('StatusIndicator', () => {
  it('shows disconnected when rosConnected is false', () => {
    render(<StatusIndicator />)
    expect(screen.getByText('disconnected')).toBeInTheDocument()
  })

  it('shows connected when rosConnected is true', () => {
    useStore.setState({ rosConnected: true })
    render(<StatusIndicator />)
    expect(screen.getByText('connected')).toBeInTheDocument()
  })

  it('shows MOCK badge when isMock is true', () => {
    useStore.setState({ isMock: true })
    render(<StatusIndicator />)
    expect(screen.getByText('MOCK')).toBeInTheDocument()
  })

  it('does not show MOCK badge when isMock is false', () => {
    render(<StatusIndicator />)
    expect(screen.queryByText('MOCK')).not.toBeInTheDocument()
  })

  it('shows landmark count', () => {
    useStore.setState({ landmarkCount: 7 })
    render(<StatusIndicator />)
    expect(screen.getByText('7')).toBeInTheDocument()
    expect(screen.getByText('objects')).toBeInTheDocument()
  })

  it('shows "ws live" when wsConnected', () => {
    useStore.setState({ wsConnected: true })
    render(<StatusIndicator />)
    expect(screen.getByText('ws live')).toBeInTheDocument()
  })

  it('shows "ws offline" when ws disconnected', () => {
    render(<StatusIndicator />)
    expect(screen.getByText('ws offline')).toBeInTheDocument()
  })

  it('shows "—" for last update when no messages received', () => {
    render(<StatusIndicator />)
    expect(screen.getByText('updated —')).toBeInTheDocument()
  })

  it('shows elapsed time when lastUpdateAt is set', () => {
    vi.useFakeTimers()
    useStore.setState({ lastUpdateAt: Date.now() - 3_000 })
    render(<StatusIndicator />)
    expect(screen.getByText('updated 3s ago')).toBeInTheDocument()
    vi.useRealTimers()
  })
})
