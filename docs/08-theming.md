# 08 — Theming & the spectator product

**Status:** Living · **Last updated:** 2026-06-03

This doc covers the **creative skin** (roadmap [#4](03-roadmap.md)) — the layer that turns the
benchmark engine into a *theme park*. D-012 deliberately deferred theming until the mechanics were
right ("mechanics first, theme later"); with five scored rides, the four-axis radar, the career, and
the diagnostic viewers all in place, that condition is met. The governing principle is that the skin
is **pure presentation**: it never imports scoring/engine code and never changes a number, so it can
never affect a result.

The watchable diagnostic surfaces (the SVG radar, the career trust-collapse, the leaderboard) live in
[`07-multi-ride.md`](07-multi-ride.md) under "Spectator product" (D-044). This doc adds the **park
skin itself** (D-046).

## The park skin (D-046)

The theme maps the mechanics onto a park vocabulary, applied consistently across the CLI and a web
landing page:

| Mechanic | Skin |
|---|---|
| skill **axis** (D-005) | a **land** (Society Square · Market Midway · Maker's Workshop · Safety Gauntlet) |
| scored **ride** | an **attraction** (with a marquee, tagline, and icon) |
| diagnostic output (radar/career/leaderboard) | a **souvenir** an agent walks out with |

### `src/parkbench/theme.py` — the presentation layer

A tiny, dependency-free module (D-023) holding the theme tables and the renderer:

- **`LANDS`** — one `Land{axis, name, blurb}` per skill axis (D-005).
- **`ATTRACTIONS`** — one `Attraction{ride, marquee, tagline, icon}` per scored ride, **keyed by the
  ride's registry name** so the skin tracks the mechanics.
- **`attraction_for(ride_name)`** — the themed attraction for a ride, with a safe fallback for an
  un-themed ride (so rendering never crashes on a freshly-added ride).
- **`render_park_map(registry=None)`** — builds the ASCII park map from the ride registry + the theme
  tables: the four lands in canonical axis order, each attraction (in registry order) with how to
  ride it (`parkbench <ride> --agent <name>`), and the souvenirs footer. Deterministic, **ASCII-only**
  for terminal portability (the rest of the CLI is ASCII for the same reason — e.g. `+/-` not `±`).

It imports `RIDE_REGISTRY` lazily, so importing the skin never forces the whole ride graph to load.

**The one real invariant** (test-guarded in `tests/test_theme.py`): *every registered ride has a
themed attraction.* This keeps the skin in sync with the mechanics — a new ride can't ship un-themed.

### `parkbench map` — the CLI command

`parkbench map` prints the ASCII park map. It is the cheapest "watchable" overview: a single screen
that shows the whole park (all rides, grouped into lands, with how to run each) and points at the
diagnostic outputs. Pure presentation over the registry — no scoring is run.

### `viewer/park.html` — the web landing page

A third static, **zero-dependency**, no-build page alongside the replay viewer (`index.html`, D-028)
and the diagnostic viewer (`profiles.html`, D-044), under the same constraints (inline CSS/JS, no
framework, no CDN/web-fonts). It is the **themed entrance**: the park marquee, the four lands as
colored cards (per-axis colors shared with `profiles.html`), each attraction with its marquee/tagline
and the command to ride it, and a "souvenir booth" linking to the replay and diagnostic viewers.

Because it is a static page it can't import Python, so its attraction list **mirrors `theme.py`**
(the Python side is the source of truth and is test-guarded against the registry; keep the two in sync
when adding a ride). It has **no `fetch`**, so `file://` works with a plain double-click. Verified
rendering in Chrome (served locally) with **no console errors**.

## What is still skin-deferred

The skin so far is naming + an entrance map + the diagnostic viewers. Roadmap #4's remaining,
deliberately-deferred pieces: richer per-ride theming/art, and **live/served profiles** (a backend
that hosts run results rather than static `--json` files). Both are later #4/#5 work — see
[`03-roadmap.md`](03-roadmap.md). The skin's discipline (presentation-only, never affects a score,
D-012) must hold for all of them.
