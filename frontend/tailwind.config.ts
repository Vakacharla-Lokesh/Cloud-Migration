import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["'IBM Plex Sans'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      colors: {
        base: {
          950: "#0d0f11",
          900: "#13161a",
          800: "#1a1e24",
          700: "#22272f",
          600: "#2c333d",
          500: "#3d4550",
          400: "#5a6475",
          300: "#8a96a3",
          200: "#b8c0ca",
          100: "#e2e6eb",
        },
        amber: {
          400: "#fbbf24",
          500: "#f59e0b",
        },
        emerald: {
          400: "#34d399",
          500: "#10b981",
        },
        rose: {
          400: "#fb7185",
          500: "#f43f5e",
        },
        sky: {
          400: "#38bdf8",
          500: "#0ea5e9",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
