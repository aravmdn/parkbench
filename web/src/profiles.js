// profiles.js — where the world's numbers come from.
//
// Two data paths, one shape:
//
//   1. **live**    — `fetch`ed from a running `parkbench serve --profiles` endpoint (D-067), which
//                    serves the *verbatim* `radar --json` / `leaderboard --json` bytes the CLI emits,
//                    plus `/byo` (D-073), which plays a **live** bring-your-own run over the
//                    negotiation wire on demand and returns the completed profile.
//   2. **fixture** — the committed `src/fixtures/*.json` (regenerated verbatim from the versioned CLI
//                    by `parkbench export-profiles`, D-062), so the world still boots with no server.
//
// Because the endpoint serves exactly what the exporter writes, the two are drop-in equivalents: this
// module seeds the store with the fixtures **synchronously** (the world can draw on frame 1, offline,
// with zero network traffic) and then — only if live data was asked for — upgrades entries in place as
// the fetches land. The scenes read the store every frame, so live numbers simply appear.
//
// Presentation only (D-012): this reads JSON and hands it to the scenes. It never computes a score.
//
// ## Choosing the source (page query string)
//
//   (no param)                              → fixtures only; **no network request is ever made**
//   ?profiles=http://127.0.0.1:8080         → live from that base URL
//   ?profiles=1 | on | live | auto | yes    → live from DEFAULT_PROFILES_BASE
//   ?profiles=0 | off | no | fixture(s)     → fixtures only (explicit)
//
// Offline-first is the default on purpose: a plain load of the built app must never depend on — or
// even poke at — a server that probably isn't running. Live data is opt-in, one query param away.
//
// Reachability is decided by a **short** `/health` probe (PROBE_TIMEOUT_MS) so a wrong/dead URL costs
// a moment, never a hang; the world is already on screen from the fixtures while it resolves.

import radarHeuristic from "./fixtures/radar-heuristic.json";
import radarGreedy from "./fixtures/radar-greedy.json";
import radarOptimal from "./fixtures/radar-optimal.json";
import radarRandom from "./fixtures/radar-random.json";
import radarByo from "./fixtures/radar-byo.json";
import leaderboardFixture from "./fixtures/leaderboard.json";

/** Where `parkbench serve --profiles --port 8080` listens by default. */
export const DEFAULT_PROFILES_BASE = "http://127.0.0.1:8080";

/**
 * Reachability probe budget — deliberately short: this decides live-vs-fixture, so a dead URL costs
 * a blink, never a stall. (`main.js` starts the load *after* the first frames so this deadline
 * measures the endpoint, not Kaplay's boot-time main-thread stall.)
 */
const PROBE_TIMEOUT_MS = 2500;
/** Per-payload budget once the endpoint answered `/health` (a leaderboard replays every ride: ~3–4 s). */
const DATA_TIMEOUT_MS = 20000;

export const AGENT_ORDER = ["heuristic", "greedy", "optimal", "random", "acme-bot"];

// `acme-bot` is a bring-your-own third-party agent, not part of the engine's baseline roster, so it
// is not on `/radar` — it has its own route. `/byo` (D-073) *plays a run over the negotiation wire on
// demand* and returns the completed profile, so in live mode the BYO trainer shows a real third-party
// run instead of the committed `radar-byo.json` stand-in.
export const BYO_AGENTS = new Set(["acme-bot"]);

const LIVE_AGENTS = AGENT_ORDER.filter((a) => !BYO_AGENTS.has(a));

/**
 * The *driver* for a live BYO capture: the negotiator the park drives over its own wire to stand in
 * for a third party's HTTP client (the protocol cannot tell them apart — that is the point, D-015).
 * The run is attributed to the trainer's own name, which is passed as `?name=`.
 */
const BYO_DRIVER = "heuristic";

/**
 * The radar store. Seeded with the committed fixtures and **mutated in place** when live data lands,
 * so every consumer (`radar.js`, `gymrun.js`) that reads `RADARS[agent]` at draw time picks the live
 * payload up on the next frame without re-importing anything.
 */
export const RADARS = {
  heuristic: radarHeuristic,
  greedy: radarGreedy,
  optimal: radarOptimal,
  random: radarRandom,
  "acme-bot": radarByo,
};

let leaderboard = leaderboardFixture;

/** The current leaderboard payload (fixture until/unless a live one replaces it). */
export function getLeaderboard() {
  return leaderboard;
}

/**
 * Which source each payload actually came from — read by the scenes to print an honest `live` /
 * `fixture` tag next to the `bench vX.Y.Z` stamp. Mutated in place (never reassigned).
 */
