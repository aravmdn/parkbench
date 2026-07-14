// props.js — world dressing: an entrance sign, per-land flavor props, and a controls legend.
//
// Pure decoration to make the park feel inhabited and its controls discoverable. Presentation only
// (D-012). Props are procedural sprites (pixels.js); the legend/entrance are drawn objects.

import { LANDS, PALETTE, PARK_NAME } from "./theme.js";
import { landRect } from "./lands.js";
import { makeLamp, makeBench } from "./pixels.js";
import { WORLD_W, WORLD_H } from "./world.js";

export function buildProps(k) {
  k.loadSprite("lamp", makeLamp());
  k.loadSprite("bench", makeBench());

  // Four lamps framing the central crossroads.
  for (const [x, y] of [[134, 118], [170, 118], [134, 154], [170, 154]]) {
    k.add([k.sprite("lamp"), k.pos(x, y), k.anchor("center"), k.z(20)]);
  }

  // One bench per land, in open grass off to the side.
  for (const land of LANDS) {
    const r = landRect(land.axis);
    k.add([k.sprite("bench"), k.pos(r.x + 20, r.cy + 4), k.anchor("center"), k.z(20)]);
  }

  // Entrance signboard near the foot of the central path.
  const ex = WORLD_W / 2;
  const ey = 250;
  k.add([k.rect(2, 9), k.pos(ex - 32, ey + 7), k.anchor("center"), k.color(k.Color.fromHex("#6b4a2b")), k.z(23)]);
  k.add([k.rect(2, 9), k.pos(ex + 32, ey + 7), k.anchor("center"), k.color(k.Color.fromHex("#6b4a2b")), k.z(23)]);
  k.add([
    k.rect(98, 20),
    k.pos(ex, ey),
    k.anchor("center"),
    k.color(k.Color.fromHex("#8a5a34")),
    k.outline(2, k.Color.fromHex(PALETTE.ink)),
    k.z(24),
  ]);
  k.add([k.text(PARK_NAME, { size: 8, font: "monospace" }), k.pos(ex, ey - 3), k.anchor("center"), k.color(k.Color.fromHex(PALETTE.paper)), k.z(25)]);
  k.add([k.text("est. 2026", { size: 5, font: "monospace" }), k.pos(ex, ey + 6), k.anchor("center"), k.color(k.Color.fromHex("#e6d8b6")), k.z(25)]);

  // A controls legend pinned along the bottom (mirrors the top title plate).
  k.add([
    k.rect(WORLD_W, 14),
    k.pos(0, WORLD_H - 14),
    k.color(k.Color.fromHex(PALETTE.ink)),
    k.opacity(0.6),
    k.fixed(),
    k.z(100),
  ]);
  k.add([
    k.text("arrows: walk · tab: pick trainer · S: stats · H: hall · gyms: ride", {
      size: 7,
      font: "monospace",
    }),
    k.pos(WORLD_W / 2, WORLD_H - 7),
    k.anchor("center"),
    k.color(k.Color.fromHex(PALETTE.light)),
    k.fixed(),
    k.z(101),
  ]);
}
