// radar.js — the stats screen: an agent's four-axis skill profile + its career badges, from real JSON.
//
// The numbers are verbatim `parkbench radar --agent <a> --json`; the badge row reads verbatim
// `parkbench leaderboard --json` (per-ride integrity + reputation). Both come from `profiles.js`,
// which serves them **live** from a running `parkbench serve --profiles` endpoint when the page asked
// for one and it is reachable, and from the committed fixtures otherwise — the screen prints which
// (the `live` / `fixture` tag beside the `bench vX.Y.Z` stamp). This screen only *reads* those numbers
// and draws them (D-012) — it never computes a score. Reachable with S.

import {
  RADARS,
  AGENT_ORDER,
  getLeaderboard,
  radarSource,
  leaderboardSource,
} from "./profiles.js";
import { LANDS, ATTRACTIONS, PALETTE } from "./theme.js";
import { WORLD_W, WORLD_H } from "./world.js";

// `acme-bot` is a bring-your-own (third-party) agent: its radar + D-038 identity come from a
// completed run's JSON (not the engine's baseline roster), so it renders alongside the baselines but
// is marked BYO wherever it appears. See docs/09-byo-protocol.md.
export { RADARS, AGENT_ORDER };

const BYO_HEX = "#e08a3c"; // orange — the BYO accent, matching the trainer's chip

// Canonical axis order (matches LANDS + the engine's axis order): social, economic, coding, safety.
const AXES = LANDS.map((l, i) => ({
  axis: l.axis,
  name: l.name,
  accent: l.accent,
  angle: (-90 + i * 90) * (Math.PI / 180),
}));

// --- Career badges (from the leaderboard fixture) -------------------------------------------------
// One gym badge per ride: earned when that ride's integrity is intact, cracked/revoked when it isn't
// (the reward-hacker's collapse), faint when the agent skipped the ride. Reputation = product of the
// leg integrities, straight from the engine.
const RIDE_ORDER = ATTRACTIONS.map((a) => a.ride); // negotiation, commons, economic, coding, safety
const ACCENT_BY_RIDE = Object.fromEntries(
  ATTRACTIONS.map((a) => [a.ride, LANDS.find((l) => l.axis === a.axis).accent]),
);
const RIDE_SHORT = {
  negotiation: "NEG",
  commons: "COM",
  economic: "ECO",
  coding: "COD",
  safety: "SAF",
};
// Derived from whichever leaderboard payload is current (fixture or live), and re-derived only when
// that payload is replaced — the live fetch swaps the object, so identity is the cache key.
let careerCache = { from: null, byAgent: {} };
function careerFor(agent) {
  const lb = getLeaderboard();
  if (careerCache.from !== lb) {
    careerCache = {
      from: lb,
      byAgent: Object.fromEntries(
        (lb.ranking || []).map((r) => {
          const integrityByRide = {};
          for (const leg of r.legs || []) integrityByRide[leg.ride] = leg.integrity;
          return [
            r.agent,
            { reputation: r.reputation, integrityByRide, skipped: new Set(r.skipped_rides || []) },
          ];
        }),
      ),
    };
  }
  return careerCache.byAgent[agent];
}

const WARN = "#e05a5a"; // cracked-badge red

const CX = WORLD_W / 2;
const CY = 148;
const R = 64;

function vertex(k, i, frac) {
  const a = AXES[i].angle;
  return k.vec2(CX + Math.cos(a) * R * frac, CY + Math.sin(a) * R * frac);
}

