/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      colors: {
        bg: {
          base: '#0d0d0d',
          panel: '#141414',
          elevated: '#1a1a1a',
          border: '#2a2a2a',
        },
        accent: {
          blue: '#4a9eff',
          green: '#3dd68c',
          yellow: '#f5c518',
          red: '#e05252',
        },
        text: {
          primary: '#e8e8e8',
          secondary: '#888888',
          dim: '#555555',
        },
      },
    },
  },
  plugins: [],
}
