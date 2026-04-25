import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        clay: {
          50: '#faf7f2',
          100: '#f1eade',
          200: '#e3d7c2',
          300: '#cfbb9c',
          400: '#b89a73',
          500: '#9c7c54',
          600: '#7d6243',
          700: '#5e4a34',
          800: '#3f3225',
          900: '#241c13',
        },
        sun: {
          400: '#ffb547',
          500: '#ff8a00',
          600: '#e26a00',
        },
        signal: {
          wage: '#16a34a',
          growth: '#2563eb',
          risk: '#dc2626',
        },
      },
      boxShadow: {
        card: '0 1px 2px rgba(0,0,0,0.04), 0 8px 24px -8px rgba(60,40,15,0.18)',
      },
      backgroundImage: {
        'sunrise':
          'radial-gradient(120% 80% at 0% 0%, #fff7ea 0%, #fdecd2 35%, #f6d6a3 75%, #e8b673 100%)',
      },
    },
  },
  plugins: [],
} satisfies Config;
