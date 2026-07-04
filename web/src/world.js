// world.js — the overworld: a top-down tile map of the park.
//
// Presentation only (D-012). This builds a fixed placeholder layout — a bordered green park with a
// central crossroads path and a pond — out of the procedural tiles in pixels.js. Later laps overlay
// the four lands, gym buildings, and a walking trainer.

import { TILE, makeTiles } from "./pixels.js";

export const COLS = 20;
export const ROWS = 18;
export const WORLD_W = COLS * TILE; // 320
export const WORLD_H = ROWS * TILE; // 288

// Build the tile map as an array of strings (one char per tile). Generated in code rather than
// hand-typed so the layout is easy to reason about and stays in sync with COLS/ROWS.
//   G grass · P path · W water · T tree
export function buildMap() {
  const grid = [];
  for (let y = 0; y < ROWS; y++) {
    const row = [];
    for (let x = 0; x < COLS; x++) {
      let t = "G";
      // Tree border ring.
      if (x === 0 || y === 0 || x === COLS - 1 || y === ROWS - 1) t = "T";
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
  const tiles = makeTiles();
  for (const [sym, url] of Object.entries(tiles)) k.loadSprite("tile-" + sym, url);

  return k.addLevel(buildMap(), {
    tileWidth: TILE,
    tileHeight: TILE,
    tiles: {
      G: () => [k.sprite("tile-G")],
      P: () => [k.sprite("tile-P")],
      W: () => [k.sprite("tile-W")],
      T: () => [k.sprite("tile-T")],
    },
  });
}
