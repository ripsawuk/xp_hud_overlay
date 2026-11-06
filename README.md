# xp_hud_overlay - the operator XP bar mod

A Kronos mod for Call of Duty: Black Ops 7. One bar, at the bottom or the top of the screen, showing the operator
level you are working towards:

```
P5   LVL 7   |   1,200 / 8,000 XP     +20 XP
=========================================================----
```

It works in **Zombies, Multiplayer and Endgame**.

The XP is Kronos's, not this mod's. In Zombies the client's own `zm_local_xp.gsc` awards it and mirrors it into three
dvars (`zm_local_rankxp` / `zm_local_rank` / `zm_local_prestige`); elsewhere the bar reads the game's own
`PROGRESSION` getters, which Kronos points at the same local progression. This mod **only reads and draws**. It never
writes a dvar, a file or a profile value, it has no accrual code, and there is nothing here to tune.

## Install

Copy `mod.json`, `lua\` and `images\` into:

    cod25\kronos\mods\xp_hud_overlay\

then restart the game. `install.cmd` does the copy and prints the hashes on both sides; the user launches.

To remove it, delete that folder.

If an earlier version of this mod was installed, its file was called `zm_hud_post.lua`; `install.cmd` deletes that
stale copy, because two files drawing this bar are two bars. In the console, this mod's lines start `[XpHudOverlay]`, and
a healthy install prints `[XpHudOverlay] v3 loaded: bottom, green`.

**Do not run this beside another copy of the same bar.** `mods\xp_hud` carries its own operator bar in
`lua\zm_hud_post.lua`; both scripts draw the same widget in the same VM and the screen gets two bars. Keep one.
This mod's file is `xp_hud_overlay_post.lua`, so the two are distinguishable in the console (`[XpHudOverlay]` is this one).

## Configure

Everything is at the top of `mod\lua\xp_hud_overlay_post.lua`.

| Setting | Values | Default |
|---|---|---|
| `anchor` | `"bottom"`, `"top"` | `"bottom"` |
| `showText` | `true`, `false` - hides the label and the soft light behind it (the `+N XP` popup has its own switch) | `true` |
| `showTracker` | `true`, `false` - hides only the `+N XP` tracker | `true` |
| `showBar` | `true`, `false` - hides the pill and its fill, leaving the text and the popup | `true` |
| `width` | how long the bar is, 200..1200 - the bar stays centred and the label is centred on it, so the text does not move | `1000` |
| `font` | `"text"` (the engine's own face), `"hud"` (the game's condensed glyph PNGs) | `"text"` |
| `textSize` / `trackerSize` | glyph height in points | `11` / `13` |
| `colour` | `"auto"`, a preset name, or `"custom"` | `"green"` |

`"auto"` follows the HUD theme selected in Kronos: The Giant gives blue, Shadows of Evil gives orange.

Presets: `blue`, `cyan`, `ice`, `gold`, `red`, `green`, `violet` (plus `giant` and `soe`, the two theme colours).

For anything else set `colour = "custom"` and fill in `CUSTOM`:

```lua
local CUSTOM = {
  accent = 0xFF4A4A,   -- the bar fill and the "+N XP" number
  text = nil,          -- the label (nil = keep the automatic colour)
  shadow = nil,        -- the 1 px drop shadow
  glow = nil,          -- the soft light behind the label
}
```

At runtime, from another script (and from the console if the client's console reaches Lua - unproven):
`XpHudOverlay.SetColour("gold")` re-tints the bar on screen immediately, `XpHudOverlay.SetAnchor("top")` moves it to the other edge
immediately, `XpHudOverlay.SetText(false)` hides the label and `XpHudOverlay.SetTracker(false)` hides the `+N XP` popup - all live,
no reload.

## In-game settings

Open the pause menu in a match:

```
RESUME
...
OPERATOR XP HUD        <-- this mod's row
LEAVE GAME
```

That row opens this mod's own page. `XpHudOverlay.Menu()` opens the same page from another script.

The row is added to the **Zombies** pause list (`zmpausemenubuttons`), which is the panel this mod targets; in
Multiplayer and Endgame the pause panel is a different widget, so there use `XpHudOverlay.Menu()` from another script.

The page is a small centred window, not a full-screen menu:

```
+--------------------------------------------------+
| OPERATOR XP HUD                                  |   <- accent rule along the top
| GENERAL      APPEARANCE            L1 / R1       |   <- the tab you are on is in the accent colour
|  ----------                                      |      with a rule under it
|  +----------------------------------------------+
|  | TEXT: ON                                     |
|  | XP POPUP: ON                                 |
|  | POSITION: BOTTOM                             |
|  | COLOUR: GREEN                                |
|  | CLOSE                                        |
|  +----------------------------------------------+
+--------------------------------------------------+
```

`L1` / `R1` move between the tabs, and so does a **click** on one (on keyboard, whatever those actions are bound to).
`Close`, the back button and **Esc** all leave the page.

**General** shows the version and the live XP source, the current level row, how many bars are on screen, and
`Reset the file's settings`.

**Appearance** holds the five things you can change in a match, each applied to the bar already on screen:

| Row | What it does |
|---|---|
| `Bar length` | the bar's length, 200..1200, with left/right on the row. The bar stays centred and the label is centred on it, so the text and `+N XP` never move |
| `Bar: ON` | hides the pill and its fill - the level text and `+N XP` stay on screen |
| `Text: ON` | hides the label and the soft light behind it - the bar and the `+N XP` popup stay |
| `XP popup: ON` | hides only the `+N XP` popup |
| `Position: BOTTOM` | moves the whole widget to the other screen edge |
| `Colour: GREEN` | steps through `auto`, `giant`, `soe`, `blue`, `cyan`, `ice`, `gold`, `red`, `green`, `violet` |

Three switches, so the looks people ask for are combinations: bar + text + popup (default), text only (`Bar: OFF`),
`+N XP` only (`Bar: OFF`, `Text: OFF`).

Nothing is hidden behind a rebuild: the rows and the soft light are built with the bar, so a toggle is a few
`SetAlpha` calls and takes effect as you press the row.

Settings changed in a match last for that session. The file's `CONFIG` is still the thing a restart reads; the
`Reset the file's settings` row puts the session back to what the file says.

## What the row says

- `LVL n   |   into / next XP` inside an ordinary level, with the game's cumulative ladder.
- `P<n>` in front when prestiged; `PM` at Prestige Master.
- `MAX` at the end of level 55 - the client parks the XP at 1,152,999 until you prestige, so 55 still has to be
  finished before it says MAX - and on arrival at Prestige Master 1000, which is the last level.
- `+N XP` beside the label after a kill, when the level's XP actually moved.

## Notes

- Reads the player XP four times a second, and nothing else runs between changes: no per-frame work, no engine calls
  while the values are unchanged.
- In Zombies it uses the dvars; elsewhere the game's progression getters. If neither answers, the bar hides.
- Outside Zombies it hangs off the HUD root and shows only while a map is loaded, so it stays out of the menus.
- If the PNGs are missing the bar falls back to plain shapes; if the HUD font PNGs are missing the text falls back to
  the game's own text element.

## Working on it

`AGENTS.md` is the contract, `PROGRESS.md` the live state and build log, `PLAN.md` the next rows.

    .\verify.cmd                    # replay, must print <n> / <n> and exit 0
    python make_mock.py preview.png # a picture of the layout from the script's own constants
    install.cmd                     # copy mod\ into the client, print hashes
