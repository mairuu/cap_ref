import type { Landmark, RobotPose } from '../state/types'
import { classColor } from './colors'

export interface ClassGroup {
  label: string
  color: string
  count: number
}

export function distance(ax: number, ay: number, bx: number, by: number): number {
  return Math.hypot(ax - bx, ay - by)
}

/**
 * Landmarks in the order the object panel lists them.
 *
 * NEAREST THE ROBOT FIRST. This is the order the demo is narrated in ("the
 * nearest chair"), and it is the same choice go_to_object.py makes when it is
 * asked to drive to a class -- it picks the landmark nearest the ROBOT, not
 * the one nearest some observation. So the top row of the panel is the row the
 * stretch goal would drive to, which makes the list a preview of that command
 * rather than an unrelated view.
 *
 * Before the first pose arrives robotPose is null and there is no distance to
 * sort by. Falling back to insertion order would let rows jump around as the
 * websocket rebuilds the array, so the fallback is seen_count descending (the
 * best-established landmarks first) and then class label, which is total and
 * stable.
 *
 * Pure: returns a new array, never mutates the input. The store's array is
 * handed straight to the canvas draw loop and must not be reordered under it.
 */
export function sortLandmarks(
  landmarks: Landmark[],
  robotPose: RobotPose | null,
): Landmark[] {
  const sorted = [...landmarks]

  if (robotPose) {
    sorted.sort(
      (a, b) =>
        distance(robotPose.x, robotPose.y, a.x, a.y) -
        distance(robotPose.x, robotPose.y, b.x, b.y),
    )
    return sorted
  }

  sorted.sort(
    (a, b) =>
      b.seen_count - a.seen_count ||
      a.class_label.localeCompare(b.class_label) ||
      a.id.localeCompare(b.id),
  )
  return sorted
}

/**
 * Per-class counts, which double as the colour legend.
 *
 * Worth more than a tally on this robot: P5 keys "same object again" on the
 * YOLO track id, and track ids churn (144 distinct ids in 301 s on 16 Sep, with
 * chair holding both 329 and 230). A chair that picks up a second id becomes a
 * second landmark, so `chair x2` on screen with one real chair in the room IS
 * the duplicate-landmarks metric, visible live instead of after the fact.
 */
export function groupByClass(landmarks: Landmark[]): ClassGroup[] {
  const counts = new Map<string, number>()
  for (const lm of landmarks) {
    counts.set(lm.class_label, (counts.get(lm.class_label) ?? 0) + 1)
  }

  return [...counts.entries()]
    .map(([label, count]) => ({ label, color: classColor(label), count }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label))
}
