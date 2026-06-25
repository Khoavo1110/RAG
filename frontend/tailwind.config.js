/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'background': '#081425',
        'surface': '#081425',
        'surface-container-lowest': '#040e1f',
        'surface-container-low': '#111c2d',
        'surface-container': '#152031',
        'surface-container-high': '#1f2a3c',
        'surface-container-highest': '#2a3548',
        'primary': '#bec6e0',
        'secondary': '#5de6ff',
        'tertiary': '#4edea3',
        'on-surface': '#d8e3fb',
        'on-surface-variant': '#c6c6cd',
        'on-secondary': '#00363e',
        'on-tertiary-container': '#009365',
        'inverse-primary': '#565e74',
        'error': '#ffb4ab',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        geist: ['Geist', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
