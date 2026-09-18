// Landmark colour by class.
//
// COLOUR IS THE LEGEND. The map draws a dot per landmark and the object panel
// draws a matching swatch; nothing else tells the viewer which class is which,
// so a colour has to be stable for a given class across sessions and machines.
//
// The seven entries below were hand-picked against the dark panel and the
// light mapped-free-space region, and are pinned by tests/colors.test.ts.
// Everything else used to fall through to flat grey -- which meant every class
// outside this table was the SAME colour as every other, including `table` and
// `door` in the bridge's own mock data. yolo26 emits far more classes than
// seven, so the fallback now hashes the label to a hue instead. Deterministic,
// needs no maintenance as new classes appear, and two classes on screen at once
// are very unlikely to collide. 18 Sep 2026.
const CLASS_COLORS: Record<string, string> = {
  chair: '#4a9eff',
  bottle: '#3dd68c',
  couch: '#ff8c42',
  sofa: '#ff8c42',
  person: '#e05252',
  cup: '#f5c518',
  laptop: '#b47fff',
}

// Kept for the empty-label edge case only. A real class never gets grey now.
const DEFAULT_COLOR = '#888888'

// Saturation and lightness are fixed, not hashed: they are what keeps a dot
// legible against BOTH #0d0d0d and mapped free space #f0f0f0. Only the hue
// varies, so every generated colour sits in the same readable band.
const FALLBACK_SATURATION = 65
const FALLBACK_LIGHTNESS = 60

// djb2-ish. Any stable string hash would do; this one is short and has no
// dependencies. `>>> 0` keeps it an unsigned 32-bit value so the modulo below
// cannot return a negative hue.
function hashHue(label: string): number {
  let h = 0
  for (let i = 0; i < label.length; i++) {
    h = (h * 31 + label.charCodeAt(i)) >>> 0
  }
  return h % 360
}

export function classColor(label: string): string {
  const key = label.toLowerCase()
  if (!key) return DEFAULT_COLOR
  return (
    CLASS_COLORS[key] ??
    `hsl(${hashHue(key)}, ${FALLBACK_SATURATION}%, ${FALLBACK_LIGHTNESS}%)`
  )
}
