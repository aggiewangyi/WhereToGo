/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: { 50: '#fff7ed', 100: '#ffedd5', 200: '#fed7aa', 300: '#fdba74', 400: '#fb923c', 500: '#FF6B35', 600: '#ea580c', 700: '#c2410c', 800: '#9a3412', 900: '#7c2d12' },
        accent:  { 50: '#ecfeff', 100: '#cffafe', 200: '#a5f3fc', 300: '#67e8f9', 400: '#22d3ee', 500: '#00B4D8', 600: '#0891b2', 700: '#0e7490', 800: '#155e75', 900: '#164e63' },
      },
      fontFamily: {
        sans: ['Outfit', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'],
        display: ['Outfit', 'PingFang SC', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        'glow-sm': '0 0 20px -5px rgba(45, 212, 191, 0.35)',
        'glow-md': '0 0 45px -10px rgba(45, 212, 191, 0.4)',
        panel: 'inset 0 1px 0 rgba(255,255,255,0.06), 0 24px 48px -24px rgba(0,0,0,0.65)',
      },
      backgroundImage: {
        'grid-tech':
          'linear-gradient(rgba(45,212,191,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(45,212,191,0.04) 1px, transparent 1px)',
      },
    },
  },
  plugins: [],
}
