/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        agri: {
          50: '#f2f9f3',
          100: '#e1f2e5',
          200: '#c5e5cd',
          300: '#9ad3a7',
          400: '#68b87c',
          500: '#439c58',
          600: '#327e44',
          700: '#296437',
          800: '#24502f',
          900: '#1f4228',
          950: '#0c2413',
        },
        earth: {
          50: '#fbf7f3',
          100: '#f5ede5',
          500: '#b4783f',
          800: '#643f21',
        },
        sun: {
          400: '#facc15',
          500: '#eab308',
        }
      },
      animation: {
        'pulse-slow': 'pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ripple': 'ripple 1.5s ease-out infinite',
      },
      keyframes: {
        ripple: {
          '0%': { transform: 'scale(0.9)', opacity: '1' },
          '100%': { transform: 'scale(1.6)', opacity: '0' },
        }
      }
    },
  },
  plugins: [],
}
