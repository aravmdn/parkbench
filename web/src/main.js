// main.js — boot the Parkbench visual world.
//
// The overworld now renders a top-down tile map (backlog: overworld-tilemap). Later laps grow this
// into the four labeled lands, gym buildings, a walking trainer, and the stats screen wired to
// `parkbench radar --json`. The front-end is presentation only — it never scores anything (D-012).

import kaplay from "kaplay";
import { PALETTE, PARK_NAME } from "./theme.js";
import { buildOverworld, WORLD_W, WORLD_H } from "./world.js";
import { buildLands } from "./lands.js";
import { buildGyms } from "./buildings.js";

const k = kaplay({
  width: WORLD_W,
  height: WORLD_H,
  letterbox: true,
  background: hexToRgb(PALETTE.shadow),
  root: document.getElementById("app"),
  pixelDensity: 1,
  crisp: true,
  logMax: 8,
});

// Convert a "#rrggbb" string into the [r, g, b] array Kaplay's `background` option expects.
function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

k.scene("park", () => {
  buildOverworld(k);
  buildLands(k);
  buildGyms(k);

  // A small title plate pinned to the top, drawn above the map.
  k.add([
    k.rect(WORLD_W, 18),
    k.pos(0, 0),
    k.color(k.Color.fromHex(PALETTE.ink)),
    k.opacity(0.55),
    k.fixed(),
    k.z(100),
  ]);
  k.add([
    k.text(PARK_NAME, { size: 12, font: "monospace" }),
    k.pos(6, 4),
    k.color(k.Color.fromHex(PALETTE.paper)),
    k.fixed(),
    k.z(101),
  ]);
});

k.go("park");
