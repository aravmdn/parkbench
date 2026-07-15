// halloffame.js — the Hall of Fame: the ranked leaderboard, drawn from real engine JSON.
//
// The fixture is verbatim `parkbench leaderboard --seed 1 --json` output. This scene *reads* the
// ranking and draws it (career score = capability × reputation per agent) — it never computes a score
// (D-012). Reachable from the overworld by pressing H.

import leaderboard from "./fixtures/leaderboard.json";
import { PALETTE } from "./theme.js";
import { WORLD_W, WORLD_H } from "./world.js";

// Colour each agent's bar by rank (gold / silver / bronze / rest).
const RANK_COLORS = ["#d9a441", "#b8c0c8", "#b07a44", "#7a8a6a"];

function drawHallOfFame(k) {
  const ink = k.Color.fromHex(PALETTE.ink);
  const mid = k.Color.fromHex(PALETTE.mid);
  const light = k.Color.fromHex(PALETTE.light);
  const paper = k.Color.fromHex(PALETTE.paper);

  k.drawRect({ pos: k.vec2(0, 0), width: WORLD_W, height: WORLD_H, color: ink });

  k.drawText({
    text: "HALL OF FAME",
    pos: k.vec2(WORLD_W / 2, 22),
    size: 20,
    anchor: "center",
    font: "monospace",
    color: paper,
  });
  k.drawText({
    text: "career = capability × reputation · seed " + leaderboard.seed,
    pos: k.vec2(WORLD_W / 2, 40),
    size: 8,
    anchor: "center",
    font: "monospace",
    color: light,
  });

  const ranking = leaderboard.ranking;
  const rowH = 40;
  const top = 62;
  const barX = 96;
  const barMaxW = WORLD_W - barX - 20;

  ranking.forEach((r, i) => {
    const y = top + i * rowH;
    const color = k.Color.fromHex(RANK_COLORS[Math.min(i, RANK_COLORS.length - 1)]);

    // Rank + agent name.
    k.drawText({
      text: `${i + 1}`,
      pos: k.vec2(12, y + 6),
      size: 14,
      font: "monospace",
      color,
    });
    k.drawText({
      text: r.agent.toUpperCase(),
      pos: k.vec2(30, y + 2),
      size: 11,
      font: "monospace",
      color: paper,
    });
    k.drawText({
      text: `cap ${r.mean_capability.toFixed(2)}  ·  rep ${r.reputation.toFixed(2)}`,
      pos: k.vec2(30, y + 16),
      size: 7,
      font: "monospace",
      color: mid,
    });

    // Career-score bar (career_score is already 0..1).
    const w = Math.max(2, barMaxW * r.career_score);
    k.drawRect({ pos: k.vec2(barX, y + 2), width: barMaxW, height: 12, color: k.Color.fromHex(PALETTE.shadow) });
    k.drawRect({ pos: k.vec2(barX, y + 2), width: w, height: 12, color });
    k.drawText({
      text: r.career_score.toFixed(3),
      pos: k.vec2(barX + barMaxW, y + 18),
      size: 8,
      anchor: "topright",
      font: "monospace",
      color: paper,
    });
  });

  k.drawText({
    text:
      "H / Esc  back to park" +
      (leaderboard.benchmark_version ? "   ·   bench v" + leaderboard.benchmark_version : ""),
    pos: k.vec2(WORLD_W / 2, WORLD_H - 14),
    size: 8,
    anchor: "center",
    font: "monospace",
    color: mid,
  });
}

export function registerHallOfFameScene(k) {
  k.scene("halloffame", () => {
    k.onDraw(() => drawHallOfFame(k));
    k.onKeyPress("h", () => k.go("park"));
    k.onKeyPress("escape", () => k.go("park"));
  });
}
