export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0c0e10',
        surface: '#121416',
        'surface-low': '#1a1c1e',
        'surface-container': '#1e2022',
        'surface-high': '#282a2c',
        'surface-highest': '#333537',
        primary: '#00f2ff',
        'primary-dim': '#99f7ff',
        'primary-on': '#00363a',
        secondary: '#ffaa00',
        'secondary-dim': '#fecb00',
        'secondary-on': '#452b00',
        error: '#ffb4ab',
        'error-container': '#93000a',
        outline: '#747578',
        'outline-variant': '#3a494b',
        'on-surface': '#e2e2e5',
        'on-muted': '#849495',
      },
      fontFamily: {
        headline: ['"Space Grotesk"', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
