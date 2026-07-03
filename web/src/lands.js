// lands.js — the four lands overlaid on the overworld.
//
// The central crossroads (world.js) splits the park into four quadrants; each is one skill axis's
// land (social / economic / coding / safety), mirroring theme.py's LANDS. This tints each quadrant
// with its accent colour and plants a labeled town sign. Presentation only (D-012) — it draws the
// engine's vocabulary, it never scores.

import { LANDS, PALETTE } from "./theme.js";
import { TILE } from "./pixels.js";

// Inclusive tile-index rectangle for each land's quadrant (carved out by the crossroads at
// cols 9-10 / rows 8-9). Keyed by axis; matches the grid hints in theme.js.
const QUADRANTS = {
  social: { c0: 1, c1: 8, r0: 1, r1: 7 }, // top-left
  economic: { c0: 11, c1: 18, r0: 1, r1: 7 }, // top-right
  coding: { c0: 1, c1: 8, r0: 10, r1: 16 }, // bottom-left
  safety: { c0: 11, c1: 18, r0: 10, r1: 16 }, // bottom-right
};

// A land's on-screen pixel rectangle + horizontal centre.
export function landRect(axis) {
  const q = QUADRANTS[axis];
  const x = q.c0 * TILE;
  const y = q.r0 * TILE;
  const w = (q.c1 - q.c0 + 1) * TILE;
  const h = (q.r1 - q.r0 + 1) * TILE;
  return { x, y, w, h, cx: x + w / 2, cy: y + h / 2 };
}

export function buildLands(k) {
  for (const land of LANDS) {
    const r = landRect(land.axis);

    // Faint accent wash so each region reads as its own place (grass still shows through).
    k.add([
      k.rect(r.w, r.h),
      k.pos(r.x, r.y),
      k.color(k.Color.fromHex(land.accent)),
      k.opacity(0.16),
      k.z(10),
    ]);

    // A town sign near the top of the quadrant: an ink plate with an accent border, the land name,
    // and its axis underneath.
    const labelY = r.y + 22;
    const plateW = Math.max(land.name.length, land.axis.length + 4) * 5 + 12;

    k.add([
      k.rect(plateW + 2, 24),
      k.pos(r.cx, labelY),
      k.anchor("center"),
      k.color(k.Color.fromHex(land.accent)),
      k.z(20),
    ]);
    k.add([
      k.rect(plateW, 22),
      k.pos(r.cx, labelY),
      k.anchor("center"),
      k.color(k.Color.fromHex(PALETTE.ink)),
      k.opacity(0.86),
      k.z(21),
    ]);
    k.add([
      k.text(land.name, { size: 8, font: "monospace" }),
      k.pos(r.cx, labelY - 4),
      k.anchor("center"),
      k.color(k.Color.fromHex(PALETTE.paper)),
      k.z(22),
    ]);
    k.add([
      k.text(land.axis.toUpperCase(), { size: 6, font: "monospace" }),
      k.pos(r.cx, labelY + 6),
      k.anchor("center"),
      k.color(k.Color.fromHex(land.accent)),
      k.z(22),
    ]);
  }
}
