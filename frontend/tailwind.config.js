export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        console: {
          deep: '#0f1723',
          panel: '#162334',
          surface: '#1b2c40',
          edge: '#29405d',
          glow: '#4ec1d2',
          good: '#2da98a',
          warn: '#ef9a3d',
          bad: '#d85b5b',
          ink: '#e7eff7',
          muted: '#99adc2'
        }
      },
      fontFamily: {
        sans: ['Segoe UI', 'IBM Plex Sans', 'sans-serif']
      }
    },
  },
  plugins: [],
}
