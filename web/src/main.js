// main.js — boot the Parkbench visual world.
//
// The world now has a tile overworld, four labeled lands, gym buildings, a walking trainer, and a
// stats screen wired to real `parkbench radar --json` fixtures (press S). The front-end is
// presentation only — it never scores anything (D-012).

import kaplay from "kaplay";
import { PALETTE, PARK_NAME } from "./theme.js";
import { buildOverworld, WORLD_W, WORLD_H } from "./world.js";
import { buildLands } from "./lands.js";
import { buildGyms } from "./buildings.js";
import { buildProps } from "./props.js";
import { addTrainer } from "./trainer.js";
import { setupGymRuns } from "./gymrun.js";
import { registerStatsScene } from "./radar.js";
import { registerHallOfFameScene } from "./halloffame.js";

// Which agent the on-screen trainer represents (drives the gym-run scores + stats default).
const TRAINER_AGENT = "heuristic";

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
  const gyms = buildGyms(k);
  buildProps(k);
  const trainer = addTrainer(k, TRAINER_AGENT);
  setupGymRuns(k, trainer, gyms);

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
  k.add([
    k.text("S: stats   H: hall", { size: 8, font: "monospace" }),
    k.pos(WORLD_W - 6, 6),
    k.anchor("topright"),
    k.color(k.Color.fromHex(PALETTE.light)),
    k.fixed(),
    k.z(101),
  ]);

  // The diagnostic screens are reachable from the world.
  k.onKeyPress("s", () => k.go("stats", TRAINER_AGENT));
  k.onKeyPress("h", () => k.go("halloffame"));
});

registerStatsScene(k);
registerHallOfFameScene(k);
k.go("park");
