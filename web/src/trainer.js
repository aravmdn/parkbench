// trainer.js — the agent avatar: a trainer sprite that walks the overworld.
//
// A trainer is an agent (heuristic / greedy / optimal / llm / BYO…). This lap adds one with a
// 4-direction walk cycle: arrow-key controllable, and — so the world is alive on load and in
// screenshots — auto-patrolling the park paths when idle. Presentation only (D-012).

import { makeTrainer, TRAINER_COLS, TRAINER_ROWS } from "./pixels.js";
import { WORLD_W, WORLD_H } from "./world.js";
import { PALETTE } from "./theme.js";

const SPEED = 52; // px/sec

export function addTrainer(k, agent = "heuristic", startX = 152, startY = 138) {
  k.loadSprite("trainer", makeTrainer(), {
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
    k.sprite("trainer"),
    k.pos(startX, startY),
    k.anchor("center"),
    k.z(40),
    k.scale(1.5),
    { facing: "down", agent },
  ]);
  let curName = "down-idle";
  t.play(curName);

  // A small name tag showing which agent this trainer is; follows the sprite.
  const tag = k.add([
    k.text(agent, { size: 6, font: "monospace" }),
    k.pos(startX, startY - 16),
    k.anchor("center"),
    k.color(k.Color.fromHex(PALETTE.paper)),
    k.outline(2, k.Color.fromHex(PALETTE.ink)),
    k.z(41),
  ]);

  const setAnim = (dir, moving) => {
    t.facing = dir;
    const name = moving ? dir : dir + "-idle";
    if (curName !== name) {
      curName = name;
      t.play(name);
    }
  };

  // A scripted patrol loop around the central crossroads, so the trainer is visibly walking.
  const route = [
    [152, 60],
    [152, 138],
    [56, 138],
    [152, 138],
    [152, 236],
    [152, 138],
    [252, 138],
    [152, 138],
  ];
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
    // Frozen while a gym run's overlay is showing (gymrun.js sets t.paused).
    if (t.paused) {
      setAnim(t.facing, false);
      tag.pos = k.vec2(t.pos.x, t.pos.y - 16);
      return;
    }

    // Player control takes over whenever an arrow key is held.
    const kd = heldDir();
    if (kd) {
      const [dx, dy] = DELTA[kd];
      t.move(dx * SPEED, dy * SPEED);
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
        t.move((dx / dist) * SPEED, (dy / dist) * SPEED);
        setAnim(dir, true);
      }
    }

    // Keep the trainer on-screen (leave room for the top title plate).
    t.pos.x = Math.max(10, Math.min(WORLD_W - 10, t.pos.x));
    t.pos.y = Math.max(24, Math.min(WORLD_H - 10, t.pos.y));
    tag.pos = k.vec2(t.pos.x, t.pos.y - 16);
  });

  return t;
}
