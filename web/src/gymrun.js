// gymrun.js — the "trainer enters gym → run plays → result" beat.
//
// Walking the trainer onto a gym triggers a short "NOW RIDING…" pause, then reveals that agent+ride's
// **score** — read verbatim from the radar fixture (`rides[].score`, i.e. `parkbench radar --json`).
// Presentation only (D-012): it reveals a number the engine already computed; it never scores.

import { RADARS } from "./radar.js";
import { PALETTE } from "./theme.js";
import { WORLD_W, WORLD_H } from "./world.js";

// The per-ride score for this agent, straight from the radar fixture.
function scoreFor(agent, ride) {
  const data = RADARS[agent];
  const leg = data?.rides?.find((r) => r.ride === ride);
  return leg ? leg.score : null;
}

// Wire gym-run detection + the overlay onto the park scene. `gyms` is buildGyms()'s return value.
export function setupGymRuns(k, trainer, gyms) {
  let mode = "walk"; // walk | riding | result
  let active = null; // { ride, marquee, score }
  let t0 = 0;
  const cooldownUntil = {}; // ride -> time; avoids instantly re-triggering while stood on the gym

  const RIDING_SECS = 1.3;
  const RESULT_SECS = 3.2;

  k.onUpdate(() => {
    const now = k.time();
    if (mode === "walk") {
      for (const g of gyms) {
        if (cooldownUntil[g.ride] && now < cooldownUntil[g.ride]) continue;
        // AABB overlap (with a small margin) between the trainer and the gym footprint.
        const m = 6;
        if (
          trainer.pos.x > g.x - m &&
          trainer.pos.x < g.x + g.w + m &&
          trainer.pos.y > g.y - m &&
          trainer.pos.y < g.y + g.h + m
        ) {
          active = { ride: g.ride, marquee: g.marquee, score: scoreFor(trainer.agent, g.ride) };
          mode = "riding";
          t0 = now;
          trainer.paused = true;
          break;
        }
      }
    } else if (mode === "riding") {
      if (now - t0 > RIDING_SECS) {
        mode = "result";
        t0 = now;
      }
    } else if (mode === "result") {
      if (now - t0 > RESULT_SECS) dismiss();
    }
  });

  function dismiss() {
    if (active) cooldownUntil[active.ride] = k.time() + 2.0;
    trainer.pos.y += 22; // step back off the gym so it doesn't immediately re-trigger
    trainer.paused = false;
    mode = "walk";
    active = null;
  }
  k.onKeyPress("space", () => mode === "result" && dismiss());
  k.onKeyPress("enter", () => mode === "result" && dismiss());

  k.onDraw(() => {
    if (mode === "walk") return;
    const cx = WORLD_W / 2;
    k.drawRect({
      pos: k.vec2(0, 0),
      width: WORLD_W,
      height: WORLD_H,
      color: k.Color.fromHex(PALETTE.ink),
      opacity: 0.92,
    });

    if (mode === "riding") {
      const dots = ".".repeat(1 + (Math.floor(k.time() * 3) % 3));
      k.drawText({ text: "NOW RIDING", pos: k.vec2(cx, 118), size: 14, anchor: "center", font: "monospace", color: k.Color.fromHex(PALETTE.paper) });
      k.drawText({ text: active.marquee, pos: k.vec2(cx, 144), size: 9, anchor: "center", font: "monospace", color: k.Color.fromHex(PALETTE.light) });
      k.drawText({ text: dots, pos: k.vec2(cx, 168), size: 16, anchor: "center", font: "monospace", color: k.Color.fromHex(PALETTE.light) });
    } else {
      const s = active.score;
      const sHex = s == null ? PALETTE.mid : s >= 0.8 ? PALETTE.light : s >= 0.5 ? "#d9a441" : "#e05a5a";
      k.drawText({ text: trainer.agent.toUpperCase() + " RODE", pos: k.vec2(cx, 96), size: 10, anchor: "center", font: "monospace", color: k.Color.fromHex(PALETTE.mid) });
      k.drawText({ text: active.marquee, pos: k.vec2(cx, 116), size: 10, anchor: "center", font: "monospace", color: k.Color.fromHex(PALETTE.paper) });
      k.drawText({ text: "SCORE", pos: k.vec2(cx, 148), size: 8, anchor: "center", font: "monospace", color: k.Color.fromHex(PALETTE.mid) });
      k.drawText({ text: s == null ? "—" : s.toFixed(3), pos: k.vec2(cx, 170), size: 24, anchor: "center", font: "monospace", color: k.Color.fromHex(sHex) });
      k.drawText({ text: "SPACE  back to park", pos: k.vec2(cx, WORLD_H - 28), size: 8, anchor: "center", font: "monospace", color: k.Color.fromHex(PALETTE.mid) });
    }
  });
}
