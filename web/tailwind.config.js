/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080710",
        glass: {
          light: "rgba(255, 255, 255, 0.05)",
          border: "rgba(255, 255, 255, 0.1)",
          glow: "rgba(59, 130, 246, 0.15)",
        },
        accent: {
          blue: "#3b82f6",
          purple: "#8b5cf6",
          green: "#10b981",
        }
      },
      fontFamily: {
        sans: ["Outfit", "Inter", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(59, 130, 246, 0.2), 0 0 10px rgba(59, 130, 246, 0.1)' },
          '100%': { boxShadow: '0 0 20px rgba(59, 130, 246, 0.6), 0 0 30px rgba(59, 130, 246, 0.3)' },
        }
      }
    },
  },
  plugins: [],
}
