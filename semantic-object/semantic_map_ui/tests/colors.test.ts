import { describe, it, expect } from 'vitest'
import { classColor } from '../src/utils/colors'

describe('classColor', () => {
  it('returns correct colour for known labels', () => {
    expect(classColor('chair')).toBe('#4a9eff')
    expect(classColor('bottle')).toBe('#3dd68c')
    expect(classColor('couch')).toBe('#ff8c42')
    expect(classColor('person')).toBe('#e05252')
    expect(classColor('cup')).toBe('#f5c518')
    expect(classColor('laptop')).toBe('#b47fff')
  })

  it('is case-insensitive', () => {
    expect(classColor('CHAIR')).toBe('#4a9eff')
    expect(classColor('Bottle')).toBe('#3dd68c')
  })

  // CHANGED 18 Sep 2026. This used to assert classColor('toaster') === grey.
  // Flat grey for every unmapped class meant `table` and `door` -- two of the
  // three landmarks the bridge's own mock mode publishes -- were the same
  // colour as each other and as everything else the robot detects outside the
  // seven-entry table. Colour is the legend, so that made the legend useless
  // past seven classes. Unknown labels now hash to a stable hue instead.
  it('returns grey only for an empty label', () => {
    expect(classColor('')).toBe('#888888')
    expect(classColor('toaster')).not.toBe('#888888')
  })

  it('gives unknown labels a stable colour', () => {
    expect(classColor('table')).toBe(classColor('table'))
    expect(classColor('TABLE')).toBe(classColor('table'))
  })

  it('gives different unknown labels different colours', () => {
    expect(classColor('table')).not.toBe(classColor('door'))
  })

  it('treats sofa as same colour as couch', () => {
    expect(classColor('sofa')).toBe(classColor('couch'))
  })
})
