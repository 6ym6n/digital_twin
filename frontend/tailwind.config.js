/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f172a',
        surface: 'rgba(30, 41, 59, 0.7)',
        'surface-light': 'rgba(51, 65, 85, 0.5)',
        primary: '#3b82f6',
        accent: '#14b8a6',
        warning: '#f59e0b',
        danger: '#ef4444',
        success: '#22c55e',
      },
      backdropBlur: {
        'glass': '20px',
      },
      boxShadow: {
        'glass': '0 8px 32px rgba(0, 0, 0, 0.3)',
        'glow-primary': '0 0 20px rgba(59, 130, 246, 0.4)',
        'glow-danger': '0 0 20px rgba(239, 68, 68, 0.4)',
        'glow-success': '0 0 20px rgba(34, 197, 94, 0.4)',
      },
    },
  },
  plugins: [],
}
