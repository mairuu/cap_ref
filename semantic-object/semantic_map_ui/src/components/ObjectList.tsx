import { useStore } from '../state/store'
import { sortLandmarks, groupByClass } from '../utils/landmarks'
import { classColor } from '../utils/colors'
import { centreViewOn } from './Map/coords'
import type { Landmark } from '../state/types'

/**
 * Centre the map on a landmark.
 *
 * followRobot MUST go off first. The RAF loop recomputes panX/panY from the
 * robot pose every frame while follow is on, so a view set underneath it is
 * overwritten before it is ever painted and the click looks broken. Turning it
 * off is also what a manual drag already does, so the two never fight.
 *
 * The canvas is found the same way App.tsx's RESET button finds it. Not
 * elegant, but it is the existing idiom here and inventing a second one for
 * the same job would be worse.
 */
function centreOn(lm: Landmark) {
  const canvas = document.querySelector('canvas')
  if (!canvas) return

  const store = useStore.getState()
  store.setFollowRobot(false)
  store.setView(centreViewOn(store.view, canvas.width, canvas.height, lm.x, lm.y))
}

function ClassSummary() {
  const landmarks = useStore((s) => s.landmarks)
  const groups = groupByClass(landmarks)

  if (groups.length === 0) return null

  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1 mb-3">
      {groups.map((g) => (
        <span key={g.label} className="flex items-center gap-1.5 font-mono text-xs">
          <span
            className="inline-block w-2 h-2 rounded-full shrink-0"
            style={{ backgroundColor: g.color }}
          />
          <span className="text-text-secondary">{g.label}</span>
          <span className="text-text-primary">×{g.count}</span>
        </span>
      ))}
    </div>
  )
}

function ObjectRow({ lm }: { lm: Landmark }) {
  const selectedId = useStore((s) => s.selectedLandmarkId)
  const selected = lm.id === selectedId

  return (
    <li>
      <div
        className={`w-full flex items-start gap-2 px-2 py-1.5 rounded border-l-2 transition-colors ${
          selected
            ? 'bg-accent-blue/10 border-l-accent-blue'
            : 'border-l-transparent hover:bg-bg-elevated'
        }`}
        style={{ opacity: lm.stale ? 0.4 : 1 }}
      >
        <button
          type="button"
          // Toggle lives here, not in the store: clicking the selected row
          // again clears it. Matches how App.tsx's f/c keys read-then-call.
          onClick={() => useStore.getState().selectLandmark(selected ? null : lm.id)}
          aria-pressed={selected}
          className="flex-1 min-w-0 flex items-start gap-2 text-left"
        >
          <span
            className="inline-block w-2.5 h-2.5 rounded-full shrink-0 mt-1"
            style={{ backgroundColor: classColor(lm.class_label) }}
          />
          <span className="min-w-0 flex-1">
            <span className="flex items-baseline gap-1.5">
              <span className="font-mono text-sm text-text-primary truncate">
                {lm.class_label}
              </span>
              {lm.stale && (
                <span className="font-mono text-[10px] text-text-dim shrink-0">stale</span>
              )}
            </span>
            {/* The published map-frame position. During the tape-measure
                protocol this is the number being compared against the tape, so
                it is readable here instead of only in a terminal. */}
            <span className="block font-mono text-xs text-text-secondary tabular-nums">
              {lm.x.toFixed(2)}, {lm.y.toFixed(2)} m
            </span>
            <span className="block font-mono text-[10px] text-text-dim tabular-nums">
              {(lm.confidence * 100).toFixed(0)}% · seen {lm.seen_count}×
            </span>
          </span>
        </button>

        <button
          type="button"
          onClick={() => centreOn(lm)}
          title="Centre map here (turns FOLLOW off)"
          aria-label={`Centre map on ${lm.class_label}`}
          className="shrink-0 px-1.5 py-0.5 font-mono text-xs text-text-dim hover:text-text-primary border border-transparent hover:border-bg-border rounded transition-colors"
        >
          ⌖
        </button>
      </div>
    </li>
  )
}

export function ObjectList() {
  const landmarks = useStore((s) => s.landmarks)
  const robotPose = useStore((s) => s.robotPose)
  const sorted = sortLandmarks(landmarks, robotPose)

  return (
    <div className="flex flex-col min-h-0 flex-1">
      <div className="font-mono text-xs text-text-secondary mb-2 tracking-wider shrink-0">
        OBJECTS{' '}
        <span className="text-text-dim">
          {landmarks.length > 0 && `(${landmarks.length})`}
        </span>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <ClassSummary />

        {sorted.length === 0 ? (
          // Says "nothing found" rather than looking like a broken panel. The
          // same idiom as CameraPanel's NO SIGNAL.
          <div className="font-mono text-xs text-text-dim py-2">
            NO OBJECTS DETECTED
          </div>
        ) : (
          <ul className="space-y-0.5">
            {sorted.map((lm) => (
              <ObjectRow key={lm.id} lm={lm} />
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