export const SOURCE = {
  mode: "fixture", // "fixture" | "live" | "partial"
  base: null, // resolved endpoint base URL, when live was requested
  requested: false, // did the page ask for live data at all?
  note: "committed fixtures",
  radar: Object.fromEntries(AGENT_ORDER.map((a) => [a, "fixture"])),
  leaderboard: "fixture",
};

/** Source tag for one agent's radar: "live" or "fixture". */
export function radarSource(agent) {
  return SOURCE.radar[agent] || "fixture";
}

/** Source tag for the leaderboard: "live" or "fixture". */
export function leaderboardSource() {
  return SOURCE.leaderboard;
}

const ON = /^(1|on|yes|true|live|auto)$/i;
const OFF = /^(0|off|no|false|fixture|fixtures)$/i;

/**
 * Resolve the profiles base URL from a page query string.
 * Returns `null` when the world should stay on fixtures (and make no request at all).
 */
export function resolveProfilesBase(search) {
  let raw;
  try {
    raw = new URLSearchParams(search || "").get("profiles");
  } catch {
    return null;
  }
  if (raw === null) return null; // no param → offline default
  const value = raw.trim();
  if (value === "" || ON.test(value)) return DEFAULT_PROFILES_BASE;
  if (OFF.test(value)) return null;
  const base = value.replace(/\/+$/, "");
  return /^https?:\/\//i.test(base) ? base : "http://" + base;
}

/** `fetch` + parse JSON under a hard deadline (AbortController) — never hangs the boot. */
async function fetchJson(url, timeoutMs) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, { signal: ctrl.signal, cache: "no-store" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

// Shape guards — a malformed/foreign payload is ignored rather than allowed to break the draw loop.
const isRadar = (d) => !!d && typeof d === "object" && !!d.axes && typeof d.axes === "object";
const isLeaderboard = (d) => !!d && typeof d === "object" && Array.isArray(d.ranking);

async function probe(base) {
  try {
    const health = await fetchJson(base + "/health", PROBE_TIMEOUT_MS);
    return !!health && health.status === "ok";
  } catch {
    return false;
  }
}

function log(message) {
  // Informational only — never an error, so an offline load stays console-clean.
  if (typeof console !== "undefined" && console.info) console.info("[parkbench] " + message);
}

/**
 * Resolve the data source and, when live was asked for and is reachable, upgrade the store in place.
 *
 * Safe to fire-and-forget from `main.js`: it never throws, never blocks the first frame, and leaves
 * every un-fetched entry on its committed fixture.
 */
export async function loadProfiles(search) {
  const base = resolveProfilesBase(
    search !== undefined ? search : typeof window !== "undefined" ? window.location.search : "",
  );
  SOURCE.requested = base !== null;
  SOURCE.base = base;

  if (!base) {
    SOURCE.mode = "fixture";
    SOURCE.note = "committed fixtures - add ?profiles=" + DEFAULT_PROFILES_BASE + " for live data";
    log("data source: fixture (" + SOURCE.note + ")");
    return SOURCE;
  }

  if (!(await probe(base))) {
    SOURCE.mode = "fixture";
    SOURCE.note = "no profiles endpoint at " + base + " - showing committed fixtures";
    log("data source: fixture (" + SOURCE.note + ")");
    return SOURCE;
  }

  const jobs = [
    ...LIVE_AGENTS.map((agent) =>
      fetchJson(base + "/radar?agent=" + encodeURIComponent(agent), DATA_TIMEOUT_MS)
        .then((data) => {
          if (!isRadar(data)) return false;
          RADARS[agent] = data;
          SOURCE.radar[agent] = "live";
          return true;
        })
        .catch(() => false),
    ),
    ...[...BYO_AGENTS].map((agent) =>
      fetchJson(
        base +
          "/byo?agent=" +
          encodeURIComponent(BYO_DRIVER) +
          "&name=" +
          encodeURIComponent(agent),
        DATA_TIMEOUT_MS,
      )
        .then((data) => {
          if (!isRadar(data)) return false;
          RADARS[agent] = data;
          SOURCE.radar[agent] = "live";
          return true;
        })
        .catch(() => false),
    ),
    fetchJson(base + "/leaderboard", DATA_TIMEOUT_MS)
      .then((data) => {
        if (!isLeaderboard(data)) return false;
        leaderboard = data;
        SOURCE.leaderboard = "live";
        return true;
      })
      .catch(() => false),
  ];

  const results = await Promise.all(jobs);
  const ok = results.filter(Boolean).length;
  SOURCE.mode = ok === results.length ? "live" : ok > 0 ? "partial" : "fixture";
  SOURCE.note =
    ok === 0
      ? "endpoint answered but served no usable payload - showing committed fixtures"
      : ok + "/" + results.length + " payloads live from " + base;
  log("data source: " + SOURCE.mode + " (" + SOURCE.note + ")");
  return SOURCE;
}
