// trainer.js — the agent avatars: trainer sprites that walk the overworld.
//
// A trainer is an agent (heuristic / greedy / optimal / random / llm / BYO…). Each baseline agent
// now walks the park at once: every instance gets its own palette-swapped sprite sheet (pixels.js
// re-tints the same procedural drawing — original / CC0 by construction), its own patrol route +
// speed, and a name tag. One trainer is the *player* (arrow-key control overrides its patrol; it is
// the one that enters gyms); the rest wander as NPCs. A **BYO** (bring-your-own) agent joins the same
// way — an additional palette-swapped trainer that carries a "BYO" chip over its name tag so
// spectators can tell a third-party agent from the built-in baselines (its identity + radar come from
// a completed run's JSON, D-038). `setSelected` highlights whichever trainer is currently driving the
// S stats screen. Presentation only (D-012).

import { makeTrainer, TRAINER_COLS, TRAINER_ROWS } from "./pixels.js";
import { WORLD_W, WORLD_H } from "./world.js";
import { PALETTE } from "./theme.js";

const SPEED = 52; // default px/sec

// Palette-swapped outfits so each baseline agent reads at a glance (cap + shirt hex fed to
// pixels.js's trainer generator; pants default everywhere so the silhouette stays shared).
export const AGENT_OUTFITS = {
  heuristic: { cap: "#c0392b", shirt: "#3f7d9a" }, // the classic red-cap look — the player
  greedy: { cap: "#d9a441", shirt: "#a8752c" }, // gold — the Market Midway star (and reward-hacker)
  optimal: { cap: "#e6f0d6", shirt: "#8a5aa8" }, // white cap + violet — the champion
  random: { cap: "#52525a", shirt: "#8a8f98" }, // grey — the coin-flipper
  "acme-bot": { cap: "#2f9e8f", shirt: "#e08a3c" }, // teal + orange — a BYO (bring-your-own) agent
};

// The classic patrol: out-and-back along each arm of the central crossroads.
const DEFAULT_ROUTE = [
  [152, 60],
  [152, 138],
  [56, 138],
  [152, 138],
  [152, 236],
  [152, 138],
  [252, 138],
  [152, 138],
];

const SELECTED_HEX = "#f6de8a"; // lamp-glow gold for the selected trainer's tag
const BYO_HEX = "#e08a3c"; // orange — marks a bring-your-own (third-party) trainer

export function addTrainer(k, agent = "heuristic", opts = {}) {
  const {
    x: startX = 152,
    y: startY = 138,
    route = DEFAULT_ROUTE,
    speed = SPEED,
    player = false,
    byo = false,
    label = agent,
  } = opts;

  k.loadSprite("trainer-" + agent, makeTrainer(AGENT_OUTFITS[agent]), {
    sliceX: TRAINER_COLS,
    sliceY: TRAINER_ROWS,
    anims: {
      down: { from: 0, to: 2, loop: true, speed: 6 },
      left: { from: 3, to: 5, loop: true, speed: 6 },
      right: { from: 6, to: 8, loop: true, speed: 6 },
      up: { from: 9, to: 11, loop: true, speed: 6 },
      "down-idle": { from: 1, to: 1 },
      "left-idle": { from: 4, to: 4 },
      "right-idle": { from: 7, to: 7 },
      "up-idle": { from: 10, to: 10 },
    },
  });

  const t = k.add([
    k.sprite("trainer-" + agent),
    k.pos(startX, startY),
    k.anchor("center"),
    k.z(40),
    k.scale(1.5),
    { facing: "down", agent, player },
  ]);
  let curName = "down-idle";
  t.play(curName);

  // A small name tag showing which agent this trainer is; follows the sprite. BYO trainers show the
  // agent's own name (`label`) tinted the BYO accent so a third-party stands out from the baselines.
  const tag = k.add([
    k.text(label, { size: 6, font: "monospace" }),
    k.pos(startX, startY - 16),
    k.anchor("center"),
    k.color(k.Color.fromHex(byo ? BYO_HEX : PALETTE.paper)),
    k.outline(2, k.Color.fromHex(PALETTE.ink)),
    k.z(41),
  ]);

  // A "BYO" chip riding above the name tag — the at-a-glance mark of a bring-your-own trainer.
  const byoChip = byo
    ? k.add([
        k.text("BYO", { size: 6, font: "monospace" }),
        k.pos(startX, startY - 24),
        k.anchor("center"),
        k.color(k.Color.fromHex(BYO_HEX)),
        k.outline(2, k.Color.fromHex(PALETTE.ink)),
        k.z(41),
      ])
    : null;

  // Highlight (or clear) this trainer as the one the stats screen will show.
  t.setSelected = (sel) => {
    tag.text = (sel ? ">" : "") + label;
    tag.color = k.Color.fromHex(sel ? SELECTED_HEX : byo ? BYO_HEX : PALETTE.paper);
  };

  const setAnim = (dir, moving) => {
    t.facing = dir;
    const name = moving ? dir : dir + "-idle";
    if (curName !== name) {
      curName = name;
      t.play(name);
    }
  };

  let wp = 0;

  const heldDir = () => {
    if (k.isKeyDown("left")) return "left";
    if (k.isKeyDown("right")) return "right";
    if (k.isKeyDown("up")) return "up";
    if (k.isKeyDown("down")) return "down";
    return null;
  };
  const DELTA = { left: [-1, 0], right: [1, 0], up: [0, -1], down: [0, 1] };

  t.onUpdate(() => {
    // Frozen while a gym run's overlay is showing (gymrun.js sets t.paused on the player).
    if (t.paused) {
      setAnim(t.facing, false);
      tag.pos = k.vec2(t.pos.x, t.pos.y - 16);
      if (byoChip) byoChip.pos = k.vec2(t.pos.x, t.pos.y - 24);
      return;
    }

    // Player control takes over whenever an arrow key is held (player trainer only).
    const kd = player ? heldDir() : null;
    if (kd) {
      const [dx, dy] = DELTA[kd];
      t.move(dx * speed, dy * speed);
      setAnim(kd, true);
    } else {
      // Auto-patrol toward the current waypoint.
      const [tx, ty] = route[wp];
      const dx = tx - t.pos.x;
      const dy = ty - t.pos.y;
      const dist = Math.hypot(dx, dy);
      if (dist < 2) {
        wp = (wp + 1) % route.length;
        setAnim(t.facing, false);
      } else {
        const dir = Math.abs(dx) > Math.abs(dy) ? (dx < 0 ? "left" : "right") : dy < 0 ? "up" : "down";
        t.move((dx / dist) * speed, (dy / dist) * speed);
        setAnim(dir, true);
      }
    }

    // Keep the trainer on-screen (leave room for the top title plate).
    t.pos.x = Math.max(10, Math.min(WORLD_W - 10, t.pos.x));
    t.pos.y = Math.max(24, Math.min(WORLD_H - 10, t.pos.y));
    tag.pos = k.vec2(t.pos.x, t.pos.y - 16);
    if (byoChip) byoChip.pos = k.vec2(t.pos.x, t.pos.y - 24);
  });

  return t;
}
