// main.js — boot the Parkbench visual world.
//
// The world now has a tile overworld, four labeled lands, gym buildings, the full baseline roster
// walking the park (one palette-swapped trainer per agent), and a stats screen wired to real
// `parkbench radar --json` data (press S — it shows whichever trainer is selected). That data comes
// from `profiles.js`: **live** from a running `parkbench serve --profiles` endpoint when the page
// asks for one (`?profiles=http://127.0.0.1:8080`), otherwise from the committed fixtures. The
// front-end is presentation only — it never scores anything (D-012).

import kaplay from "kaplay";
import { PALETTE, PARK_NAME } from "./theme.js";
import { buildOverworld, WORLD_W, WORLD_H } from "./world.js";
import { buildLands } from "./lands.js";
import { buildGyms } from "./buildings.js";
import { buildProps } from "./props.js";
import { addTrainer } from "./trainer.js";
import { setupGymRuns } from "./gymrun.js";
import { registerStatsScene } from "./radar.js";
import { registerHallOfFameScene } from "./halloffame.js";
import { AGENT_ORDER, SOURCE, loadProfiles } from "./profiles.js";

// The player-controlled trainer (arrow keys + gym entry). The other baselines walk as NPCs.
const PLAYER_AGENT = "heuristic";

// The NPC roster: each baseline gets its own beat of the park to patrol (kept on the crossroads
// paths, clear of the gyms / pond / entrance sign) and its own pace, so the park reads alive. The
// last entry is a **BYO** (bring-your-own) agent — a third-party trainer (`byo: true`) rendered from a
// completed run's JSON alongside the baselines but marked with a "BYO" chip so spectators can tell it
// apart (docs/09-byo-protocol.md). It patrols the upper path arm.
const NPC_TRAINERS = [
  { agent: "random", x: 36, y: 138, speed: 38, route: [[36, 138], [120, 138], [120, 152], [36, 152]] },
  { agent: "greedy", x: 268, y: 152, speed: 44, route: [[268, 152], [184, 152], [184, 138], [268, 138]] },
  { agent: "optimal", x: 152, y: 175, speed: 50, route: [[152, 175], [152, 230], [168, 230], [168, 175]] },
  { agent: "acme-bot", byo: true, x: 160, y: 64, speed: 42, route: [[152, 64], [152, 112], [168, 112], [168, 64]] },
];

// How close (px) the player must walk to an NPC trainer to select it for the stats screen.
const SELECT_RANGE = 20;

const k = kaplay({
  width: WORLD_W,
  height: WORLD_H,
  letterbox: true,
  background: hexToRgb(PALETTE.shadow),
  root: document.getElementById("app"),
  pixelDensity: 1,
  crisp: true,
  logMax: 8,
});

// Convert a "#rrggbb" string into the [r, g, b] array Kaplay's `background` option expects.
function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

// Which agent the S stats screen opens on. Persists across scene hops so world + radar agree.
let selectedAgent = PLAYER_AGENT;

k.scene("park", () => {
  buildOverworld(k);
  buildLands(k);
  const gyms = buildGyms(k);
  buildProps(k);

  const player = addTrainer(k, PLAYER_AGENT, { player: true });
  const npcs = NPC_TRAINERS.map((spec) => addTrainer(k, spec.agent, spec));
  const roster = [player, ...npcs];
  setupGymRuns(k, player, gyms);

  // A small title plate pinned to the top, drawn above the map.
  k.add([
    k.rect(WORLD_W, 18),
    k.pos(0, 0),
    k.color(k.Color.fromHex(PALETTE.ink)),
    k.opacity(0.55),
    k.fixed(),
    k.z(100),
  ]);
  k.add([
    k.text(PARK_NAME, { size: 12, font: "monospace" }),
    k.pos(6, 4),
    k.color(k.Color.fromHex(PALETTE.paper)),
    k.fixed(),
    k.z(101),
  ]);
  const hud = k.add([
    k.text("", { size: 8, font: "monospace" }),
    k.pos(WORLD_W - 6, 6),
    k.anchor("topright"),
    k.color(k.Color.fromHex(PALETTE.light)),
    k.fixed(),
    k.z(101),
  ]);

  // Selection: the trainer the stats screen will show. Highlights its name tag + the HUD. The HUD
  // also carries a small, honest note on **where the numbers come from** — `data: fixture` until the
  // profiles endpoint answers, `data: live` once it has (the fetch is async, so the world boots on
  // fixtures and the tag flips when the payloads land). It rides inside the title plate because the
  // park's greens swallow small text drawn straight onto the grass.
  const hudText = () =>
    "S: stats <" + selectedAgent + ">   H: hall   data: " + SOURCE.mode;
  const select = (agent) => {
    selectedAgent = agent;
    for (const t of roster) t.setSelected(t.agent === agent);
    hud.text = hudText();
  };
  select(selectedAgent);
  k.onUpdate(() => {
    const t = hudText();
    if (hud.text !== t) hud.text = t;
  });

  // Walking the player up to an NPC trainer selects that agent (sticky until re-selected).
  // Only while the user is actually steering — the idle auto-patrol crossing an NPC's beat
  // shouldn't drift the selection on its own.
  const steering = () =>
    k.isKeyDown("left") || k.isKeyDown("right") || k.isKeyDown("up") || k.isKeyDown("down");
  k.onUpdate(() => {
    if (!steering()) return;
    let best = null;
    let bestD = SELECT_RANGE;
    for (const t of npcs) {
      const d = player.pos.dist(t.pos);
      if (d < bestD) {
        best = t;
        bestD = d;
      }
    }
    if (best && best.agent !== selectedAgent) select(best.agent);
  });

  // Tab (or T) cycles the selection through the roster without walking.
  const cycle = () => {
    const i = AGENT_ORDER.indexOf(selectedAgent);
    select(AGENT_ORDER[(i + 1) % AGENT_ORDER.length]);
  };
  k.onKeyPress("tab", cycle);
  k.onKeyPress("t", cycle);

  // The diagnostic screens are reachable from the world.
  k.onKeyPress("s", () => k.go("stats", selectedAgent));
  k.onKeyPress("h", () => k.go("halloffame"));
});

registerStatsScene(k);
registerHallOfFameScene(k);
k.go("park");

// Resolve the data source *after* the world is on screen. `loadProfiles` never throws and never
// blocks the first frame: with no `?profiles=` param it makes no request at all (offline default),
// and when a live endpoint was asked for it probes with a short deadline, then swaps the live
// payloads into the store — the scenes read them on the next frame. Failures silently keep fixtures.
//
// It is deliberately deferred past the first couple of frames: Kaplay's boot (procedural sprite
// generation in `pixels.js`) blocks the main thread long enough on a slow/software-GL machine that a
// probe started *during* it can hit its own deadline before the browser gets to resolve the reply —
// i.e. a healthy endpoint would look unreachable. Starting after the world is drawn keeps the probe
// deadline an honest measure of *the endpoint*, so it can stay short.
const startProfiles = () => loadProfiles().catch(() => {});
if (typeof requestAnimationFrame === "function") {
  requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(startProfiles, 0)));
} else {
  startProfiles();
}
