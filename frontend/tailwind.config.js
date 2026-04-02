export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        console: {
          deep: '#ffffff',
          panel: '#f8fafc',
          surface: '#eef2ff',
          edge: '#cbd5e1',
          glow: '#1d4ed8',
          good: '#047857',
          warn: '#b45309',
          bad: '#b91c1c',
          ink: '#0f172a',
          muted: '#475569'
        }
      },
      fontFamily: {
        sans: ['Segoe UI', 'IBM Plex Sans', 'sans-serif']
      }
    },
  },
  plugins: [],
}
