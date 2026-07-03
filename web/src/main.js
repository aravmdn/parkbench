// main.js — boot the Parkbench visual world.
//
// This is the scaffold lap (backlog: web-scaffold): stand up Kaplay on a clean canvas that boots with
// no console errors. Later laps grow this into the overworld (tilemap, four lands, gym buildings, a
// walking trainer, and the stats screen wired to `parkbench radar --json`). The front-end is
// presentation only — it never scores anything (D-012).

import kaplay from "kaplay";
import { PALETTE, PARK_NAME, PARK_TAGLINE } from "./theme.js";

// Internal (pixel-art) resolution. Kaplay letterboxes/scales this to the window, and index.html sets
// `image-rendering: pixelated` so the upscale stays crisp.
const GAME_W = 320;
const GAME_H = 288; // 10:9 — the Game Boy screen ratio

const k = kaplay({
  width: GAME_W,
  height: GAME_H,
  letterbox: true,
  background: hexToRgb(PALETTE.shadow),
  root: document.getElementById("app"),
  pixelDensity: 1,
  crisp: true,
  // Fail loudly during development rather than swallowing errors.
  logMax: 8,
});

// Convert a "#rrggbb" string into the [r, g, b] array Kaplay's `background` option expects.
function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

k.scene("boot", () => {
  // A calm placeholder screen: the park is closed until the overworld lands next lap.
  k.add([
    k.rect(GAME_W, GAME_H),
    k.pos(0, 0),
    k.color(k.Color.fromHex(PALETTE.light)),
    k.opacity(0.06),
  ]);

  k.add([
    k.text(PARK_NAME, { size: 40, font: "monospace" }),
    k.pos(GAME_W / 2, GAME_H / 2 - 24),
    k.anchor("center"),
    k.color(k.Color.fromHex(PALETTE.paper)),
  ]);

  k.add([
    k.text(PARK_TAGLINE, { size: 12, font: "monospace" }),
    k.pos(GAME_W / 2, GAME_H / 2 + 12),
    k.anchor("center"),
    k.color(k.Color.fromHex(PALETTE.light)),
  ]);

  k.add([
    k.text("the gates open soon", { size: 8, font: "monospace" }),
    k.pos(GAME_W / 2, GAME_H - 20),
    k.anchor("center"),
    k.color(k.Color.fromHex(PALETTE.mid)),
  ]);
});

k.go("boot");
