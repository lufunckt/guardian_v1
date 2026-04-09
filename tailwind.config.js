/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        guardian: {
          bg: '#f8fafc',
          card: '#ffffff',
          primary: '#2563eb',
          success: '#16a34a',
          warn: '#f59e0b',
          danger: '#dc2626',
          ink: '#0f172a',
          soft: '#e2e8f0'
        }
      },
      boxShadow: {
        card: '0 8px 30px rgba(15, 23, 42, 0.08)'
      }
    },
  },
  plugins: [],
};
