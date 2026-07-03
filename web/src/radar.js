// radar.js — the stats screen: an agent's four-axis skill profile, rendered from real engine JSON.
//
// The fixtures under ./fixtures/ are verbatim `parkbench radar --agent <a> --seed 1 --json` output
// (the same contract the static viewers consume). This screen *reads* those numbers and draws a radar
// — it never computes a score (D-012). Reachable from the overworld by pressing S.

import radarHeuristic from "./fixtures/radar-heuristic.json";
import radarGreedy from "./fixtures/radar-greedy.json";
import radarOptimal from "./fixtures/radar-optimal.json";
import radarRandom from "./fixtures/radar-random.json";
import { LANDS, PALETTE } from "./theme.js";
import { WORLD_W, WORLD_H } from "./world.js";

export const RADARS = {
  heuristic: radarHeuristic,
  greedy: radarGreedy,
  optimal: radarOptimal,
  random: radarRandom,
};
export const AGENT_ORDER = ["heuristic", "greedy", "optimal", "random"];

// Canonical axis order (matches LANDS + the engine's axis order): social, economic, coding, safety.
// Each gets a compass direction so the four axes fan out around the centre (up / right / down / left).
const AXES = LANDS.map((l, i) => ({
  axis: l.axis,
  name: l.name,
  accent: l.accent,
  angle: (-90 + i * 90) * (Math.PI / 180),
}));

const CX = WORLD_W / 2;
const CY = 160;
const R = 84;

function vertex(k, i, frac) {
  const a = AXES[i].angle;
  return k.vec2(CX + Math.cos(a) * R * frac, CY + Math.sin(a) * R * frac);
}

function drawRadar(k, data) {
  const ink = k.Color.fromHex(PALETTE.ink);
  const mid = k.Color.fromHex(PALETTE.mid);
  const light = k.Color.fromHex(PALETTE.light);
  const paper = k.Color.fromHex(PALETTE.paper);

  // Full-screen backdrop.
  k.drawRect({ pos: k.vec2(0, 0), width: WORLD_W, height: WORLD_H, color: ink });

  // Concentric rings (25/50/75/100%).
  for (const f of [0.25, 0.5, 0.75, 1]) {
    const ring = AXES.map((_, i) => vertex(k, i, f));
    k.drawPolygon({ pts: ring, fill: false, outline: { width: 1, color: mid } });
  }
  // Axis spokes.
  for (let i = 0; i < AXES.length; i++) {
    k.drawLine({ p1: k.vec2(CX, CY), p2: vertex(k, i, 1), width: 1, color: mid });
  }

  // The data polygon.
  const values = AXES.map((a) => data.axes[a.axis] ?? 0);
  const pts = AXES.map((_, i) => vertex(k, i, values[i]));
  k.drawPolygon({ pts, color: light, opacity: 0.45, outline: { width: 2, color: paper } });

  // Vertex dots + per-axis labels (name + value) in each land's accent.
  for (let i = 0; i < AXES.length; i++) {
    k.drawCircle({ pos: pts[i], radius: 2.5, color: k.Color.fromHex(AXES[i].accent) });
    const lab = vertex(k, i, 1.16);
    k.drawText({
      text: AXES[i].axis.toUpperCase(),
      pos: k.vec2(lab.x, lab.y - 5),
      size: 8,
      anchor: "center",
      font: "monospace",
      color: k.Color.fromHex(AXES[i].accent),
    });
    k.drawText({
      text: values[i].toFixed(3),
      pos: k.vec2(lab.x, lab.y + 4),
      size: 7,
      anchor: "center",
      font: "monospace",
      color: paper,
    });
  }

  // Title + footer hint.
  k.drawText({
    text: data.agent.toUpperCase(),
    pos: k.vec2(CX, 22),
    size: 20,
    anchor: "center",
    font: "monospace",
    color: paper,
  });
  k.drawText({
    text: "SKILL PROFILE · seed " + data.seed,
    pos: k.vec2(CX, 40),
    size: 8,
    anchor: "center",
    font: "monospace",
    color: light,
  });
  k.drawText({
    text: "← → cycle agent    S / Esc  back to park",
    pos: k.vec2(CX, WORLD_H - 14),
    size: 8,
    anchor: "center",
    font: "monospace",
    color: mid,
  });
}

// Define the "stats" scene. It takes the agent name to display.
export function registerStatsScene(k) {
  k.scene("stats", (agent = "heuristic") => {
    let idx = Math.max(0, AGENT_ORDER.indexOf(agent));
    k.onDraw(() => drawRadar(k, RADARS[AGENT_ORDER[idx]]));

    const cycle = (d) => {
      idx = (idx + d + AGENT_ORDER.length) % AGENT_ORDER.length;
    };
    k.onKeyPress("right", () => cycle(1));
    k.onKeyPress("left", () => cycle(-1));
    k.onKeyPress("s", () => k.go("park"));
    k.onKeyPress("escape", () => k.go("park"));
  });
}
