/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        pip: {
          50:  "#EEF2FF",
          100: "#E0E7FF",
          200: "#C7D2FE",
          500: "#6366F1",
          600: "#4F46E5",
          700: "#3730A3",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "sans-serif"],
      },
      keyframes: {
        spin: { to: { transform: "rotate(360deg)" } },
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        slideUp: {
          from: { opacity: "0", transform: "translateY(12px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        spin:     "spin .7s linear infinite",
        fadeIn:   "fadeIn .18s ease",
        slideUp:  "slideUp .22s ease",
      },
    },
  },
  plugins: [],
};
