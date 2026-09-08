const CLASS_COLORS: Record<string, string> = {
  chair: '#4a9eff',
  bottle: '#3dd68c',
  couch: '#ff8c42',
  sofa: '#ff8c42',
  person: '#e05252',
  cup: '#f5c518',
  laptop: '#b47fff',
}

const DEFAULT_COLOR = '#888888'

export function classColor(label: string): string {
  return CLASS_COLORS[label.toLowerCase()] ?? DEFAULT_COLOR
}
