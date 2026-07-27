// world.js — the overworld: a top-down tile map of the park.
//
// Presentation only (D-012). This builds a fixed layout — a bordered green park with a central
// crossroads path and a pond — out of the procedural tiles in pixels.js, plus a **paved forecourt
// per land** so each of the four lands has its own ground treatment (flagstone plaza / market
// cobbles / workshop checkerplate / hazard-kerbed concrete) rather than only an accent tint. The
// lands overlay, gym buildings, props, and trainers are layered on top of this map.

import { TILE, makeTiles } from "./pixels.js";
import { LANDS } from "./theme.js";

export const COLS = 20;
export const ROWS = 18;
export const WORLD_W = COLS * TILE; // 320
export const WORLD_H = ROWS * TILE; // 288

// Each land's paved forecourt, as an inclusive tile rectangle inside that land's quadrant (lands.js
// QUADRANTS). Every patch is bounded by the quadrant, so none of them touches the crossroads paths
// (cols 9-10 / rows 8-9) the trainers patrol, the tree border, or the pond — the park stays walkable
// and the gyms keep their approach.
//   S plaza (social) · M cobbles (economic) · F checkerplate (coding) · X hazard kerb + H concrete (safety)
export const LAND_GROUND = [
  { sym: "S", c0: 2, c1: 8, r0: 4, r1: 7 }, // Society Square — a flagstone plaza under its two gyms
  { sym: "M", c0: 11, c1: 18, r0: 6, r1: 7 }, // Market Midway — the cobbled trading strip
  { sym: "F", c0: 2, c1: 8, r0: 14, r1: 16 }, // Maker's Workshop — a steel-plated works yard
  { sym: "X", c0: 12, c1: 18, r0: 13, r1: 13 }, // Safety Gauntlet — the hazard-striped threshold
  { sym: "H", c0: 12, c1: 18, r0: 14, r1: 16 }, // Safety Gauntlet — the concrete apron
];

// Build the tile map as an array of strings (one char per tile). Generated in code rather than
// hand-typed so the layout is easy to reason about and stays in sync with COLS/ROWS.
//   G grass · P path · W water · T tree · S/M/F/H/X the four lands' ground (see LAND_GROUND)
export function buildMap() {
  const grid = [];
  for (let y = 0; y < ROWS; y++) {
    const row = [];
    for (let x = 0; x < COLS; x++) {
      let t = "G";
      // Tree border ring.
      if (x === 0 || y === 0 || x === COLS - 1 || y === ROWS - 1) t = "T";
      // Each land's paved forecourt.
      for (const g of LAND_GROUND) {
        if (x >= g.c0 && x <= g.c1 && y >= g.r0 && y <= g.r1) t = g.sym;
      }
      // Central crossroads: a horizontal + vertical path meeting in the middle.
      if ((y === 8 || y === 9) && x > 0 && x < COLS - 1) t = "P";
      if ((x === 9 || x === 10) && y > 0 && y < ROWS - 1) t = "P";
      // A pond in the top-right quadrant.
      if (x >= 13 && x <= 16 && y >= 3 && y <= 5) t = "W";
      row.push(t);
    }
    grid.push(row.join(""));
  }
  return grid;
}

// Load the tile sprites and add the level. Returns the Kaplay level object.
export function buildOverworld(k) {
  // The land grounds take their signature colour from the same LANDS table the signs + gyms use.
  const accents = Object.fromEntries(LANDS.map((l) => [l.axis, l.accent]));
  const tiles = makeTiles(accents);
  for (const [sym, url] of Object.entries(tiles)) k.loadSprite("tile-" + sym, url);

  // One tile component per symbol — built from the sprite keys above so a new ground tile only has
  // to be added to makeTiles() + LAND_GROUND.
  const tileDefs = {};
  for (const sym of Object.keys(tiles)) tileDefs[sym] = () => [k.sprite("tile-" + sym)];

  return k.addLevel(buildMap(), {
    tileWidth: TILE,
    tileHeight: TILE,
    tiles: tileDefs,
  });
}