function drawRadarShape(k, data) {
  const mid = k.Color.fromHex(PALETTE.mid);
  const light = k.Color.fromHex(PALETTE.light);
  const paper = k.Color.fromHex(PALETTE.paper);

  for (const f of [0.25, 0.5, 0.75, 1]) {
    const ring = AXES.map((_, i) => vertex(k, i, f));
    k.drawPolygon({ pts: ring, fill: false, outline: { width: 1, color: mid } });
  }
  for (let i = 0; i < AXES.length; i++) {
    k.drawLine({ p1: k.vec2(CX, CY), p2: vertex(k, i, 1), width: 1, color: mid });
  }

  const values = AXES.map((a) => data.axes[a.axis] ?? 0);
  const pts = AXES.map((_, i) => vertex(k, i, values[i]));
  k.drawPolygon({ pts, color: light, opacity: 0.45, outline: { width: 2, color: paper } });

  for (let i = 0; i < AXES.length; i++) {
    k.drawCircle({ pos: pts[i], radius: 2.5, color: k.Color.fromHex(AXES[i].accent) });
    const lab = vertex(k, i, 1.2);
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
}

function drawBadges(k, agent) {
  const c = careerFor(agent);
  if (!c) return;

  // Reputation line — colour-coded by how intact the career is.
  const repHex = c.reputation >= 0.999 ? PALETTE.light : c.reputation >= 0.5 ? "#d9a441" : WARN;
  k.drawText({
    text: "REPUTATION " + c.reputation.toFixed(3),
    pos: k.vec2(CX, 52),
    size: 9,
    anchor: "center",
    font: "monospace",
    color: k.Color.fromHex(repHex),
  });

  // Badge shelf.
  k.drawLine({
    p1: k.vec2(16, 232),
    p2: k.vec2(WORLD_W - 16, 232),
    width: 1,
    color: k.Color.fromHex(PALETTE.mid),
  });
  k.drawText({
    text: "GYM BADGES · " + leaderboardSource(),
    pos: k.vec2(CX, 240),
    size: 7,
    anchor: "center",
    font: "monospace",
    color: k.Color.fromHex(PALETTE.mid),
  });

  const by = 258;
  RIDE_ORDER.forEach((ride, i) => {
    const x = CX + (i - 2) * 58;
    const accent = k.Color.fromHex(ACCENT_BY_RIDE[ride]);
    const attempted = !c.skipped.has(ride) && ride in c.integrityByRide;
    const integ = c.integrityByRide[ride];

    if (!attempted) {
      k.drawCircle({
        pos: k.vec2(x, by),
        radius: 8,
        color: k.Color.fromHex(PALETTE.shadow),
        opacity: 0.5,
        outline: { width: 1, color: k.Color.fromHex(PALETTE.mid) },
      });
      k.drawText({
        text: "-",
        pos: k.vec2(x, by - 1),
        size: 9,
        anchor: "center",
        font: "monospace",
        color: k.Color.fromHex(PALETTE.mid),
      });
    } else if (integ >= 0.999) {
      // Earned: bright accent medal + check.
      k.drawCircle({ pos: k.vec2(x, by), radius: 8, color: accent });
      k.drawLine({ p1: k.vec2(x - 4, by + 1), p2: k.vec2(x - 1, by + 4), width: 2, color: k.Color.fromHex(PALETTE.ink) });
      k.drawLine({ p1: k.vec2(x - 1, by + 4), p2: k.vec2(x + 4, by - 3), width: 2, color: k.Color.fromHex(PALETTE.ink) });
    } else {
      // Cracked/revoked: dimmed medal + a red X (the reward-hacker loses the badge).
      k.drawCircle({
        pos: k.vec2(x, by),
        radius: 8,
        color: accent,
        opacity: 0.28,
        outline: { width: 1, color: k.Color.fromHex(WARN) },
      });
      k.drawLine({ p1: k.vec2(x - 3, by - 3), p2: k.vec2(x + 3, by + 3), width: 2, color: k.Color.fromHex(WARN) });
      k.drawLine({ p1: k.vec2(x - 3, by + 3), p2: k.vec2(x + 3, by - 3), width: 2, color: k.Color.fromHex(WARN) });
    }

    const labelHex = !attempted ? PALETTE.mid : integ >= 0.999 ? ACCENT_BY_RIDE[ride] : WARN;
    k.drawText({
      text: RIDE_SHORT[ride],
      pos: k.vec2(x, by + 11),
      size: 6,
      anchor: "center",
      font: "monospace",
      color: k.Color.fromHex(labelHex),
    });
  });
}

// A BYO agent has no career leg on the official leaderboard, so where a baseline shows its reputation
// + gym badges, a BYO shows its D-038 identity (name · version · config_hash — read straight from the
// run's JSON) and a plain note that it isn't ranked. Presentation only (D-012).
function drawByoIdentity(k, identity) {
  const id = identity || {};
  const parts = ["BYO AGENT"];
  if (id.version) parts.push("v" + id.version);
  if (id.config_hash) parts.push("#" + id.config_hash);
  k.drawText({
    text: parts.join(" · "),
    pos: k.vec2(CX, 52),
    size: 9,
    anchor: "center",
    font: "monospace",
    color: k.Color.fromHex(BYO_HEX),
  });

  k.drawLine({ p1: k.vec2(16, 232), p2: k.vec2(WORLD_W - 16, 232), width: 1, color: k.Color.fromHex(PALETTE.mid) });
  k.drawText({
    text: "GYM BADGES",
    pos: k.vec2(CX, 240),
    size: 7,
    anchor: "center",
    font: "monospace",
    color: k.Color.fromHex(PALETTE.mid),
  });
  k.drawText({
    text: "bring-your-own agent — not on the official leaderboard",
    pos: k.vec2(CX, 260),
    size: 7,
    anchor: "center",
    font: "monospace",
    color: k.Color.fromHex(PALETTE.mid),
  });
}

function drawStats(k, agent) {
  const data = RADARS[agent];
  const byo = !!data.byo;
  k.drawRect({ pos: k.vec2(0, 0), width: WORLD_W, height: WORLD_H, color: k.Color.fromHex(PALETTE.ink) });

  k.drawText({
    text: agent.toUpperCase(),
    pos: k.vec2(CX, 22),
    size: 20,
    anchor: "center",
    font: "monospace",
    color: k.Color.fromHex(byo ? BYO_HEX : PALETTE.paper),
  });
  const src = radarSource(agent);
  k.drawText({
    text:
      (byo ? "BYO SKILL PROFILE · seed " : "SKILL PROFILE · seed ") +
      data.seed +
      (data.benchmark_version ? " · bench v" + data.benchmark_version : "") +
      " · " +
      src,
    pos: k.vec2(CX, 40),
    size: 8,
    anchor: "center",
    font: "monospace",
    color: k.Color.fromHex(PALETTE.light),
  });
  // Where these numbers came from, stated plainly: LIVE = fetched from a running
  // `parkbench serve --profiles`; FIXTURE = the committed export (see profiles.js).
  k.drawText({
    text: src === "live" ? "● LIVE" : "○ FIXTURE",
    pos: k.vec2(WORLD_W - 8, 8),
    size: 7,
    anchor: "topright",
    font: "monospace",
    color: k.Color.fromHex(src === "live" ? PALETTE.light : PALETTE.mid),
  });

  drawRadarShape(k, data);
  if (byo) drawByoIdentity(k, data.identity);
  else drawBadges(k, agent);

  k.drawText({
    text: "← → cycle agent    S / Esc  back to park",
    pos: k.vec2(CX, WORLD_H - 10),
    size: 8,
    anchor: "center",
    font: "monospace",
    color: k.Color.fromHex(PALETTE.mid),
  });
}

// Define the "stats" scene. It takes the agent name to display.
export function registerStatsScene(k) {
  k.scene("stats", (agent = "heuristic") => {
    let idx = Math.max(0, AGENT_ORDER.indexOf(agent));
    k.onDraw(() => drawStats(k, AGENT_ORDER[idx]));

    const cycle = (d) => {
      idx = (idx + d + AGENT_ORDER.length) % AGENT_ORDER.length;
    };
    k.onKeyPress("right", () => cycle(1));
    k.onKeyPress("left", () => cycle(-1));
    k.onKeyPress("s", () => k.go("park"));
    k.onKeyPress("escape", () => k.go("park"));
  });
}
