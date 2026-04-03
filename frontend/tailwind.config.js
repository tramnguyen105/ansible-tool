export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        console: {
          deep: '#f4efe4',
          panel: '#fffdf8',
          surface: '#f7f1e6',
          edge: '#d8cfc1',
          glow: '#0f766e',
          good: '#0f766e',
          warn: '#b45309',
          bad: '#b91c1c',
          ink: '#14213d',
          muted: '#5c677d',
          accent: '#d97706'
        }
      },
      fontFamily: {
        sans: ['"Aptos"', '"IBM Plex Sans"', '"Segoe UI"', 'sans-serif']
      }
    },
  },
  plugins: [],
}
