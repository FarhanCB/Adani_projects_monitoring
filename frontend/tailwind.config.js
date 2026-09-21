/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        adani: {
          blue: '#0078BD',
          cyan: '#0082CA',
          purple: '#583896',
          magenta: '#BE185D',
          dark: '#1E1B4B',
          surface: '#F8FAFC',
          card: '#FFFFFF',
          border: '#E2E8F0',
        },
        status: {
          up: '#16A34A',
          upBg: '#DCFCE7',
          down: '#DC2626',
          downBg: '#FEE2E2',
          warning: '#D97706',
          warningBg: '#FEF3C7',
          nodata: '#64748B',
          nodataBg: '#F1F5F9',
        }
      },
      backgroundImage: {
        'adani-gradient': 'linear-gradient(135deg, #0078BD 0%, #583896 50%, #BE185D 100%)',
        'adani-gradient-h': 'linear-gradient(90deg, #0078BD 0%, #583896 50%, #BE185D 100%)',
        'adani-gradient-hover': 'linear-gradient(135deg, #0284c7 0%, #6366f1 50%, #db2777 100%)',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'subtle': '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
        'hover': '0 10px 15px -3px rgba(88, 56, 150, 0.12), 0 4px 6px -2px rgba(0, 120, 189, 0.06)',
        'adani': '0 4px 14px 0 rgba(88, 56, 150, 0.25)',
      }
    },
  },
  plugins: [],
}
