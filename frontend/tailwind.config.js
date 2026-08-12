/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        void: "#0f1219",
        chart: "#171c28",
        chartline: "#2a3244",
        parchment: "#eef1f6",
        muted: "#8b93a7",
        ice: "#5aa9e6",
        ember: "#ff6b35",
        embersoft: "#ffb088",
      },
      fontFamily: {
        display: ["Fraunces", "ui-serif", "Georgia", "serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px -8px var(--tw-shadow-color)",
      },
    },
  },
  plugins: [],
};
