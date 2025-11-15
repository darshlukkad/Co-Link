/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        slack: {
          // Sidebar colors (exact Slack purple)
          'purple': '#4A154B',
          'purple-dark': '#3E0E40',
          'purple-darker': '#350D36',
          'purple-border': '#682769',
          'purple-hover': '#3E0E40',
          'purple-active': '#1164A3',

          // Accent colors
          'green': '#007a5a',
          'green-dark': '#005a42',
          'blue': '#1264a3',
          'blue-light': '#1f8bfa',
          'red': '#e01e5a',

          // UI colors
          'gray': {
            50: '#f8f8f8',
            100: '#f0f0f0',
            200: '#e0e0e0',
            300: '#c7c7c7',
            400: '#a0a0a0',
            500: '#717171',
            600: '#5c5c5c',
            700: '#464646',
            800: '#2e2e2e',
            900: '#1a1a1a',
          },

          // Message colors
          'message-hover': '#f8f8f8',
          'message-highlight': '#fff4e0',
          'border': '#e0e0e0',
        },
      },
      keyframes: {
        'slide-in-right': {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        'slide-out-right': {
          '0%': { transform: 'translateX(0)', opacity: '1' },
          '100%': { transform: 'translateX(100%)', opacity: '0' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'scale-in': {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'pulse-slow': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
      animation: {
        'slide-in-right': 'slide-in-right 0.3s ease-out',
        'slide-out-right': 'slide-out-right 0.3s ease-in',
        'slide-up': 'slide-up 0.2s ease-out',
        'fade-in': 'fade-in 0.2s ease-out',
        'scale-in': 'scale-in 0.2s ease-out',
        'pulse-slow': 'pulse-slow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
    },
  },
  plugins: [],
}
