/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        river: "#0ea5e9",
        ocean: "#2563eb",
        earth: "#92400e",
        amber: "#f59e0b",
        slate: "#0f172a",
        emerald: "#059669",
        indigo: "#4f46e5"
      }
    }
  },
  plugins: []
}

