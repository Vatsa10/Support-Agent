import { Instrument_Serif, Geist, JetBrains_Mono } from "next/font/google";

export const display = Instrument_Serif({
  subsets: ["latin"],
  weight: ["400"],
  style: ["normal", "italic"],
  variable: "--font-display",
  display: "swap"
});

export const sans = Geist({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap"
});

export const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap"
});
