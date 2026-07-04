// theme.js — the front-end's mirror of the engine's park skin (src/parkbench/theme.py).
//
// Presentation only (upholds D-012 / the visual-world load-bearing rule): this file holds names,
// blurbs, and a palette for drawing the world. It never computes or influences a score — all truth
// lives in the stdlib engine and arrives here as JSON. Keep the land/ride vocabulary in sync with
// theme.py so the world reads the way the CLI does.

// A small, original GB/GBA-era palette (4 greyscale-green shades + per-land accents). Not ripped from
// any commercial game — just the classic 4-tone Game Boy feel, our own hex values.
export const PALETTE = {
  ink: "#0f1410", // darkest — outlines, text
  shadow: "#28402b",
  mid: "#5c7a4d",
  light: "#9bbc6f", // classic GB screen green
  paper: "#e6f0d6", // lightest — highlights
};

// The four skill axes, skinned as the park's four lands (mirrors LANDS in theme.py).
// `accent` is this land's signature colour on the overworld; laid out clockwise from top-left.
export const LANDS = [
  {
    axis: "social",
    name: "Society Square",
    blurb: "Where agents deal, cooperate, and connive.",
    accent: "#6f9bbc", // sky blue
    grid: { col: 0, row: 0 },
  },
  {
    axis: "economic",
    name: "Market Midway",
    blurb: "Scarcity, budgets, and the hunt for value.",
    accent: "#d9a441", // gold
    grid: { col: 1, row: 0 },
  },
  {
    axis: "coding",
    name: "Maker's Workshop",
    blurb: "Build it, ship it, survive the tests.",
    accent: "#b06fbc", // violet
    grid: { col: 0, row: 1 },
  },
  {
    axis: "safety",
    name: "Safety Gauntlet",
    blurb: "Hold the line when the rewards pull you across it.",
    accent: "#bc6f6f", // red
    grid: { col: 1, row: 1 },
  },
];

// One attraction (gym) per scored ride, keyed by the ride's engine registry name (mirrors
// ATTRACTIONS in theme.py). `axis` says which land it sits in.
export const ATTRACTIONS = [
  { ride: "negotiation", axis: "social", marquee: "The Bargaining Bazaar" },
  { ride: "commons", axis: "social", marquee: "The Commons Carousel" },
  { ride: "economic", axis: "economic", marquee: "The Knapsack Coaster" },
  { ride: "coding", axis: "coding", marquee: "The Code Foundry" },
  { ride: "safety", axis: "safety", marquee: "The Red-Line Rapids" },
];

export const PARK_NAME = "PARKBENCH";
export const PARK_TAGLINE = "a theme park for AI agents";
