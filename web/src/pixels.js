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

// --- Trainer sprite sheet ------------------------------------------------------------------------
// A 3×4 walk-cycle sheet (16×16 cells): rows = facing down/left/right/up, cols = step-left / stand /
// step-right. Original art, drawn procedurally on a transparent canvas so grass shows through.
// The sheet is palette-swappable: pass an `outfit` (cap/shirt/pants hex) and the same drawing is
// re-tinted, so every agent gets a visually-distinct trainer without any new art files.
export const TRAINER_CELL = 16;
export const TRAINER_COLS = 3;
export const TRAINER_ROWS = 4;

const OUTFIT_DEFAULTS = { cap: "#c0392b", shirt: "#3f7d9a", pants: "#2c3e66" };

function drawTrainer(ctx, ox, oy, dir, frame, outfit) {
  const CAP = outfit.cap;
  const CAPD = darken(outfit.cap, 0.3);
  const SKIN = "#e8c39e";
  const HAIR = "#5a3a22";
  const SHIRT = outfit.shirt;
  const PANTS = outfit.pants;
  const SHOE = "#3a2a1a";
  const INK = "#0f1410";
  const p = (x, y, w, h, color) => px(ctx, ox + x, oy + y, w, h, color);

  // Head / cap — brim and face change with facing.
  p(5, 3, 6, 2, CAP); // crown
  if (dir === "down") {
    p(4, 5, 8, 1, CAPD);
    p(5, 6, 6, 2, SKIN);
    p(6, 6, 1, 1, INK);
    p(9, 6, 1, 1, INK);
  } else if (dir === "left") {
    p(3, 5, 7, 1, CAPD);
    p(5, 6, 5, 2, SKIN);
    p(5, 6, 1, 1, INK);
    p(10, 6, 1, 2, HAIR);
  } else if (dir === "right") {
    p(6, 5, 7, 1, CAPD);
    p(6, 6, 5, 2, SKIN);
    p(10, 6, 1, 1, INK);
    p(5, 6, 1, 2, HAIR);
  } else {
    // up — back of the head
    p(4, 5, 8, 1, CAPD);
    p(5, 6, 6, 2, HAIR);
  }

  // Torso + arms.
  p(5, 8, 6, 3, SHIRT);
  p(4, 8, 1, 3, SKIN);
  p(11, 8, 1, 3, SKIN);

  // Legs — one foot bobs ahead of the other to read as a stride (stand on the middle frame).
  const lOff = frame === 2 ? 1 : 0;
  const rOff = frame === 0 ? 1 : 0;
  p(5, 11 + lOff, 2, 3, PANTS);
  p(5, 14 + lOff, 2, 1, SHOE);
  p(9, 11 + rOff, 2, 3, PANTS);
  p(9, 14 + rOff, 2, 1, SHOE);
}

export function makeTrainer(outfit = {}) {
  const o = { ...OUTFIT_DEFAULTS, ...outfit };
  const W = TRAINER_CELL * TRAINER_COLS;
  const H = TRAINER_CELL * TRAINER_ROWS;
  const c = document.createElement("canvas");
  c.width = W;
  c.height = H;
  const ctx = c.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  const dirs = ["down", "left", "right", "up"];
  for (let r = 0; r < TRAINER_ROWS; r++) {
    for (let col = 0; col < TRAINER_COLS; col++) {
      drawTrainer(ctx, col * TRAINER_CELL, r * TRAINER_CELL, dirs[r], col, o);
    }
  }
  return c.toDataURL();
}

// A small offscreen-canvas sprite of arbitrary size (for props that aren't tile-sized).
function spriteURL(w, h, draw) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  draw(ctx);
  return c.toDataURL();
}

// A lamp post — dark pole with a glowing head. Transparent background (drops onto grass).
export function makeLamp() {
  return spriteURL(8, 18, (ctx) => {
    px(ctx, 3, 4, 2, 12, "#52525a"); // pole
    px(ctx, 2, 16, 4, 2, "#3a3a40"); // base
    px(ctx, 2, 1, 4, 4, "#f6de8a"); // glowing head
    px(ctx, 1, 2, 1, 2, "#c9b25f");
    px(ctx, 6, 2, 1, 2, "#c9b25f");
    px(ctx, 2, 0, 4, 1, "#42424a"); // cap
  });
}

// A park bench — wooden seat + back on little legs.
export function makeBench() {
  return spriteURL(16, 9, (ctx) => {
    px(ctx, 3, 1, 10, 2, "#8a5a34"); // back
    px(ctx, 3, 3, 1, 1, "#6b4a2b");
    px(ctx, 12, 3, 1, 1, "#6b4a2b");
    px(ctx, 2, 4, 12, 2, "#9a6a40"); // seat
    px(ctx, 3, 6, 2, 3, "#6b4a2b"); // legs
    px(ctx, 11, 6, 2, 3, "#6b4a2b");
  });
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
