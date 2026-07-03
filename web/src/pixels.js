// pixels.js — a tiny procedural pixel-art tile generator.
//
// All tiles are drawn here at runtime onto an offscreen <canvas>, so the art is **original / CC0 by
// construction** (nothing is ripped — see the art policy in docs/11-visual-world.md). A fixed seed
// keeps the speckle deterministic, so screenshots are reproducible lap to lap. Presentation only.

export const TILE = 16; // px per tile (internal resolution)

// mulberry32 — a small deterministic PRNG so placeholder texture is stable across builds.
function rng(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function tileDataURL(draw) {
  const c = document.createElement("canvas");
  c.width = TILE;
  c.height = TILE;
  const ctx = c.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  draw(ctx);
  return c.toDataURL();
}

const px = (ctx, x, y, w, h, color) => {
  ctx.fillStyle = color;
  ctx.fillRect(x, y, w, h);
};

// A patch of grass: base GB-green with scattered darker specks + a few bright blades.
function grass(ctx) {
  px(ctx, 0, 0, TILE, TILE, "#9bbc6f");
  const r = rng(1);
  for (let i = 0; i < 12; i++) px(ctx, (r() * TILE) | 0, (r() * TILE) | 0, 1, 1, "#7a9a54");
  for (let i = 0; i < 5; i++) px(ctx, (r() * TILE) | 0, (r() * TILE) | 0, 1, 2, "#c3d99a");
}

// A packed-dirt path: sandy base with a little grit.
function path(ctx) {
  px(ctx, 0, 0, TILE, TILE, "#cdbe93");
  const r = rng(7);
  for (let i = 0; i < 10; i++) px(ctx, (r() * TILE) | 0, (r() * TILE) | 0, 1, 1, "#b3a377");
  for (let i = 0; i < 6; i++) px(ctx, (r() * TILE) | 0, (r() * TILE) | 0, 1, 1, "#e3d8b6");
}

// Water: blue base with a couple of lighter wave dashes.
function water(ctx) {
  px(ctx, 0, 0, TILE, TILE, "#5c86ab");
  px(ctx, 2, 4, 5, 1, "#9bc0d9");
  px(ctx, 9, 9, 5, 1, "#9bc0d9");
  px(ctx, 4, 12, 4, 1, "#7aa6c4");
}

// A tree: grass underneath, a small trunk and a rounded dark-green canopy (drawn over grass so the
// tile isn't transparent where it sits on the map).
function tree(ctx) {
  grass(ctx);
  px(ctx, 7, 11, 2, 4, "#6b4a2b"); // trunk
  px(ctx, 4, 3, 8, 8, "#3f6b32"); // canopy body
  px(ctx, 3, 5, 10, 4, "#3f6b32");
  px(ctx, 5, 2, 6, 2, "#4f7d3f"); // top highlight
  px(ctx, 5, 4, 3, 2, "#5c944a");
}

export const BUILDING_W = 28;
export const BUILDING_H = 26;

// Darken a "#rrggbb" toward black by `f` (0..1) — for roof/wall shading.
function darken(hex, f) {
  const n = parseInt(hex.slice(1), 16);
  const r = Math.round(((n >> 16) & 255) * (1 - f));
  const g = Math.round(((n >> 8) & 255) * (1 - f));
  const b = Math.round((n & 255) * (1 - f));
  return `rgb(${r},${g},${b})`;
}

// A small gym building sprite tinted with its land's accent (accent roof, pale wall, a door and two
// windows). Original art, drawn procedurally. Returns a data URL.
export function makeBuilding(accent) {
  const c = document.createElement("canvas");
  c.width = BUILDING_W;
  c.height = BUILDING_H;
  const ctx = c.getContext("2d");
  ctx.imageSmoothingEnabled = false;

  // Wall (pale) with a darker right/bottom edge for a hint of depth.
  px(ctx, 6, 10, 16, 16, "#e6f0d6");
  px(ctx, 21, 10, 1, 16, "#c3cdae");
  px(ctx, 6, 25, 16, 1, "#c3cdae");

  // Stepped roof in the land accent, widening toward the eaves; bottom row shaded.
  const roof = [
    [13, 3, 2],
    [12, 4, 4],
    [11, 5, 6],
    [10, 6, 8],
    [9, 7, 10],
    [8, 8, 12],
    [6, 9, 16],
  ];
  for (const [x, y, w] of roof) px(ctx, x, y, w, 1, accent);
  px(ctx, 6, 9, 16, 1, darken(accent, 0.28)); // eave line

  // Door (dark) with an accent knob.
  px(ctx, 11, 17, 6, 9, "#0f1410");
  px(ctx, 15, 21, 1, 1, accent);
  // Windows.
  px(ctx, 7, 13, 3, 3, accent);
  px(ctx, 18, 13, 3, 3, accent);

  return c.toDataURL();
}

// Build every world tile as a data URL, keyed by its map symbol.
export function makeTiles() {
  return {
    G: tileDataURL(grass),
    P: tileDataURL(path),
    W: tileDataURL(water),
    T: tileDataURL(tree),
  };
}
