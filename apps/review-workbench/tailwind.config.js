import tailwindcssAnimate from "tailwindcss-animate"

export default {
    darkMode: ["class"],
    content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
  	extend: {
		colors: {
			background: '#0c0e10',
			foreground: '#e2e2e5',
			surface: '#121416',
			'surface-low': '#1a1c1e',
			'surface-container': '#1e2022',
			'surface-high': '#282a2c',
			'surface-highest': '#333537',
			card: '#121416',
			'card-foreground': '#e2e2e5',
			popover: '#1e2022',
			'popover-foreground': '#e2e2e5',
			primary: '#00f2ff',
			'primary-dim': '#99f7ff',
			'primary-on': '#00363a',
			'primary-foreground': '#00363a',
			secondary: '#ffaa00',
			'secondary-dim': '#fecb00',
			'secondary-on': '#452b00',
			'secondary-foreground': '#452b00',
			muted: '#1a1c1e',
			'muted-foreground': '#849495',
			accent: '#1e2022',
			'accent-foreground': '#e2e2e5',
			error: '#ffb4ab',
			'error-container': '#93000a',
			destructive: '#93000a',
			'destructive-foreground': '#ffb4ab',
			outline: '#747578',
			'outline-variant': '#3a494b',
			'on-surface': '#e2e2e5',
			'on-muted': '#849495',
			border: '#3a494b',
			input: '#3a494b',
			ring: '#00f2ff'
		},
  		fontFamily: {
  			headline: [
  				'Space Grotesk',
  				'sans-serif'
  			],
  			body: [
  				'Inter',
  				'sans-serif'
  			],
  			mono: [
  				'JetBrains Mono',
  				'monospace'
  			]
  		},
  		keyframes: {
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			}
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out'
  		}
  	}
  },
  plugins: [tailwindcssAnimate],
}
