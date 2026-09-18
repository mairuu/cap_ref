import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useStore } from '../../src/state/store'
import { ObjectList } from '../../src/components/ObjectList'
import type { Landmark } from '../../src/state/types'

function lm(over: Partial<Landmark> & { id: string }): Landmark {
  return {
    class_label: 'chair',
    x: 1.5,
    y: 2.0,
    confidence: 0.92,
    seen_count: 10,
    stale: false,
    ...over,
  }
}

beforeEach(() => {
  useStore.setState({
    landmarks: [],
    robotPose: null,
    selectedLandmarkId: null,
    followRobot: true,
    view: { panX: 0, panY: 0, scale: 80 },
  })
})

describe('ObjectList', () => {
  it('shows the empty state when nothing has been detected', () => {
    render(<ObjectList />)
    expect(screen.getByText('NO OBJECTS DETECTED')).toBeInTheDocument()
  })

  it('renders a row per landmark with class, position, confidence and count', () => {
    useStore.setState({ landmarks: [lm({ id: 'a' })] })
    render(<ObjectList />)

    const row = within(screen.getByRole('listitem'))
    expect(row.getByText('chair')).toBeInTheDocument()
    expect(row.getByText('1.50, 2.00 m')).toBeInTheDocument()
    expect(row.getByText('92% · seen 10×')).toBeInTheDocument()
    expect(screen.queryByText('NO OBJECTS DETECTED')).not.toBeInTheDocument()
  })

  it('orders rows by distance from the robot', () => {
    useStore.setState({
      landmarks: [
        lm({ id: 'far', class_label: 'laptop', x: 9, y: 0 }),
        lm({ id: 'near', class_label: 'cup', x: 1, y: 0 }),
      ],
      robotPose: { x: 0, y: 0, yaw: 0 },
    })
    render(<ObjectList />)

    const rows = screen.getAllByRole('listitem')
    expect(rows[0]).toHaveTextContent('cup')
    expect(rows[1]).toHaveTextContent('laptop')
  })

  it('selects a landmark when its row is clicked', async () => {
    const user = userEvent.setup()
    useStore.setState({ landmarks: [lm({ id: 'a' })] })
    render(<ObjectList />)

    await user.click(screen.getByRole('button', { name: /^chair/ }))

    expect(useStore.getState().selectedLandmarkId).toBe('a')
  })

  it('deselects when the selected row is clicked again', async () => {
    const user = userEvent.setup()
    useStore.setState({ landmarks: [lm({ id: 'a' })], selectedLandmarkId: 'a' })
    render(<ObjectList />)

    await user.click(screen.getByRole('button', { name: /^chair/ }))

    expect(useStore.getState().selectedLandmarkId).toBeNull()
  })

  it('marks the selected row as pressed', () => {
    useStore.setState({ landmarks: [lm({ id: 'a' })], selectedLandmarkId: 'a' })
    render(<ObjectList />)

    expect(screen.getByRole('button', { name: /^chair/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('tags a stale landmark', () => {
    useStore.setState({ landmarks: [lm({ id: 'a', stale: true })] })
    render(<ObjectList />)

    expect(screen.getByText('stale')).toBeInTheDocument()
  })

  it('counts landmarks per class', () => {
    useStore.setState({
      landmarks: [
        lm({ id: 'a', class_label: 'chair' }),
        lm({ id: 'b', class_label: 'chair' }),
        lm({ id: 'c', class_label: 'laptop' }),
      ],
    })
    render(<ObjectList />)

    // Two ids for one real chair is what a track-id split looks like, so this
    // chip is the duplicate-landmarks metric on screen.
    expect(screen.getByText('×2')).toBeInTheDocument()
    expect(screen.getByText('×1')).toBeInTheDocument()
  })

  it('turns follow off before centring, so the RAF loop cannot overwrite the view', async () => {
    const user = userEvent.setup()
    useStore.setState({ landmarks: [lm({ id: 'a' })], followRobot: true })
    // jsdom has no canvas layout; the helper reads width/height off the element.
    const canvas = document.createElement('canvas')
    canvas.width = 800
    canvas.height = 600
    document.body.appendChild(canvas)

    render(<ObjectList />)
    await user.click(screen.getByRole('button', { name: /Centre map on chair/ }))

    expect(useStore.getState().followRobot).toBe(false)
    expect(useStore.getState().view.panX).toBeCloseTo(800 / 2 - 1.5 * 80)
    expect(useStore.getState().view.panY).toBeCloseTo(600 / 2 + 2.0 * 80)

    canvas.remove()
  })

  it('does not throw when there is no canvas to centre on', async () => {
    const user = userEvent.setup()
    useStore.setState({ landmarks: [lm({ id: 'a' })] })
    render(<ObjectList />)

    await user.click(screen.getByRole('button', { name: /Centre map on chair/ }))

    expect(useStore.getState().followRobot).toBe(true)
  })
})
