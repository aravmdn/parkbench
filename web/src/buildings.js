// buildings.js — a gym building per ride, placed in its land.
//
// Each scored ride (theme.py's ATTRACTIONS) gets an enterable-looking gym in its land's quadrant,
// tinted with the land accent. Entering a gym = an agent attempting that benchmark (a later lap wires
// the actual run). Presentation only (D-012).

import { ATTRACTIONS, LANDS, PALETTE } from "./theme.js";
import { landRect } from "./lands.js";
import { makeBuilding, BUILDING_W, BUILDING_H } from "./pixels.js";

export function buildGyms(k) {
  const accentByAxis = Object.fromEntries(LANDS.map((l) => [l.axis, l.accent]));

  // One building sprite per land (accent-tinted); reused by every gym in that land.
  for (const l of LANDS) k.loadSprite("gym-" + l.axis, makeBuilding(l.accent));

  // Group rides by land so lands with several rides (social has two) space their gyms out.
  const byAxis = {};
  for (const a of ATTRACTIONS) (byAxis[a.axis] ||= []).push(a);

  for (const [axis, rides] of Object.entries(byAxis)) {
    const r = landRect(axis);
    const gap = 8;
    const totalW = rides.length * BUILDING_W + (rides.length - 1) * gap;
    const startX = Math.round(r.cx - totalW / 2);
    const by = r.y + r.h - BUILDING_H - 6; // bottom-aligned in the quadrant (clears the sign + pond)

    rides.forEach((a, i) => {
      const bx = startX + i * (BUILDING_W + gap);
      k.add([k.sprite("gym-" + axis), k.pos(bx, by), k.z(30)]);
      // Nameplate under the door with the ride's engine key (the link back to mechanics).
      k.add([
        k.text(a.ride, { size: 6, font: "monospace" }),
        k.pos(bx + BUILDING_W / 2, by + BUILDING_H + 3),
        k.anchor("center"),
        k.color(k.Color.fromHex(PALETTE.paper)),
        k.outline(2, k.Color.fromHex(PALETTE.ink)),
        k.z(31),
      ]);
    });
  }
}
