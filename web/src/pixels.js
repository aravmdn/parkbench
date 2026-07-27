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

// --- palette helpers ------------------------------------------------------------------------------
// The four lands must read as *one* park, so every land's art is built from the same two anchors —
// the GB ink and the GB paper — blended with that land's accent. `mix` is the only colour maths the
// land art uses, which is what keeps the palette limited and consistent.

const INK = "#0f1410";
const PAPER = "#e6f0d6";

function toHex(r, g, b) {
  const h = (v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0");
  return "#" + h(r) + h(g) + h(b);
}

// Blend two "#rrggbb" colours: t = 0 → a, t = 1 → b.
function mix(a, b, t) {
  const A = parseInt(a.slice(1), 16);
  const B = parseInt(b.slice(1), 16);
  return toHex(
    ((A >> 16) & 255) * (1 - t) + ((B >> 16) & 255) * t,
    ((A >> 8) & 255) * (1 - t) + ((B >> 8) & 255) * t,
    (A & 255) * (1 - t) + (B & 255) * t,
  );
}

const shade = (hex, f) => mix(hex, INK, f); // toward the ink
const lift = (hex, f) => mix(hex, PAPER, f); // toward the paper

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

// --- per-land ground tiles ------------------------------------------------------------------------
// Each land gets its own **ground treatment**, not just an accent wash: a paved forecourt whose
// texture says what the land is about. They share the grass/path base tones and take their signature
// colour from the land's accent (theme.js), so four distinct places still read as one park.

// Society Square — a swept flagstone plaza: 8×8 slabs, mortar joints, an accent inlay at the crossing.
function plazaTile(accent) {
  const stone = mix("#c6cfbd", accent, 0.12); // pale civic stone, faintly the land's blue
  return (ctx) => {
    px(ctx, 0, 0, TILE, TILE, stone);
    for (const [sx, sy] of [[0, 0], [9, 0], [0, 9], [9, 9]]) px(ctx, sx, sy, 7, 7, lift(stone, 0.3));
    px(ctx, 0, 7, TILE, 2, shade(stone, 0.16)); // mortar joints
    px(ctx, 7, 0, 2, TILE, shade(stone, 0.16));
    px(ctx, 7, 7, 2, 2, mix(accent, stone, 0.35)); // accent inlay where the joints cross
    const r = rng(11);
    for (let i = 0; i < 5; i++) px(ctx, (r() * TILE) | 0, (r() * TILE) | 0, 1, 1, shade(stone, 0.08));
  };
}

// Market Midway — cobbled setts in offset courses, warm like the paths, with a few accent-gold stones.
function cobbleTile(accent) {
  const sett = "#cdbe93";
  return (ctx) => {
    px(ctx, 0, 0, TILE, TILE, shade(sett, 0.22)); // mortar bed
    const r = rng(23);
    for (let row = 0; row < 4; row++) {
      const y = row * 4;
      const off = row % 2 ? -4 : 0;
      for (let x = off; x < TILE; x += 8) {
        const gold = r() < 0.2;
        const face = gold ? mix(sett, accent, 0.45) : sett;
        px(ctx, x, y, 7, 3, face);
        px(ctx, x, y, 7, 1, lift(face, 0.3));
      }
    }
  };
}

// Maker's Workshop — steel checkerplate: plate seams, diamond tread, and one accent rivet per plate.
function plateTile(accent) {
  const plate = "#8d8a99";
  return (ctx) => {
    px(ctx, 0, 0, TILE, TILE, plate);
    px(ctx, 0, 0, TILE, 1, lift(plate, 0.22)); // seam highlight
    px(ctx, 0, 7, TILE, 1, shade(plate, 0.22)); // seam shadow
    px(ctx, 0, TILE - 1, TILE, 1, shade(plate, 0.22));
    const tread = (x, y) => {
      px(ctx, x + 1, y, 2, 1, lift(plate, 0.28));
      px(ctx, x, y + 1, 4, 1, lift(plate, 0.28));
      px(ctx, x + 1, y + 2, 2, 1, shade(plate, 0.14));
    };
    tread(2, 3);
    tread(10, 3);
    tread(6, 11);
    tread(12, 11);
    px(ctx, 1, 9, 1, 1, lift(plate, 0.35)); // rivets
    px(ctx, 14, 2, 1, 1, lift(plate, 0.35));
    px(ctx, 8, 5, 1, 1, accent); // the accent rivet
  };
}

// Safety Gauntlet — poured concrete: fine grain, a slab joint, a fleck of warning paint.
function concreteTile(accent) {
  // Deliberately darker + greyer than the Society plaza's flagstone, so the park's two pale paved
  // lands never read as the same place.
  const slab = "#a5a69a";
  return (ctx) => {
    px(ctx, 0, 0, TILE, TILE, slab);
    const r = rng(37);
    for (let i = 0; i < 16; i++) px(ctx, (r() * TILE) | 0, (r() * TILE) | 0, 1, 1, shade(slab, 0.1));
    for (let i = 0; i < 6; i++) px(ctx, (r() * TILE) | 0, (r() * TILE) | 0, 1, 1, lift(slab, 0.22));
    px(ctx, 0, 7, TILE, 1, shade(slab, 0.16)); // slab joints
    px(ctx, 7, 8, 1, 8, shade(slab, 0.16));
    px(ctx, 12, 2, 2, 1, mix(slab, accent, 0.45)); // a scuff of warning paint
  };
}

// Safety Gauntlet — the hazard-striped kerb you cross to enter the gauntlet (one row only; loud on
// purpose, so the threshold reads as "you are entering the red-line zone").
function hazardTile(accent) {
  const cream = "#e6d8c0";
  return (ctx) => {
    for (let y = 0; y < TILE; y++) {
      for (let x = 0; x < TILE; x++) px(ctx, x, y, 1, 1, (x + y) % 8 < 4 ? accent : cream);
    }
    px(ctx, 0, 0, TILE, 1, INK); // dark kerb edges
    px(ctx, 0, TILE - 1, TILE, 1, INK);
  };
}

// --- per-land props -------------------------------------------------------------------------------
// Freestanding scenery (transparent background, dropped on top of the ground). One motif per land.

// Society Square: a stone fountain — the plaza's centrepiece.
export function makeFountain(accent) {
  const stone = mix("#c6cfbd", accent, 0.1);
  const rim = shade(stone, 0.22); // darker rim so the fountain reads against the pale plaza
  const wet = mix(accent, "#5c86ab", 0.35);
  return spriteURL(24, 20, (ctx) => {
    // Basin.
    px(ctx, 5, 6, 14, 1, lift(rim, 0.35));
    px(ctx, 3, 7, 18, 9, rim);
    px(ctx, 4, 16, 16, 1, shade(rim, 0.3));
    px(ctx, 6, 17, 12, 1, shade(rim, 0.5));
    // Water inside the basin.
    px(ctx, 6, 8, 12, 6, wet);
    px(ctx, 5, 9, 14, 4, wet);
    px(ctx, 6, 8, 12, 1, lift(wet, 0.4));
    px(ctx, 7, 10, 4, 1, lift(wet, 0.55));
    px(ctx, 13, 12, 4, 1, lift(wet, 0.3));
    px(ctx, 6, 13, 12, 1, shade(wet, 0.25));
    // Spout + spray.
    px(ctx, 11, 2, 2, 7, stone);
    px(ctx, 10, 1, 4, 1, lift(stone, 0.4));
    px(ctx, 9, 3, 1, 2, lift(wet, 0.6));
    px(ctx, 14, 3, 1, 2, lift(wet, 0.6));
    px(ctx, 8, 5, 1, 2, lift(wet, 0.25));
    px(ctx, 15, 5, 1, 2, lift(wet, 0.25));
  });
}

// Society Square: a clipped topiary hedge — the manicured civic look.
export function makeHedge() {
  return spriteURL(16, 12, (ctx) => {
    px(ctx, 1, 3, 14, 8, "#3f6b32");
    px(ctx, 2, 2, 12, 1, "#4f7d3f");
    px(ctx, 4, 1, 8, 1, "#4f7d3f");
    px(ctx, 3, 3, 4, 1, "#5c944a");
    px(ctx, 9, 5, 3, 1, "#5c944a");
    px(ctx, 1, 11, 14, 1, "#2f5226");
    px(ctx, 6, 6, 1, 1, "#c3d99a");
    px(ctx, 11, 8, 1, 1, "#c3d99a");
  });
}

// Market Midway: a market stall — striped awning, counter, goods.
export function makeStall(accent) {
  const wood = "#a8763f";
  return spriteURL(26, 22, (ctx) => {
    px(ctx, 1, 6, 2, 15, shade(wood, 0.35)); // posts
    px(ctx, 23, 6, 2, 15, shade(wood, 0.35));
    px(ctx, 2, 13, 22, 5, wood); // counter
    px(ctx, 2, 13, 22, 1, lift(wood, 0.3));
    px(ctx, 2, 17, 22, 1, shade(wood, 0.3));
    // Goods on the counter.
    px(ctx, 5, 9, 4, 4, mix(accent, PAPER, 0.15));
    px(ctx, 11, 10, 5, 3, shade(wood, 0.15));
    px(ctx, 18, 9, 3, 4, lift(accent, 0.35));
    // Striped awning, drawn last so it overhangs.
    for (let x = 0; x < 26; x++) px(ctx, x, 1, 1, 6, (x >> 2) % 2 ? PAPER : accent);
    px(ctx, 0, 0, 26, 1, shade(accent, 0.35));
    for (let x = 0; x < 26; x += 4) px(ctx, x + 1, 7, 2, 1, (x >> 2) % 2 ? PAPER : accent); // scallops
  });
}

// Market Midway: a goods barrel.
export function makeBarrel() {
  const wood = "#a8763f";
  return spriteURL(10, 14, (ctx) => {
    px(ctx, 1, 1, 8, 12, wood);
    px(ctx, 2, 0, 6, 2, lift(wood, 0.35));
    px(ctx, 0, 3, 10, 1, shade(wood, 0.4)); // hoops
    px(ctx, 0, 9, 10, 1, shade(wood, 0.4));
    px(ctx, 3, 4, 1, 5, shade(wood, 0.18)); // staves
    px(ctx, 6, 4, 1, 5, shade(wood, 0.18));
    px(ctx, 1, 13, 8, 1, shade(wood, 0.55));
  });
}

// Maker's Workshop: a stack of crates.
function crate(ctx, x, y, s, base) {
  px(ctx, x, y, s, s, base);
  px(ctx, x, y, s, 1, lift(base, 0.3));
  px(ctx, x, y + s - 1, s, 1, shade(base, 0.35));
  px(ctx, x + s - 1, y, 1, s, shade(base, 0.3));
  for (let i = 1; i < s - 1; i++) {
    px(ctx, x + i, y + i, 1, 1, shade(base, 0.3));
    px(ctx, x + s - 1 - i, y + i, 1, 1, shade(base, 0.3));
  }
}

export function makeCrates() {
  return spriteURL(18, 18, (ctx) => {
    crate(ctx, 0, 6, 12, "#a8763f");
    crate(ctx, 11, 9, 7, "#8f6535");
    crate(ctx, 3, 0, 7, "#8f6535");
  });
}

// Maker's Workshop: an anvil on its block.
export function makeAnvil() {
  const steel = "#8d8a99";
  return spriteURL(16, 13, (ctx) => {
    px(ctx, 4, 9, 8, 3, "#6b4a2b"); // block
    px(ctx, 4, 12, 8, 1, shade("#6b4a2b", 0.4));
    px(ctx, 6, 6, 4, 3, shade(steel, 0.2)); // waist
    px(ctx, 2, 2, 12, 4, steel); // body
    px(ctx, 0, 3, 3, 2, steel); // horn
    px(ctx, 2, 2, 12, 1, lift(steel, 0.35));
    px(ctx, 2, 5, 12, 1, shade(steel, 0.3));
  });
}

// Maker's Workshop: a cog wheel leaning against the yard wall.
export function makeCog(accent) {
  const steel = "#7e7b8c";
  return spriteURL(16, 16, (ctx) => {
    for (const [x, y, w, h] of [[6, 0, 4, 4], [6, 12, 4, 4], [0, 6, 4, 4], [12, 6, 4, 4]]) {
      px(ctx, x, y, w, h, steel); // square teeth at the compass points
    }
    for (const [x, y] of [[2, 2], [11, 2], [2, 11], [11, 11]]) px(ctx, x, y, 3, 3, steel); // diagonals
    px(ctx, 3, 4, 10, 8, steel); // body disc
    px(ctx, 4, 3, 8, 10, steel);
    px(ctx, 4, 3, 8, 1, lift(steel, 0.32)); // lit top-left, shaded bottom-right
    px(ctx, 3, 4, 1, 8, lift(steel, 0.32));
    px(ctx, 4, 12, 8, 1, shade(steel, 0.4));
    px(ctx, 12, 4, 1, 8, shade(steel, 0.4));
    px(ctx, 6, 6, 4, 4, accent); // hub
    ctx.clearRect(7, 7, 2, 2); // bore
  });
}

// Safety Gauntlet: a traffic cone.
export function makeCone(accent) {
  const body = mix(accent, "#e08a3c", 0.45);
  return spriteURL(10, 14, (ctx) => {
    for (let y = 1; y <= 10; y++) {
      const w = 2 + Math.floor((y - 1) * 0.6);
      const x = 5 - Math.ceil(w / 2);
      px(ctx, x, y, w, 1, y === 5 || y === 6 ? PAPER : body);
    }
    px(ctx, 1, 11, 8, 2, shade(body, 0.25)); // base
    px(ctx, 0, 13, 10, 1, shade(body, 0.5));
  });
}

// Safety Gauntlet: a striped barrier across the yard.
export function makeBarrier(accent) {
  const cream = "#e6d8c0";
  return spriteURL(26, 14, (ctx) => {
    px(ctx, 3, 6, 2, 8, "#52525a"); // legs
    px(ctx, 21, 6, 2, 8, "#52525a");
    for (let y = 2; y < 8; y++) {
      for (let x = 0; x < 26; x++) px(ctx, x, y, 1, 1, (x + y) % 8 < 4 ? accent : cream);
    }
    px(ctx, 0, 1, 26, 1, INK);
    px(ctx, 0, 8, 26, 1, INK);
  });
}

// Safety Gauntlet: a warning sign on a post.
export function makeWarnSign(accent) {
  return spriteURL(16, 18, (ctx) => {
    px(ctx, 7, 10, 2, 8, "#6b4a2b"); // post
    for (let y = 0; y <= 10; y++) {
      const w = 1 + Math.round(y * 1.4);
      const x = 8 - Math.round(w / 2);
      px(ctx, x, y, w, 1, accent);
    }
    for (let y = 3; y <= 8; y++) {
      const w = Math.round((y - 2) * 1.4);
      const x = 8 - Math.round(w / 2);
      px(ctx, x, y, w, 1, PAPER);
    }
    px(ctx, 7, 4, 2, 3, INK); // the "!"
    px(ctx, 7, 8, 2, 1, INK);
  });
}

// Build every world tile as a data URL, keyed by its map symbol. `accents` maps an axis to its land
// accent (theme.js LANDS) so the land grounds carry their land's signature colour.
export function makeTiles(accents = {}) {
  const a = { social: "#6f9bbc", economic: "#d9a441", coding: "#b06fbc", safety: "#bc6f6f", ...accents };
  return {
    G: tileDataURL(grass),
    P: tileDataURL(path),
    W: tileDataURL(water),
    T: tileDataURL(tree),
    S: tileDataURL(plazaTile(a.social)), // Society Square flagstone
    M: tileDataURL(cobbleTile(a.economic)), // Market Midway cobbles
    F: tileDataURL(plateTile(a.coding)), // Maker's Workshop checkerplate
    H: tileDataURL(concreteTile(a.safety)), // Safety Gauntlet concrete
    X: tileDataURL(hazardTile(a.safety)), // Safety Gauntlet hazard kerb
  };
}
