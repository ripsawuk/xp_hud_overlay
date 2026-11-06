# xp_hud_overlay - contract

A **standalone Kronos mod project**: the operator's level and XP bar for Call of Duty: Black Ops 7, and nothing
else. One script, one mod folder, its own root - open this directory as the workspace and the only subject in it is
this mod.

    mod\lua\xp_hud_overlay_post.lua   the whole mod (the loader only takes `*_post.lua`; the name is the mod's own)
    mod\scripts\xp_hud_overlay_store.gsc   mirrors the settings dvar to kronos\xphudoverlay\settings.json (D38)
    mod\images\*.png            the nine PNGs it draws with
    mod\mod.json                the Kronos manifest

## In scope

- The operator bar: level, the progress inside the level, the prestige / MAX labels, the `+N XP` tracker, the
  colour presets, the anchor, the font, the fallback when a PNG or a glyph is missing.
- Reading the level: Kronos's three Zombies dvars first, the game's `PROGRESSION` getters second.

## Out of scope - do not add it here

- **Weapon XP, weapon level, Gunsmith values, the weapon strip.** That is `mods\xp_hud` / the `zm_weaplvl`
  workstream in `..\..`. This mod must not read, draw or publish anything for it.
- **Camos, challenges, augments, dailies, the shooting-range/ladder tuning.** Separate work, separate mods.
- **Awarding or storing XP.** Kronos's `zm_local_xp.gsc` awards it and the client saves it. The script sets
  exactly one dvar, `xp_hud_overlay_cfg` (its own settings text, D38 - approved by the user 2026-11-06), and no file,
  no `writeconfig`, no XP, no profile value. `verify.py` asserts this on the Lua and the GSC and must keep asserting it.
- **Tuning the XP model** (`challenges.tsv`, `progression.cfg`, the hourly cap). Data / client work, not a mod.

If a change needs one of those, it belongs to the other project - stop and say so rather than widening this one.

## Files

| File | Rule |
|---|---|
| `mod\lua\xp_hud_overlay_post.lua` | The script. `VERSION` is the **release** number and stays `v1.0` until the mod is finished - a build is identified by its size and SHA-256 in `PROGRESS.md`, not by that string (D34). The reload guard still keys on `VERSION`, so a changed file under the same number loads on a **restart**, not on a mod toggle. Its log lines start `[XpHudOverlay]`. |
| `mod\mod.json` | The Kronos manifest. `version` follows the script's `VERSION` major. |
| `mod\images\zmhud_{track,cap,body,tip,glow}.png` | The v12 set; copy all five together. `make_images.py` regenerates them into `mod\images\`. `zmhud_back` / `zmhud_fill` / `zmhud_edge` are retired. |
| `verify.cmd` / `verify.py` | Replay on a stubbed loader. Must print `<n> / <n>` and exit 0. Never weaken an assertion to make a build pass. |
| `make_mock.py` | A picture of the layout from the script's own constants (not a screenshot). |
| `make_index.py` | Writes `release\index_entry.json` (the Kronos Workshop entry, sizes and SHA-256 read from `mod\`) and `release\upload\` (flat names for the GitHub release). Rerun after any change to `mod\`. |
| `install.cmd` | Copies `mod\` to `cod25\kronos\mods\xp_hud_overlay\` and prints both hashes. Refuses while `cod25-cod.exe` runs. |
| `PROGRESS.md` | Live state, build log, next action. |
| `PLAN.md` | The staged plan. One row is `doing`, and that row names the next action. |
| `docs\DECISIONS.md` | Append-only decisions, with the reason and the evidence path. |
| `trace\` | Evidence: console pastes, hashes read back from the game, screenshots. |

## Install

- The user's word, and `cod25-cod.exe` closed. **The user launches the game, always** - from
  `cod25\KronosLauncher.exe`. The launcher may stay open; only the game process blocks an install.
- Read the installed hash back and compare it with the repo copy. If the launcher removes a file, that is a finding,
  not a failure to hide.
- The Kronos mod format allows only `mod.json`, `lua\<name>.lua`, `scripts\<name>.gsc` and `images\<name>.png`
  inside a mod folder. **Nothing else may be copied into `mods\xp_hud_overlay\`** - the docs, the replays and the tools
  stay outside it, which is why the packaged mod lives in `mod\`.

## Evidence

1. No guessing: every claim is a `file:line`, a command and its output, or labelled `UNVERIFIED` with the artifact
   that would settle it.
2. "Compiled", "installed" and "should work" are not results. A hash read back, a log line or a screenshot is.
3. After two failed attempts on the same criterion, stop and record both.
4. `verify.cmd` passing proves logic and argument shapes only. It never proves the game draws it: one launch does.

## Provenance

Built 2026-11-05 from `..\zm_hud\zm_hud_post.lua` v26 (the operator half of `mods\xp_hud`), with the weapon-bar
coupling and the layout knob removed and the geometry closed up - `docs\DECISIONS.md` D1/D2. The parent project is
**read-only** from here. Nothing in this directory is written by it, and this project installs nothing but
`mods\xp_hud_overlay\`.

