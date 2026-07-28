// landart.js — the four lands' scenery: one motif per land, placed on its paved forecourt.
//
// The ground treatments live in the tilemap (world.js LAND_GROUND + pixels.js); this adds the
// freestanding props that finish the theming, so a spectator can tell Society Square from Market
// Midway from Maker's Workshop from the Safety Gauntlet at a glance:
//
//   Society Square (social)     — a stone fountain on the plaza, clipped topiary hedges.
//   Market Midway (economic)    — two awninged market stalls flanking the gym, goods barrels.
//   Maker's Workshop (coding)   — crate stacks, an anvil, a cog wheel in the works yard.
//   Safety Gauntlet (safety)    — a warning sign, traffic cones, a striped barrier past the kerb.
//
// All art is procedurally generated in pixels.js (original / CC0 by construction — see the art
// policy in docs/11-visual-world.md), drawn once at boot; nothing allocates per frame. Placement is
// hand-tuned to keep every prop **off the crossroads paths** (cols 9-10 / rows 8-9 — the trainers'
// patrol routes) and **off the gym footprints + their approach**, so the world stays walkable and
// gym entry still triggers. Presentation only (D-012).

import { LANDS } from "./theme.js";
import {
  makeFountain,
  makeHedge,
  makeStall,
  makeBarrel,
  makeCrates,
  makeAnvil,
  makeCog,
  makeCone,
  makeBarrier,
  makeWarnSign,
} from "./pixels.js";

const ACCENT = Object.fromEntries(LANDS.map((l) => [l.axis, l.accent]));

// [sprite key, centre x, centre y] — world pixels (the map is a fixed 320×288 layout).
const PLACEMENTS = [
  // Society Square — the fountain is the plaza's centrepiece; hedges frame the gym forecourt.
  ["prop-fountain", 80, 76],
  ["prop-hedge", 34, 100],
  ["prop-hedge", 138, 100],
  ["prop-hedge", 34, 122],
  ["prop-hedge", 138, 122],

  // Market Midway — stalls either side of the Knapsack Coaster, barrels between.
  ["prop-stall", 192, 110],
  ["prop-stall", 288, 110],
  ["prop-barrel", 214, 118],
  ["prop-barrel", 266, 118],

  // Maker's Workshop — the works yard: crates, an anvil, a spare cog. Kept clear of the entrance
  // signboard (props.js draws it over x≈111-209, y≈240-260 at a higher z).
  ["prop-crates", 40, 231],
  ["prop-crates", 106, 232],
  ["prop-cog", 130, 231],
  ["prop-anvil", 40, 259],

  // Safety Gauntlet — the hazard course past the striped kerb.
  ["prop-warnsign", 205, 234],
  ["prop-cone", 205, 262],
  ["prop-cone", 274, 264],
  ["prop-barrier", 283, 235],
];

export function buildLandArt(k) {
  k.loadSprite("prop-fountain", makeFountain(ACCENT.social));
  k.loadSprite("prop-hedge", makeHedge());
  k.loadSprite("prop-stall", makeStall(ACCENT.economic));
  k.loadSprite("prop-barrel", makeBarrel());
  k.loadSprite("prop-crates", makeCrates());
  k.loadSprite("prop-anvil", makeAnvil());
  k.loadSprite("prop-cog", makeCog(ACCENT.coding));
  k.loadSprite("prop-cone", makeCone(ACCENT.safety));
  k.loadSprite("prop-barrier", makeBarrier(ACCENT.safety));
  k.loadSprite("prop-warnsign", makeWarnSign(ACCENT.safety));

  // z 22: above the land wash (10), the signs (20-21) are elsewhere on the map, below the gyms (30)
  // and the trainers (40), so a trainer always walks in front of the scenery.
  for (const [sprite, x, y] of PLACEMENTS) {
    k.add([k.sprite(sprite), k.pos(x, y), k.anchor("center"), k.z(22)]);
  }
}
