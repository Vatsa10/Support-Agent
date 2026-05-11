import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0A0A0A",
          2: "#525252",
          3: "#A3A3A3"
        },
        line: {
          DEFAULT: "#E5E5E5",
          2: "#F2F2F2"
        },
        paper: "#FFFFFF",
        cream: "#FAFAF8",
        blue: {
          DEFAULT: "#1B4DFF",
          soft: "#EBF0FF",
          ink: "#0A2BB0"
        },
        success: "#0F8F5A",
        warn: "#B45309",
        danger: "#B91C1C"
      },
      fontFamily: {
        display: ["var(--font-display)", "ui-serif", "Georgia", "serif"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"]
      },
      letterSpacing: {
        tightest: "-0.04em"
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        fadein: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" }
        },
        slide: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" }
        },
        blink: {
          "0%,49%": { opacity: "1" },
          "50%,100%": { opacity: "0" }
        }
      },
      animation: {
        rise: "rise 700ms cubic-bezier(0.2, 0.7, 0.1, 1) both",
        fadein: "fadein 900ms ease-out both",
        slide: "slide 2.4s linear infinite",
        blink: "blink 1.05s steps(1) infinite"
      }
    }
  },
  plugins: []
};
export default config;
