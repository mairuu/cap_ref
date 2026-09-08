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

  it('returns grey for unknown labels', () => {
    expect(classColor('toaster')).toBe('#888888')
    expect(classColor('')).toBe('#888888')
  })

  it('treats sofa as same colour as couch', () => {
    expect(classColor('sofa')).toBe(classColor('couch'))
  })
})
