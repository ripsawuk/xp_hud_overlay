# DECISIONS - zm_xp_hud

Append-only. Each entry: what was decided, why, and where the evidence is.

---

## D1 - This is its own project and its own mod, extracted from `zm_hud` v26 (2026-11-05)

**Decision.** The operator XP bar becomes a standalone Kronos mod, `mods\zm_xp_hud\`, with its own project root, and
the source of truth for it is `mod\lua\zm_hud_post.lua` in this directory. It is **not** a build product of
`..\zm_hud\`, and the parent project does not write here.

**Why.** The user's direction: *"I want to release a kronos mod with just our progression layer for the operator and
XP tracking related to it, and level and etc... take out all the other code that does not apply here... a clean
folder to work from called zm_xp_hud so I can use that as its own project root."* The operator bar is the one piece
of the parent project that is display-only and needs nothing else: it reads three dvars the Kronos client already
writes. The weapon strip, the Gunsmith values, the camo cards for the challenge feed and the hourly-cap seeder all
live in other files with their own surfaces and their own installs; bundling them into a "progression HUD" release
makes every one of them a dependency of this one.

**What stayed and what went.**

| Kept (the operator layer) | Removed (another workstream, or dead here) |
|---|---|
| The model: level from rank/XP, the level's own band, `P<n>` / `PM`, `MAX` at 55 and at PM 1000 | `CONFIG.layout` and `_G.ZMHUD_LAYOUT` - they placed the weapon bar |
| The three dvars, and the `PROGRESSION` getters as the MP/Endgame fallback | `zm_weaplvl`, `zwxp.gsc`, `xp_tuning`'s `_G.ZMWXP_ONLEVELUP` interface |
| The pill, fill, label, `+N XP` tracker, soft light, five PNGs | The `scripts\` folder and the publisher GSC |
| Presets, `auto` theme colour, `custom`, `SetColour` / `SetAnchor` | Camos, challenges, augments, the XP model / cap seeder |

**Consequence, stated plainly:** there is now a second copy of this bar in the game's `mods\xp_hud`. Two
`*_post.lua` files that draw it are two bars; the reload guard is per file and cannot stop it. `PLAN.md` X4 settles
which one survives, and `install.cmd` warns when the other copy is present.

**Evidence.** `mod\lua\zm_hud_post.lua` (the file), `verify.cmd` -> 192 / 192, and the parent's own record of the
v26 behaviour (`..\zm_hud\STATE.md`, D396/D397).

---

## D2 - The lone bar closes up: the text row moves from 26..44 to 20..38 (2026-11-05)

**Decision.** Fill 4..10 px from the edge inside a pill at 2..12 (unchanged); label 20..38; tracker 20..40; soft
light 10..48. The text row sits 8 px above the pill.

**Why.** v22 moved the row to 26..44 so it cleared the weapon pill that occupied 13..23 and shared one row with the
weapon label. With that bar gone the row would float 14 px above its own pill with an empty slot underneath - the
widget would read as a bar that is missing something. Closing it up keeps the bar where the user last saw it and
drops the whole widget from 54 px to 48 px tall.

**What is not changed.** The bar itself: 1000 px, 6 px fill, the 2 px outline margin, the popup placed from the
label's measured width, the soft light clamped inside the bar. Those were settled across v20-v26 and are not this
project's to revisit without a match screenshot.

**Evidence.** `verify.py` asserts the four bands from the script's constants and the rendered geometry in the
stubbed environment; `python make_mock.py preview.png` draws the result at true scale.

---

## D3 - `VERSION` starts again at `v1` (2026-11-05)

**Decision.** The script's `VERSION` is `v1` and `mod.json`'s `version` is `1`, not `v27`.

**Why.** This is a separate release line with a separate manifest and a separate install folder. The parent's
`vNN` counts builds of a file that was also carrying the weapon bar; inheriting the number would tell a reader
nothing about what changed here. The reload guard only needs the string to differ between two bodies, which it does.

**Evidence.** `mod\lua\zm_hud_post.lua` line 93 (`local VERSION = "v1"`); `mod\mod.json`; `verify.py` pins the load
line `v1 loaded: ...`.

---

## D4 - The file is renamed `zm_xp_hud_post.lua` and the log prefix is `[ZmXpHud]` (2026-11-05, v2)

**Decision.** `mod\lua\zm_hud_post.lua` becomes `mod\lua\zm_xp_hud_post.lua`; the console prefix becomes
`[ZmXpHud]`. `_G.ZMHud` keeps its name.

**Why.** The user's direction: *"Unless we rename the .lua file accordingly as zm_xp_hud and replace all references
inside."* Two reasons beyond the name itself. The mod's folder, manifest and id are `zm_xp_hud`, so a file called
`zm_hud_post.lua` told a reader nothing about which mod it belonged to and it was byte-for-byte the parent's file
name in a different folder. And while the duplicate in `mods\xp_hud` is being settled (`PLAN.md` X4), one console
line pairing `[ZmXpHud]` with `[ZMHud]` settles which script printed it without reading the install folders.

**What was deliberately not renamed.** The global `_G.ZMHud` (the reload guard and the documented `SetColour` /
`SetAnchor` surface: renaming it would make two copies run side by side instead of the newer one silencing the
older) and the five `zmhud_*.png` assets (the material names the game already has registered; `D2`'s geometry and
the image set are not this decision's subject).

**Consequence.** The loader takes any `*_post.lua`, so nothing else moved: same folder, same five PNGs, same
manifest. `install.cmd` deletes a stale `lua\zm_hud_post.lua` from the destination, because a v1 install left there
would draw a second bar beside the renamed file. `AGENTS.md`, `README.md`, `verify.py`, `make_mock.py` and
`install.cmd` were updated with the name; D1-D3 above keep the v1 path because they describe v1.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (the file); `verify.cmd` -> 196 / 196, whose load-line assertion is now
`[ZmXpHud] v2 loaded: ...`; `install.cmd` lines that copy and hash the new name.

---

## D5 - v2 removes dead weight and fixes three things that looked like they worked (2026-11-05)

**Decision.** In the cleanup pass, delete what is never read, delete build-history markers from the source and the
harness, and repair - rather than leave in place - three defects found while reading.

**Removed.**

| Removed | Evidence it was dead |
|---|---|
| `HEIGHT` in `local WIDTH, HEIGHT, CAPW` | never read in the script or in `make_mock.py`; the fill height is `BAR_FAR - BAR_NEAR` |
| `local P = colours()` and `P = C` (twice) | assigned three times, never read |
| `v16`..`v26`, `D355`, `PROGRESS.md` / `STATE.md` markers | comments describing which build introduced a line; the live docs hold that history |
| `png = true` in `nullImage()` | a missing optional PNG made the attach line report "images" |

**Repaired.**

1. **The `+N XP` popup outlived the bar.** `setVisible(false)` cleared the track, label, fill and glow but not the
   tracker rows, so a menu or loading screen could hold a frozen "+20 XP" for its remaining ~1.5 s. It now hides
   both rows and clears `gainShown`, so the next award starts a fresh total.
2. **`ZMHud.SetAnchor` did nothing to a bar already on screen.** It wrote `CFG.anchor` and returned; the comment said
   "takes effect on the next HUD". `reanchor()` now re-places track, glow, label, popup and fill from the same
   constants, so the documented console call mirrors the widget it is looking at.
3. **Two width estimates disagreed.** `styledRow` sets `row.width = #str * size * 0.4`; `labelWidth`'s fallback used
   `0.55`, so when `getElementTextDims` failed the popup jumped to a different column than the row it follows. The
   fallback is now `0.4`.

**Why repair and not remove.** (1) and (2) are behaviour a user would call broken, not knobs nobody uses; deleting
`SetAnchor` would have removed a documented API instead of making it true. (3) is a one-number inconsistency.

**What did not change.** The bar's geometry (`D2`), the model, the ladder, the dvars, the attach strategy, the
timer, the colours and the idle-is-silent property. `python make_mock.py` renders a file byte-identical to v1's
preview (`280BB5A0EB74E01F`), which is the check that the cleanup did not move a pixel.

**Evidence.** `verify.cmd` -> **196 / 196** (192 at v1, plus one assertion for the anchor move and three for the
popup). A mutation run that removes fix 1 and fix 2 fails exactly three assertions (`193 / 196`), so the new checks
bite rather than decorate: `trace\` records the transcript. Hashes: script `9EC96545D89CDB9E...`, manifest
`5F2F842CB35A56A1...`.

---

## D6 - The settings page is a popup built from the pause panel's own widgets (2026-11-05, v3)

**Decision.** The mod's in-game settings are a page of its own, registered with `MenuBuilder.registerType` and opened
with `LUI.FlowManager.RequestPopupMenu(nil, id, true, ctrl, false, {})`. It is entered from a `genericbutton` this
mod appends to the client's ZM pause list (`id == "zmpausemenubuttons"`), and from `ZMHud.Menu()`. Its rows are
`LUI.UIVerticalList` + `MenuBuilder.BuildRegisteredType("genericbutton", ...)`.

**Why that surface and not a hotkey or the game's options menu.**

| Candidate | Why not |
|---|---|
| A hotkey | `bind` is not evidenced in this client, and reading a keypress means wrapping `LUI.UIRoot.ProcessEvent` - a second unverified surface on top of the menu itself. The pause list already navigates with the game's own input |
| A tab in the game's options menu | its tabs and rows come from **script bundles** (`ui\utils\optionsutils.dec.lua:1214-1290` reads `getcurrentmenubundle().tablist`), i.e. game data this mod cannot add to without wrapping `Engine.GetScriptBundle` and forging option entries with setters - far more surface than a page of our own |
| The frontend's `GenericButtonListFlyIn` | it lives under `ui\generated\widgets\frontend\`; whether the match VM has it loaded is unknown. `genericbutton` **is** proven in the match VM because the pause panel builds it there |
| A page drawn into the HUD by our own elements | drawing is proven, input is not: nothing here reads a cursor or a key event |

**The one thing that makes it live.** The label, the tracker and the soft light are now built with **every** bar and
hidden with `SetAlpha` (`lookVisible`), instead of being skipped when `CONFIG.showText = false`. A row's action calls
`repaint(bar)`, so a toggle is a handful of cached `SetAlpha`/`SetRGB` calls on the elements that are already drawing;
no element is created, destroyed or duplicated, and `S.bars` stays at one entry. The cost is three hidden rows when
text is off (they draw nothing at alpha 0); the benefit is that "live" cannot leak or double-draw.

**What it deliberately does not do.**

- **No persistence.** A setting lasts for the session; `Reset the file's settings` returns to `CONFIG`. Writing a
  dvar, a cfg or a file would break D1's display-only contract and `verify.py`'s no-write assertions.
- **No new tab machinery.** The two tabs are two rows that re-open the page with a different row set. `LUI.TabManager`
  is the real tab bar (Kronos wraps it, `LUIFPSCounter.lua:5126-5154`) and is the next step, not this one.
- **No row hiding inside one page.** A tab's rows are not built at all rather than built invisible: an alpha-0 row
  would still be reachable by the list's focus.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`menuRows`, `buildPage`, `openMenu`, `addPauseEntry`, `repaint`);
`ui\generated\widgets\ingame\zm\zmpausemenubuttons.dec.lua:228-310` (the list, its `genericbutton` rows and
`addEventHandler("button_action", ...)`); `ui\generated\widgets\sat\genericbutton.dec.lua:420-525`;
`LUI.FlowManager.RequestPopupMenu` at `ui\flowmanager.dec.lua:172-186`; the shipped precedent
`Warzone Progression 1.0\Assets\Lua\wzprogression_post.lua:1762-1786, 1886-1891, 4448-4452`. Replay **225 / 225**;
`make_mock.py` output still `280BB5A0EB74E01F` (the default look did not move a pixel).

---

## D7 - A hidden row is now built and invisible, not absent (2026-11-05, v3)

**Decision.** `CONFIG.showText = false` and `CONFIG.showTracker = false` no longer remove the elements: the rows exist
on every build and `lookVisible` sets their alpha. The load line still says `text hidden` / `tracker hidden`.

**Why.** D6's live toggle needs something to switch on. Building the rows on demand would mean tearing a bar down
inside the game's HUD tree and rebuilding it on the same parent - an element-removal path (`RemoveElement` /
`closeTree`) this project has never run in a match - for a feature whose whole point is that it must not fail loudly
in the middle of a round.

**What this costs, stated plainly.** With text off, a bar carries three additional invisible rows and the soft light
(the glow is created but at alpha 0). They issue no engine work while idle: the replay still asserts zero setter calls
over 600 idle ticks and one timer re-arm per tick. `verify.py` section 9/10 changed from "no rows at all" to "both
rows built, all at alpha 0", which is the behaviour this decision buys.

**Evidence.** `verify.py` -> **225 / 225**; the two rewritten sections and the new section 15 (a `Text: OFF` row hides
the label, the popup and the glow on the same bar object, `id(label)` unchanged).

---

## D8 - The pause row is hooked three ways, and the build log names which one works (2026-11-05, v4)

**Decision.** v3's single hook - `widget.id == "zmpausemenubuttons"` inside the wrapped
`MenuBuilder.BuildRegisteredType` - stays, and two more are added: the **registered constructor** of
`zmpausemenubuttons` / `mppausemenubuttons` is wrapped (so the row is appended whatever builds the panel, with no id
to match), and **`MenuBuilder.registerType`** is wrapped for those two names (so a type file loaded after this script
is still caught). `CONFIG.debug` logs the first 40 distinct builds as `build <type> id=<id>`.

**Why.** Launch 1 printed every line v3 predicted except the pause row (`trace\2026-11-05-launch-1-v3.md`). The dump
says the panel *is* `zmpausemenubuttons`, registered under that name and built by
`menuBuilder.BuildRegisteredType("zmpausemenubuttons", ...)`
(`ui\generated\widgets\ingame\zm\zmpausemenubuttons.dec.lua:228-236, 555`;
`ui\generated\widgets\sat\globalpanelnavigation.dec.lua:361-367`), and the buttons in the user's screenshot match that
file. So the miss is one of: the id differs in v1.41, the panel is not built through that function in that VM, or the
wrapper is not in the call chain there. The paste cannot distinguish them, and guessing among three would be exactly
the kind of claim this project does not allow. The build log discriminates: **no** `build` lines = third case; build
lines but no pause row = first case; a row = whichever hook reports itself in the brackets.

**Why not just log and wait.** A pure probe costs a launch and answers one question. These hooks cost nothing extra
and may simply work in launch 2; the log then confirms *which* one did, which is what the release documentation
needs anyway.

**Two implementation notes that are easy to get wrong again.**

- **A Lua function cannot carry a field.** `ctor.zmXpWrapped = true` throws "attempt to index a function value". The
  markers live in `WRAPPED` / `MINE` tables keyed by the function, and `MINE` is what stops our own wrapper from
  being wrapped a second time (while a re-registered *original* is wrapped again, deliberately).
- **The row's own button build re-enters the hook.** The constructor hook fires for every `genericbutton` too, so
  `S.addingRow` fences the build of the row itself; without it, a stub or a client that propagates the parent's id
  would recurse.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`PAUSE_TYPES`, `isPauseType`, `appendPauseRow`, `wrapPauseType`,
`installRegisterHook`, the `debug` block in `onBuilt`); `verify.cmd` -> **236 / 236** (+11: the hook arms, the build
path, the register path, the constructor path with no id, a non-pause type left alone, re-registration adding exactly
one row, and the build log being de-duplicated and bounded). A mutation that makes `isPauseType` always false fails
the register and constructor checks.

---

## D9 - The page is a compact popup with a real tab strip (2026-11-05, v5)

**Decision.** The page is a 620x316 window at 650..1270 x 372..688 in 1920x1080 units, centred, with no full-screen
dim: a black backer at 62 %, one accent rule along the top, a 20 pt title, a tab **strip** (`GENERAL`,
`APPEARANCE` - the active tab in the accent colour with a 3 px rule under it, the other grey), a `L1 / R1` hint, and
five 40 px rows in a vertical list. The tabs are no longer rows. `L1` / `R1` switch them through
`AddGamepadEventCallback`; the page's accent re-tints with `Colour`.

**Why.** The user, on the first working build: *"can we make this look more like an actual menu thats tabbed, it
doesnt have to be this big either, it can just be a small popup window maybe?"* The v3/v4 page was a full-height list
of 1040 px rows with two rows pretending to be tabs (`[x] General`), which read as a page, not a menu.

**Why the tabs are drawn rather than a `LUI.TabManager`.** `LUI.TabManager` is the client's real tab bar (Kronos wraps
`SetTabs`, `LUIFPSCounter.lua:5126-5154`), but it is fed by a **data source** (`_tabManagerDataSource`,
`ui\widgets\tabmanager.dec.lua:12-140`), i.e. a data model this mod would have to construct before it could show two
labels. Two `UIStyledText` labels and a rectangle do the same job with the calls the bar already uses
(`SetAnchorsAndPosition`, `SetRGB`, `SetAlpha`) and are checkable in the replay. The tab *switch* is the client's own
input path: `AddGamepadEventCallback("button_shoulderl", ...)`, the same call `loadoutoverview.dec.lua:549-554` uses,
and it handles keyboard binds too (`ui\luielement.dec.lua:280-307` reads `qualifier == "keyboard"` and `uiBind`/`bind`).

**What is deliberately unchanged.** The rows are still `genericbutton`s in a `UIVerticalList`: that is the widget the
pause panel itself builds in this VM, it is what launch 2 proved works, and it brings the client's own focus, sound
and hover art. A hand-drawn row with custom focus handling would be a second input surface for a cosmetic gain.

**One behaviour worth knowing.** A tab switch closes the page and re-opens it one tick later (the engine leaves a
menu asynchronously, and the tab strip is built with the page). That is ~0.5 s, and it is why the tab labels are not
updated in place: they are the only thing that differs between the two builds.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`PANEL_*`, `TAB_*`, `ROW_*`, `pageBox`, `pageText`, `switchTab`,
`S.refreshAccent`); `verify.cmd` -> **241 / 241** (the tabs are labels not rows, the active tab is the accent colour,
the window is inside 600..1400 px, the shoulders are wired, a colour change re-tints the open page);
`python make_mock.py preview-page.png --page` draws the popup at true scale from those constants.

---

## D10 - `Text` and the `+N XP` popup are two switches, not one (2026-11-05, v6)

**Decision.** `CFG.showText` hides the label, its shadow and the soft light. `CFG.showTracker` hides the `+N XP` popup.
Neither implies the other, at load or from the page. With the label off, the popup is placed at the bar's **left
end** (`LABEL_X`) instead of after a label width that no longer exists.

**Why.** The user, from a match: *"I noticed a small bug. Disabling text also disables XP pop up"*. `lookVisible` had
`local gain = text and CFG.showTracker`, a leftover from v1 where one switch controlled the whole text row. Once the
page exposes two independent switches, that line makes the `XP popup` row lie: it reads `ON` and the popup still
disappears.

**What this changes for the file's config.** `showText = false` used to silence the popup as well; now it does not, so
`showText = false, showTracker = true` means "bar and popup, no label". Anyone who wanted silence needs
`showTracker = false` too - stated in `README.md`'s config table.

**Placement, and why left rather than centred.** `placeTracker` follows the label's measured width
(`getElementTextDims`) so the popup sits immediately after the text. With text off that width is a label nobody can
see; centring it in the empty row read as a stray number, so the popup starts at the bar's own left end - the same
column the label would have started in.

**Evidence.** `verify.cmd` -> **244 / 244**: section 9 now asserts that with `showText = false` a kill still raises
`+N XP` at x = -500 and the label stays at alpha 0; section 15 asserts the same through the page's `Text` row, that
`Text: ON` puts the popup back beside the label, and that the `XP popup` row still hides it on its own.

---

## D11 - The bar grows to the right from a fixed left end (2026-11-05, v7)

**Decision.** `BAR_L = -500` is fixed. `CFG.width` (600..1200, step 50) moves only the **right** end: the pill and the
fill are drawn from `BAR_L` to `BAR_L + CFG.width`; the label, the `+N XP` popup and the soft light are placed from
`BAR_L` exactly as before. The page gets a `Bar length` row built from the client's own arrow control, and
`ZMHud.SetWidth(px)` does the same from a script.

**Why left-anchored and not centred.** The user: *"adjustment for maybe a slider of how long the bar is, but the text
has to still be pinned in the same place it was"*. A centred bar moves **both** ends when it changes length, which
drags the label (placed at the left end) and the popup with it. Growing to the right is the only geometry where
"length" and "text stays put" are both true: at the default 1000 the widget is pixel-identical to v6, and every other
length only changes the right-hand 500 px.

**The control.** `GenericArrowButton` + `LUI.AddUIArrowTextButtonLogic` is the client's own left/right option row
(`ui\widgets\arrowbuttonlogic.dec.lua:237-246`; `genericbuttonlistflyin.dec.lua:28-40` builds it the same way), with
`labels` = 600..1200 and `action(value)` = `S.SetWidth(600 + (value - 1) * 50)`. It is patched in through a `pcall`,
because it is a *different* widget family from `genericbutton` and launch 2 only proved `genericbutton` in this VM:
if either the widget or the logic is missing, the row becomes a button that steps the length and wraps, so the
setting is never unreachable.

**What did not change.** `TRACKER_MAX` still caps the popup's left edge at -120, so a long label on a short bar cannot
push it across the middle. `fitGlow` clamps to the new right end instead of the old half-width. The fill keeps its
caps and tip: `setFill` scales by `CFG.width`.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`WIDTH_MIN/MAX/STEP`, `BAR_L`, `CFG.width`, `S.SetWidth`, `arrowRow`,
`nextWidth`, `fitGlow`, `setFill`, `reanchor`); `verify.cmd` -> **253 / 253** (+9: the arrow row is registered with
13 labels and starts on 1000; index 5 shortens the pill to -500..300; the label and popup keep their x on the shorter
bar; the fill scales; index 13 grows it to 1200; `Reset` restores the file's length). `make_mock.py` draws the bar at
`WIDTH` and the page at `PANEL_*`, both parsed from the source, and the bar preview is still
`280BB5A0EB74E01F` - the default look did not move.

**Superseded by D12.** The left-anchored geometry above pinned the text by fixing the left end; the user asked for a
centred bar with a centred label, which pins it for every length without moving the widget off centre. `BAR_L` is
gone; `BAR_L`/`LABEL_X` in this entry describe v7 only.

---

## D12 - The label is centred on the bar, and the gap above the pill is gone (2026-11-05, v8)

**Decision.** The label is centre-aligned in a box the width of the bar (`-CFG.width/2 .. +CFG.width/2`) and the bar
stays centred on the screen. The bands close up: fill 4..10, pill 2..12, **text 14..32**, popup 13..33, soft light
4..42. `+N XP` is placed from the centred label's right edge (`w/2 + 16`) and clamped inside the bar.

**Why.** The user, on launch 2's screenshot: *"can we get rid of the empty space under the text, it was done like this
because of the weapon XP bar but this mod doesnt have it anymore, so we can make use of the space better"*, and
*"by default can the level text (not just the + XP) centered on the bar, as the bar should by default be centered on
the users screen"*.

The 8 px band under the text was D2's `20..38`: v22 of the parent file put the text at 26..44 to clear the weapon
pill, D2 pulled it to 20..38 when that pill left, and the remaining gap was never closed because the label was left
aligned. Moving the text onto the pill and centring it does both asks at once.

**Why this pins the text better than D11.** With the bar centred and the label centred on it, the label's centre is
the screen centre for **every** length - so the text does not move when the slider moves, and the widget does not
drift off centre the way a left-anchored bar did. The popup follows the label's right edge, which is `w/2 + 16` and
also independent of the length.

**What changed for the popup.** `TRACKER_MAX = -120` (which kept the popup left of the middle for the classic HUD's
perk icons) no longer makes sense once the label is centred: the popup now sits right of centre by design. The clamp
is "inside the bar's right end".

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`LABEL_NEAR, LABEL_FAR = 14, 32`, `TRACKER_NEAR, TRACKER_FAR = 13, 33`,
`GLOW_NEAR, GLOW_FAR = 4, 42`, `row(1, ...)`, `fitGlow`'s `cx = 0`, `placeTracker`'s `w/2 + TRACKER_GAP`);
`verify.cmd` -> **253 / 253** (the label's box is the bar's full width at align 1; the bands are 14..32 / 13..33 /
4..42; the glow is centred at 0; the popup is derived from `len x 3.1`; at 800 and 1200 the popup's x is unchanged
while the pill's box moves); `make_mock.py` now renders `CFB462D35A150AFD...` - the default look changed on purpose,
and this hash is the new baseline.

---

## D13 - Mouse tabs, Esc, a bar switch, and a 200 px floor (2026-11-05, v9)

**Decision.** Four separate asks in one build:

1. **The tabs are clickable.** Each tab label gets an invisible `LUI.UIButton` of its own size on top of it:
   `SetFocusable(false)` (so the pad keeps the list's focus), `addEventHandler("button_action", ...)` and
   `registerEventHandler("mousedownleft", ...)`, both calling `switchTabTo(key)`. `switchTabTo` re-opens the page only
   when the tab actually changes, so clicking the tab you are already on does nothing.
2. **Esc / back closes the page**: `menu:AddGamepadEventCallback("button_secondary", closeMenu)` beside the two
   shoulder callbacks. `AddGamepadEventCallback` also delivers keyboard binds (`ui\luielement.dec.lua:280-307`), so
   the key bound to "back" works, not only the pad's circle.
3. **`Bar: ON/OFF`** (`CFG.showBar`, `ZMHud.SetBar`). Off hides the pill and the fill; the label and the popup stay.
   Bar off + text off + popup on is "just the `+N XP`"; bar off alone is "just the level".
4. **The length floor drops to 200 px** (`WIDTH_MIN`), still in steps of 50.

**Why mouse-only for the tabs.** A focusable button outside the vertical list would steal the pad's focus on the way
past. `SetFocusable(false)` keeps the list as the pad's focus chain while the element still receives mouse events -
`SetHandleMouse(true)` is what `LUI.UIButton` already does for itself (`ui\luibutton.dec.lua:901-902`), and
`mousedownleft` on a mouse-enabled element is the pattern the client uses for its sliders
(`ui\widgets\arrowbuttonlogic.dec.lua:320-339`).

**Why `showBar` is not just "alpha 0 on the track".** `setFill` caches by width, so turning the bar back on would
otherwise leave the fill hidden until the next XP change; `S.SetBar` resets `bar.fillW` and repaints, and `setFill`
itself refuses to light up while `CFG.showBar` is false - so an XP change while the bar is off cannot resurrect it.

**At 200 px the popup is clamped.** A 200 px pill cannot hold the centred label plus a 150 px popup box, so the popup
slides inside the bar's right end. That is the one length where the text's x moves, and the replay asserts the clamp
rather than pretending otherwise.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`showBar`, `SetBar`, `WIDTH_MIN = 200`, the hit buttons in `buildPage`,
`switchTabTo`, the `button_secondary` callback); `verify.cmd` -> **264 / 264** (+11: the Appearance list has the bar
switch and seven rows; the arrow row starts at 200 and defaults to index 17; clicking a tab closes and re-opens; Esc
closes; the bar switch hides the pill and the fill and keeps the label, and an XP change cannot bring the fill back;
the 200 px floor and its popup clamp).

---

## D14 - Four tabs, one concern each, and the popup's own colour and position (2026-11-05, v10)

**Decision.** The page is four tabs - **General**, **XP Bar**, **XP Text**, **XP Popup** - each holding only its own
part's switches and a reset that touches only that part. General is the version, `Reset everything` and `Close`.
`S.SetPrestige`, `S.SetTextSize`, `S.SetTextPos`, `S.SetTrackerPos`, `S.SetTrackerColour`, `S.SetLook`,
`S.ResetBar/Text/Popup` are the new surface; `Reset` still puts everything back to `CONFIG`.

**The popup's position rules** (`placeTracker`), which is the one genuinely new piece of geometry:

| text | popup | where it goes |
|---|---|---|
| left | left | left of the text - no room, so it flips to the text's right |
| center | center | left of the text (the text's inner side) |
| right | right | right of the text |
| any | a different slot | that region of the bar: left end, middle, right end - clamped inside |

Every case is clamped to `[-half, half - TRACKER_W]`, so a 200 px bar can never push the popup outside its pill.

**Why "inner side" and not "always left".** The user's four rules as literally written put the popup outside the bar
when the text is already at the edge (`text left + popup left`). "So it stays within the bar constraints" is the
sentence that bounds the other three, so the placement flips when the asked-for side has no room. This is the one
place the build interprets rather than copies, and it is called out for the launch.

**The prestige prefix.** `model()` now returns the level body and the prestige facts separately, and `labelFor()`
adds `P<n>` / `PM` only when `CFG.showPrestige` is on. The prefix is one string, so `Prestige: OFF` hides `PM` too.

**Sizes.** `TEXT_MIN/TEXT_MAX = 11..15`; `styledRow` gained `setSize`/`setAlign` so the live change is a
`SetFontSize`/`SetAlignment` on the element that is already drawing, and the row's band (14..32) does not move. The
PNG-glyph face has no live size (its glyph height is baked into the layout at build); the UI only exposes the engine
face, so that limit is not reachable from the page.

**Colours.** The bar colour keeps driving the fill, the label and the glow (they are a preset, with the label's own
contrast). The popup gained its own: `auto` borrows the bar's accent and shadow, a preset name takes that preset's
accent for the `+N XP` text.

**Not done, and stated as such in `PROGRESS.md`:** the settings do not survive a restart. There is no store this mod
has evidence it may write - `verify.py` bans every setter, the loader has no `io`, and the client's save path belongs
to Kronos. v10 logs the storage globals the VM actually has `(storage: FileStorage (table), ...)` so the next build
can be built on evidence.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`TABS` with four entries, `menuRows` per tab, `placeTracker`,
`popupColours`, `labelFor`, `SetPrestige`/`SetTextSize`/`SetTextPos`/`SetTrackerPos`/`SetTrackerColour`/`SetLook`,
`ResetBar`/`ResetText`/`ResetPopup`, the storage log); `verify.cmd` -> **257 / 257**, section 15 rewritten for the four
tabs (General is three rows; the bar tab's length/colour/look/position/reset; the prestige prefix appearing and
disappearing; size 11..15 and wrapping; three text alignments; the popup's left/right/centre rules against a centred
text; its own colour; the per-tab resets; Reset everything).

---

## D15 - Five bugs from the v10 launch (2026-11-05, v11)

**Decision.** Fix what the launch showed, each with the mechanism the client actually uses:

| Bug | Cause | Fix |
|---|---|---|
| `Reset bar` leaves the length | `CFG.width` was reset, but `GenericArrowButton` keeps its own `_currentValue` and its action feeds `SetWidth` from that value | `syncArrow()` calls the widget's `SetCurrentValue` to the file's length after any reset that changes the width |
| Size / Position do not re-render the text | `SetFontSize` / `SetAlignment` alone do not re-lay a styled row in this client; only `setText` does | `row.setSize`/`row.setAlign` re-set the same string (`row.str = nil; row.set(s, rgb)`) |
| The glow does not follow the text | `fitGlow` centred on `0` (the bar's middle) | it centres on the label's own position for LEFT / CENTER / RIGHT |
| The popup can overlap the label | placement used a measured width that lags a frame after a size change, and nothing checked the spans | `placeTracker` checks the label's span and moves the popup to the free side; size/position changes schedule one deferred repaint so the measurement settles |
| Esc resumes the game | the callback closed our page but the event carried on to the pause menu underneath | the callbacks `return true` - `AddGamepadEventCallback` stops propagating when the callback does (`ui\luielement.dec.lua:328-329`) |

**Clearance.** The text box moved to 18..39 with the text bottom-aligned, so there are 6 px between the text's line
and the pill at 12, and a bigger font grows **upward** instead of into the bar.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`refreshText`, `fitGlow`, `placeTracker`, `syncArrow`, the `return true`
callbacks, the 18..39 band); `verify.cmd` -> **257 / 257** with the bands, the arrow value and the consumed Esc
asserted.

---

## D16 - The popup beside the text, an uncapped glow, and the drop with the bar off (2026-11-05, v12)

**Decision.** Five geometry changes from the v11 launch:

1. **The glow is centred on the text and may bleed past the bar's ends.** The clamp to the pill was what left it
   behind at LEFT/RIGHT: near an edge it pushed the centre inward, so the light sat between the text and the middle.
2. **The popup is always adjacent to the text.** `right` puts it right of the text, `left`/`center` put it left of
   it, and it flips when that side has no room. The per-region placement (`left end`/`middle`/`right end`) is gone -
   it was what left the "lot of empty space" between the popup and the text.
3. **The popup's own text is aligned toward the label** (right-aligned in its box when the box is on the left,
   left-aligned when on the right), so the gap is the 16 px gap rather than 16 px plus an empty 150 px box.
4. **`textDrop()`**: with `Bar: OFF` the text and the popup move 10 px down, onto where the pill was.
5. **`XP Popup > Size`**: `AUTO` follows the XP Text size; 11..15 sets the popup's own.

**Why the drop matters.** The 18..39 band exists to clear the pill. With the pill hidden that clearance is an empty
row under the text - the report was "can we move the text down if it is enabled (and XP Popup) if the bar is
disabled". The drop is applied in `build`, `reanchor`, `placeTracker` and `fitGlow`, so it follows the switch live.

**Popup size.** `repaint` now sets the popup rows to `CFG.trackerAuto and CFG.textSize or CFG.trackerSize`, and
`build` uses the same expression so the first frame is right. `S.SetTrackerSize(nil|"auto"|n)` is the script surface.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`textDrop`, `fitGlow`, `placeTracker`, the `align` argument, `trackerAuto`,
`SetTrackerSize`); `verify.cmd` -> **258 / 258** (the popup's default align is 2 at the text size; LEFT/CENTER sit
`-tw/2 - 16 - 150` with align 2; RIGHT sits `tw/2 + 16` with align 0; the size row steps AUTO -> 11; Reset popup
restores size, colour and position).

---

## D17 - `SetBar` re-places the rows, so the drop is immediate (2026-11-05, v13)

**Decision.** `S.SetBar` calls `reanchor` + `repaint` per bar instead of touching only the fill's alpha.

**Why.** v12 applied `textDrop()` in the four places that *place* the text - `build`, `reanchor`, `placeTracker`,
`fitGlow` - but `SetBar` called none of them. So `Bar: OFF` hid the pill and left the text where it was; it dropped
only when something else re-placed it (a width change, or the next XP change through `placeTracker`), which is exactly
the "randomly decided to pop down later" the user saw, and `Bar: ON` did not bring it back up either.

**Evidence.** `verify.cmd` -> **259 / 259**: toggling `Bar` moves the label and the popup by +10 on the press and
back on the second press (the coordinates are checked against the pre-toggle values, not against the constants).

---

## D18 - Five bar styles drawn inside the existing fill band (2026-11-05, v14)

**Decision.** `Look` cycles **Line -> Divided -> Blocks -> Cat paws -> Dragon**. Every style draws only inside
`BAR_NEAR..BAR_FAR` (4..10) across the same `-width/2 .. width/2`, so the label, the popup and the soft light cannot
move. `S.SetLook(name)` is the script surface; `Reset bar` puts it back to the file's value.

| Style | How it is drawn | Why |
|---|---|---|
| `line` | the existing cap/body/tip gradient | unchanged default |
| `divided` | the same smooth fill, plus 2 px separators over the **whole track** at a 24 px pitch | the MW2 2009 read: the bar looks segmented even where it is empty |
| `blocks` | 20 px segments at a 24 px pitch over the **filled width** | the `\|\|\|\|\|\|` request |
| `paws` | a 20 px paw at a 26 px pitch over the filled width | "for the lolz" |
| `dragon` | a 20 px scale at a 24 px pitch over the filled width | the dragon request |

**Pool, not a rebuild.** Each bar lazily creates up to 56 pooled `UIImage`s; a style draws the first *n* of them and
hides the rest by alpha. At 1200 px the smallest pitch (24) needs 50, which is what the pool is sized for. Switching
style therefore never touches the tree's shape, only materials and positions - and `setVisible(false)` hides the pool
with the pill, so no glyphs are left floating over a menu.

**Assets.** `make_images.py` now emits `zmhud_seg` (20x8), `zmhud_tick` (2x10), `zmhud_paw` (20x8) and `zmhud_scale`
(20x8), all white with an alpha mask so the accent tints them exactly like cap/body/tip. The `make_mock.py --styles`
mode draws the five styles at true scale from those files.

**Quantisation, stated plainly.** A non-line style draws whole glyphs only: the fill's last partial pitch is not drawn,
so progress reads in 24/26 px steps (about 2.5 % of a 1000 px bar). The smooth line remains exact.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`LOOKS`, `LOOK_PITCH`, `LOOK_MAT`, `LOOK_POOL`, `poolImage`, `setFill`,
`S.SetLook`, `lookName`/`nextLook`); `verify.cmd` -> **269 / 269**; `python make_mock.py preview-styles.png --styles`.

---

## D19 - A style IS the bar: the pill goes away for every non-line style (2026-11-05, v15)

**Decision.** For `divided`, `blocks`, `paws` and `dragon` the black track is **hidden** and the style draws its pieces
across the whole width: the first *k* in the accent, the rest at 30 % of it. The plain `line` style keeps the pill.
Styles may use 3..11 (the pill's height) rather than the 4..10 fill band.

**Why.** The user's report on v14: *"you still have a flat black bar behind it ... This currently doesnt look good"*,
with four references - a paw trail, a dragon-scale line, a striped loading bar, and MW2's translucent segmented bar -
none of which sits on a black pill. v14 drew style pieces *on* the pill, which read as decoration over a bar rather
than as the bar.

| Style | Pieces over the full 1000 px | Look |
|---|---|---|
| `divided` | 25 segments at a 40 px pitch, alpha 0.80 | MW2: translucent segments, no pill |
| `blocks` | 100 thin stripes at a 10 px pitch | the loading-bar texture |
| `paws` | 38 paws at a 26 px pitch | the paw trail, straightened |
| `dragon` | 45 scales at a 22 px pitch | the scale line, straightened |

**The trap this created, and the fix.** `lookVisible` re-asserts the track's alpha on every `applyAll`/`repaint`, so
hiding the pill in `setFill` alone was undone a tick later. The track's visibility is now style-aware in **both**
functions: `CFG.showBar and not hidden and CFG.look == "line"`.

**What still holds.** Pieces stay inside the bar's own box and below the text (18..39), so no style can move the label,
the popup or the glow - the replay asserts the label/popup coordinates across every style switch.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`STYLE_NEAR/FAR`, `LOOK_PITCH`, `LOOK_GLYPH`, `LOOK_ALPHA`, `dimAccent`,
`setFill`, `lookVisible`); `verify.cmd` -> **269 / 269** (no pill under any style, 25/100/38/45 pieces, the split
between accent and dim at 50 % fill, and Line restoring the pill and the pieces); `make_mock.py --styles`.

---

## D20 - Style art at its own aspect, MW2 slanted and translucent (2026-11-05, v16)

**Decision.** Each style keeps its art at the size it was drawn (no squashing into the 6 px fill band) and gets its own
vertical band inside the bar:

| Style | Glyph | Band | Pitch | Filled alpha | Empty alpha |
|---|---|---|---|---|---|
| divided | 44x12 slanted parallelogram | 1..13 | 48 | 0.55 | 0.22 |
| blocks | 4x8 stripe | 3..11 | 10 | 1.0 | 1.0 (dim tint) |
| paws | 16x16 paw, rotated 45 degrees | 1..17 | 20 | 1.0 | 0.22 |
| dragon | 16x16 scale, pointed diamond | 1..17 | 15 | 1.0 | 0.22 |

**Why.** The user's report on v15: the MW2 bar "looks nothing like I said", it is "slashed in a slanted way sort of
like /-----/-----/", and "the filled section also has to be seethrough"; the cat paw is "literally nothing like a cat
paw - use my image, and rotate the paws about 45 degrees"; "same as above for the dragon"; and "the images for the
bars should just be cropped too, instead of changed size". v15's paw was a 20x8 shape squashed into the fill band, so
it read as a blob, and the MW2 segment was a rounded rectangle rather than a parallelogram.

**Cropping, not scaling.** A piece is always placed at its drawn size: on a shorter bar the count drops, it is never
stretched. The last partial pitch is skipped rather than squeezed (the line style is still exact).

**Assets.** `zmhud_seg` is now a 44x12 parallelogram with 6 px slanted ends, `zmhud_stripe` is its own 4x8 stripe (so
`blocks` is unaffected by the MW2 shape), `zmhud_paw` and `zmhud_scale` are 16x16 at their own aspect, the paw rotated
-45 degrees.

**Evidence.** `make_images.py`; `mod\lua\zm_xp_hud_post.lua` (`LOOK_NEAR/FAR`, `LOOK_EMPTY_ALPHA`, `setFill`);
`verify.cmd` -> **270 / 270** (20 slanted segments at alpha 0.55/0.22, 100 stripes, 50 paws, 66 scales, no pill under
any style); `make_mock.py --styles`.

---

## D21 - MW2 at the pill's height, the user's paw and a scale link (2026-11-05, v17)

**Decision.** Three changes from the user's own references (`cat-paw-trail.svg`, `dragon-tail.svg`):

| Style | Art | Band | Pitch |
|---|---|---|---|
| divided | 44x10 slanted parallelogram, the pill's exact height | 1..11 (10 tall, same as the pill at 2..12) | 48 |
| paws | 16x16 paw: the pad blob **and four toes**, at the SVG's proportions | 1..17 | 22 |
| dragon | 16x16 link: pointed ring plus a lattice cross, from the tail's chain | 1..17 | 15 |

**Why.** The user's report: the MW2 bar was *smaller than the other bars by default* - the segments sat at 1..13 with
a 12 px glyph while the plain pill is 10 px, and the gaps made it read thinner still; the cat paw was *literally
nothing like a cat paw* with three toes; and the dragon needed the same treatment as the paw - one element from their
art, repeated.

**The size ceiling, stated plainly.** The text row starts at 18 and the bar's own edge is at 2, so a style glyph can be
at most 16 px tall without touching the label. That is why the paw is 16x16 and not larger: a recognisable paw at this
size is pad + four toes, which is what the SVG shows at its own scale.

**Cropping, not scaling.** Pieces are placed at their drawn size; a shorter bar fits fewer of them and never stretches
one. The last partial pitch is skipped (the `line` style remains exact).

**Evidence.** `make_images.py` (`paw`, `scale`, `seg`); `mod\lua\zm_xp_hud_post.lua` (`LOOK_PITCH`, `LOOK_GLYPH`,
`LOOK_NEAR/FAR`); `verify.cmd` -> **270 / 270** (20 segments at alpha 0.55/0.22, 100 stripes, 45 paws, 66 scales, no
pill under any style); `make_mock.py --styles`.

---

## D22 - The user's SVG is the bar: strips, stencil-cropped at the progress (2026-11-05, v18)

**Decision.** `Cat paws` and `Dragon` are no longer built from a repeated single glyph. Each is **one wide strip** -
`zmhud_pawstrip.png` (678x120, rendered from `cat-paw-trail.svg`) and `zmhud_dragonstrip.png` (1400x240, from
`dragon-tail.svg`) - drawn across the whole bar:

- a **dim** copy (30 % of the accent) spans the full width, so the shape is always visible;
- a **bright** copy sits inside a `setUseStencil(true)` element whose width is the progress, so the art is **cropped**
  at the progress point rather than squeezed or covered by a plate.

**Why.** The user's correction: *"The SVG I gave you IS The bar, you should not interpret it to be your own ... Use my
designs for the bar not whatever you did here"*. v17 read the SVGs as a palette - one paw, one scale, repeated - which
is not their design. v18 renders their artwork and uses it whole.

**The renderer.** There is no SVG library on this machine (`cairosvg`, `svglib`, `skia` all absent), so
`make_images.py` carries a small rasteriser: groups with `translate`/`rotate`, absolute `M/L/C/H/V/Z` paths with cubic
sampling, and rotated ellipses (transformed through the group, which is what the paw toes need). Both files render
correctly from it.

**The one honest limitation.** The bar is ~16 px tall (the text row starts at 18). The paw trail's paws are 30 px in a
120 px canvas, i.e. a quarter of its height, so at bar height a paw is ~4 px: the trail's composition is exact, the
paws are small. Enlarging them means either a taller band, which collides with the label, or moving the label, which
this mod must not do. The strip is drawn at the bar's size and **cropped**, never stretched.

**Evidence.** `make_images.py` (`svg_mask`, `_path_points`, `_transform`); `mod\lua\zm_xp_hud_post.lua`
(`LOOK_STRIP`, the stencil branch in `setFill`); `verify.cmd` -> **271 / 271** (one strip per style, its box
`-500..500`, the dim tint `0x174D21`, a stencil element holding the bright copy); `make_mock.py --styles` composites
the same two layers.

---

## D23 - Strips are never scaled; the pill goes translucent (2026-11-05, v19)

**Decision.** Two changes:

1. **A style strip is drawn 1:1** - tiles of the source art at the bar's height, under **two stencils**: one the width
   of the bar (the dim copy) and one the width of the progress (the bright copy). Nothing is stretched; a bar narrower
   than the art simply shows fewer tiles.
2. **The plain pill is translucent** (`TRACK_ALPHA = 0.55`): the user's note that a flat black bar is the one thing
   none of the other styles have.

**Why.** *"Still kind of wrong. I cant even make out the cat paws. Add more cat paws and dont skew images of the bar I
provided ... Same for the dragon one"* and *"Can we also change up the default to have the same opacity as loading bar,
but keep the pill shape for default"*.

**The size question, answered with numbers.** The strip box is **1200 x 16 px** (1200 = the widest bar the slider
allows, 16 = the band from y 1 to y 17; the label starts at 18, so 16 is the ceiling). Art authored at that size is
drawn 1:1 and cropped at the progress, with no scaling at all:
- paws: paw height 12-14 px, pitch 24-26 px, about 45-50 paws across;
- dragon: the tail body about 14 px thick, scales 3-5 px.

Until that art exists the code tiles the supplied SVGs at their own aspect (`LOOK_STRIP_ASPECT` = 678/120 and
1400/240), which is why the paws are small - the trail's paws are a quarter of its 120 px height, so at a 16 px bar a
paw is 4 px.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`TRACK_ALPHA`, `LOOK_STRIP_ASPECT`, the two-stencil branch in
`setFill`); `verify.cmd` -> **272 / 272** (tiles 90/93 px wide, two stencils, the dim tint, the pill at 0.55 rather
than 1).

---

## D24 - The user's own strips, 1200x16, one tile each (2026-11-05, v20)

**Decision.** `assets/zmhud_pawstrip.png` and `assets/zmhud_dragonstrip.png` (the user's art, supplied at 4800x64) are
downsampled by `make_images.py` to exactly **1200 x 16**, forced to white, and shipped as `mod/images/zmhud_*strip.png`.
Their aspect is `1200/16 = 75`, so the strip branch lays **one tile**: at the widest bar (1200) it is shown 1:1, at any
shorter bar it is cropped at the bar's right edge and at the progress by the two stencils.

**Why.** The user authored the art to the size asked for (4x for sharpness) and said *"Ive added both pictures"*. The
previous build tiled the SVGs at their own 678x120 / 1400x240 aspect, which made every paw ~4 px - their report was
*"I cant even make out the cat paws"*.

**What is now fixed by construction.**

- **No scaling, ever**: a 1200 px tile is either fully shown (bar at 1200) or cropped at the bar's edge / progress.
  Only the plain `line` style stretches its fill, which is what it is for.
- **The art is the bar**: no pill, no plate, no black behind either style.

**Evidence.** `make_images.py` (`strips()`); `mod\lua\zm_xp_hud_post.lua` (`LOOK_STRIP_ASPECT = 1200/16`, the
two-stencil branch); `verify.cmd` -> **272 / 272** (one 1200 px tile, two stencils, the dim tint); the installed
`mods\zm_xp_hud\images\` holds both 1200x16 files; `make_mock.py --styles` draws them 1:1.

---

## D25 - The plain pill takes the dim accent, and a silent failure is silenced no more (2026-11-05, v21)

**Decision.** The `line` style's pill is tinted with `dimAccent(accent)` - 30 % of the bar's own colour - and drawn
opaque, instead of the near-black PNG it shipped with. All five styles therefore read the same way: accent for earned,
30 % accent for not earned.

**Why.** *"we have the other Looks using a opaque base colour instead of black. Can that be the same for default too"*,
and v19's translucent pill was a different answer to the same complaint.

**The bug this uncovered.** `dimAccent` was declared **after** `applyColours`, which uses it for the pill. In Lua that
made it a global lookup - nil at call time - so `applyColours` threw on its first line and the *colour* half of every
repaint was silently skipped: `SetColour("violet")` logged violet and left the bar green. `pcall(repaint, bar)` hid it
for two builds. Fixed by declaring `dimAccent` above its users, and `S.SetColour`/`SetText`/... now call `repaintBar`,
which logs `repaint error: <message>` once, so the next such break shows up in the console instead of in the user's
eyes.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`dimAccent` moved above `applyColours`, the `setRGB(bar.track, ...)`, the
opaque track alpha, `repaintBar`); `verify.cmd` -> **272 / 272**, whose colour assertions had been failing on that
nil until the move; `make_mock.py --styles` tints the pill the same way.

---

## D26 - The client speaks Lua 5.1; the replay speaks 5.5, so the source is checked for 5.3 syntax (2026-11-05, v22)

**Decision.** No Lua 5.3+ syntax in the script: bitwise operators, `//`, and `goto` are rejected by `verify.py` on the
source text, because the replay runtime cannot reject them for us.

**Why.** v21 shipped `dimAccent` using `>>` and `&`. The replay passed (lupa runs Lua 5.5, where they exist) and the
client refused the whole file:

    [Lua Error] ...\zm_xp_hud_post.lua:748: unexpected symbol near '>'

so the mod did not load at all. The arithmetic form is equivalent and works in 5.1:

    local r = math.floor((math.floor(rgb / 65536) % 256) * 0.30 + 0.5)

**The harness gap, closed.** `verify.py` strips string literals and comments, then fails on `>>`, `<<`, `//`, a lone
`&`, a lone `|`, `~` other than `~=`, and `goto`. Proved to bite: putting `>>` back fails
`Lua 5.1 syntax: no bitwise shift (>>)` (278 / 279).

**What else this means.** The replay's Lua being newer than the client's is a standing risk: anything 5.2-5.5 specific
(`goto`, `//`, integer division, bitwise ops, `table.pack`, `string.pack`, `<close>`) would pass the replay and break
in the game. The operator check is the one that has actually bitten; the rest are unverified assumptions about which
Lua the client embeds, recorded here rather than pretended away.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`dimAccent`); `verify.py` (the "Lua 5.1 syntax" block);
`verify.cmd` -> **279 / 279**; the client error from the v21 launch is quoted above.

---

## D27 - A stencil child needs a height, and the fill cache needs the colour (2026-11-05, v23/v24)

Two defects, both found by the user in a live match, both invisible to the replay until the replay was taught to see
them.

**1. The strip styles drew nothing (v22, v23).** `Cats` and `DraGON` are the user's own 1200x16 art, drawn 1:1 under
two stencils. v22 placed the art with `place()`, which anchors to the **screen** edge; inside a stencil those
coordinates are meaningless and the elements had no height at all. v23 "fixed" it with

    o.el:SetAnchorsAndPosition(0, 1, 0, 1, x, x + tile, 0, 0)

which is still **zero height**: `ui\luielement.dec.lua:456` computes the second edge as
`(1 - anchor) * parentSize + offset`, so `top = 0, bottom = 0` with `topAnchor = 0, bottomAnchor = 1` is a 0 px box.
The idiom the client itself uses is the glyph row's (`zm_xp_hud_post.lua`, `glyphRow`):

    SetAnchorsAndPosition(0, 1, 0, 1, x, x + gw, 0, h)      -- h = the row's own height

v24 also stops pooling the art: pooling put elements created inside `bar.clip` back into the top-level pool on the
next style change (they would have stayed clipped and parent-relative). The strip is now **one element per stencil**,
created in `build()` before the rows so the text always draws over it, and hidden by alpha when the style is not a
strip.

**2. A colour change did not reach a style's pieces.** `setFill` opened with

    if w == bar.fillW and bar.look == CFG.look then return end

Width and style, but not the colour. `SetColour` re-tinted the pill, the label, the popup and the glow; the pieces a
style draws were only painted inside `setFill`, so they kept the old colour until the XP moved far enough to change
the width - the user's report, exactly: *"Changing colours doesnt change the colour of the bar"*, with `COLOUR: BLUE`
on the row and a green `BLOCKS` bar in the screenshot. The key now includes the accent:

    if w == bar.fillW and bar.look == CFG.look and bar.tint == C.accent then return end

**Why the replay missed both.** It stubbed `SetAnchorsAndPosition` and recorded the arguments, but never asserted the
second edge of a stencil child; and it asserted the colour row against the *pill's* cap, which `applyColours` always
tinted - so the one path that worked was the one under test. Both are now pinned:

- `each strip copy fills its stencil's height (16 px), not zero` - `geo(i)[:4] == [0, 1, 0, 1]` and
  `geo(i)[6:8] == [0, 16]`;
- `a colour change re-tints a style's pieces on the same press, with no XP change` - the `BLOCKS` pieces are
  `{0xB07CFF, 0x35254D}` (violet and its 30 %) immediately after `SetColour("violet")`, no `STEP` between.

Both were proved to bite by putting the old code back: `FAIL a colour change re-tints a style's pieces ... ['0x174d21',
'0x4cff6e']` (281 / 282) and `FAIL each strip copy fills its stencil's height (16 px), not zero [[0, 1, 0, 1, 0, 1200,
0, 0], ...]` (281 / 282).

**Also in this build.** The two display names are the user's, verbatim and case-sensitive: `Cats` and `DraGON`
(`LOOKS`); the Look row shows them as written instead of shouting them through `string.upper`.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`build` creating `clip`/`clipFill`/`stripDim`/`stripBright`, the strip
branch of `setFill`, the `bar.tint` cache key, `LOOKS`); `verify.cmd` -> **282 / 282**; the mutation runs above;
the installed `mods\zm_xp_hud\lua\zm_xp_hud_post.lua` = `F1CFCEB43BF5D0DEC547E5A4E58169979F06C8CA40BFEEC8FCAEAE8BE01D6F1D`
(86,439 B, `VERSION = "v24"`).

---

## D28 - `Divided` and `Blocks` shrink into the fill's band (2026-11-05, v25)

**Decision.** Both styled bars that are made of pieces now sit in the *fill's* height rather than the pill's:

| Style | Band (distance from the edge) | Height | Piece | Pitch |
|---|---|---|---|---|
| `Divided` | 1..11 -> **4..10** | 10 px -> **6 px** | 44 px, slanted | 48 px (unchanged) |
| `Blocks` | 3..11 -> **5..10** | 8 px -> **5 px** | 4 px | 10 px -> **7 px** |

`Line`, `Cats` and `DraGON` are untouched.

**Why.** *"Lets make the bars less height than they currently are, but keep the division aspect. Same for the loading
ones, reduce the space between them and make them less high. The others can be kept the same."*

**Keeping the division aspect.** The slab is a PNG stained with the accent, so it is the mask that carries the lean,
not the placement. `zmhud_seg.png` was 44x10 with a 6 px skew (31 deg); it is regenerated at **44x6 with a 4 px skew**
(33.7 deg) - the same lean, at two thirds the height. A 44x10 mask squeezed into a 6 px box would have flattened it to
45 deg of squash and read as a different shape. `zmhud_stripe.png` is a plain rectangle, so 4x8 -> 4x5 costs nothing
but keeps the file honest about the box it fills.

**What pins it.** Two new assertions in the replay, both proved to bite by putting the old numbers back:

- `DIVIDED is the fill's own height now: 6 px (4..10)` - `FAIL ... [1, 11]`;
- `BLOCKS is 5 px tall on the fill's baseline (5..10), and its gap is 3 px not 6` - `FAIL ... ([3, 11], 10.0)`, plus
  the count check moving 100 -> 142 pieces at the new pitch (`FAIL BLOCKS is the whole bar ... 100`).

They read the element's own band through `place`'s negation for a bottom-anchored bar (the `band()` helper in
`verify.py`), so a bar at the top edge measures the same.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`LOOK_PITCH` / `LOOK_GLYPH` / `LOOK_NEAR` / `LOOK_FAR`);
`make_images.py` (`seg()` 44x6 skew 4, `stripe()` 4x5); `verify.cmd` -> **284 / 284**; `make_mock.py --styles` draws the
new bands; montage of the five styles in the chat for this build.

---

## D29 - Settings persist through the client's own `FileStorage`, and nothing else (2026-11-05, v26)

**Decision.** The bar's settings are saved after every change to one file, `zm_xp_hud_config`, through the API the
client's own HUD editor uses for its config:

    FileStorage.writeallfilecontent( controller, "zm_xp_hud_config", text )
    FileStorage.readallfilecontent ( controller, "zm_xp_hud_config" ) -> text

**The two members are named.** A previous launch printed FileStorage's contents as two xhash keys:

    FileStorage members: xhash: #x0193258999f89095e:function xhash: #x0469f6d351feeeaab:function

Both are **FNV-1a-64** of the two names in the decompiled client: `0x0193258999f89095e` is `writeallfilecontent` and
`0x0469f6d351feeeaab` is `readallfilecontent` (the client's log pads one leading zero; the values are 16 digits). An
8 MB `PNDB` name table (`k's discord\hashes-solved-bo7 (3).cdb`) contains `readallfilecontent` as a plain string, which
is how the candidate spelling was found; the hash match is what settles it. `storeFn` therefore looks a member up by
plain name first and by `xhash(name)` second - the same dual lookup a working third-party mod uses
(`Assets\Lua\csm_mayhem_relic_post.lua:9-13`). `verify.py` recomputes FNV-1a-64 of the two names in the source and
fails unless they are those two keys, so renaming either member cannot pass the replay.

**Why that store.** It is the only one in this VM that is a *settings* store rather than a game-state one, and it is
already shipping: `ui\utils\hudeditorutils.dec.lua:2719` reads `hud_editor_config` on boot and `:2875` writes it on
save, i.e. the client persists UI configuration to exactly this API and survives restarts doing it. A dvar is not
archived for a name the game does not know, `Engine.ExecNow` is an exec, and the profile is the player's progression -
all three are things this mod has no business touching.

**The shape of the write.** `key=value` lines, fixed key set, every value validated before it is used:
`anchor, text, tracker, bar, prestige, colour, look, width, textpos, textsize, trackerpos, trackersize, trackerauto,
trackercolour`. A value that is not one of the allowed ones is dropped; a line that does not parse is dropped; a
damaged file leaves the CONFIG defaults alone instead of half-applying (tested). No path, no extension, no JSON
dependency, no free text.

**The call, when the dump is not certain.** The decompiler mangles the first argument of the client's own call site
(`local f0_local0 = f0_local0()`), so the mod tries `(0, name)` - controller index, the order the client passes - and
falls back to `(name)`. A write counts as saved only when reading the name back returns the text that was written
(compared with trailing whitespace trimmed), so "it worked" is a read, not an assumption. The console says
`settings: saved to zm_xp_hud_config (N bytes)` or `settings: the zm_xp_hud_config write did not read back`.

**What this does not change.** No XP is read, awarded or stored; no profile value, no dvar, no exec, no path. The store
is read once at load (again from the tick if `FileStorage` is not up that early) and written by one wrapper that every
setter and reset returns through, so a setter added later cannot forget it. `verify.py` still fails on `SetDvar`,
`setdvar`, `ExecNow`, `Engine.`, `io.open`, `writeconfig` and `exec `, and now also pins the store: exactly two
`FileStorage` members, one constant name, no path separators.

**Tests (12 new, 284 -> 296).** A press writes the fixed key set through the `(controller, name, text)` shape; a fresh
VM with that file comes up with the saved colour/style/length and logs how many keys it read; a damaged file changes
nothing; a VM with no `FileStorage` still draws the bar and says so once. Mutations proved two of them: removing the
save hook fails 3 assertions, and dropping the load-time read fails `a restart adopts the saved settings`.

**Open, needs the launch.** Whether the *call* works from a mod's VM - the first argument of the client's own call
site is mangled by the decompiler, so the mod tries `(0, name)` and then `(name)`, and only calls a write saved when
the name reads back - and where the file lands. The console lines are the evidence; `trace\` gets them.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`STORE`, `storeFn`, `readStore`, `applyStored`, `persist`, the setter
wrapper); `verify.py` section 17; `verify.cmd` -> **296 / 296**.

---

## D30 - The popup is pinned right of the text, and the halo moves with the row (2026-11-05, v27)

**Decision 1 - no popup position setting.** `XP Popup` loses its `Position` row. `+N XP` always starts `TRACKER_GAP`
(16 px) after the level text's own measured end, left-aligned in its 150 px box. With the text at the bar's right end
the popup runs past the bar's edge rather than jumping to the other side of the label - the only bound is the screen.
With the text off it parks at the bar's left end, as before.

**Why.** *"XP text and XP popup relationship still doesnt work. Lets just leave it pinned to the right of the XP text at
all times, remove the setting to change the position of the XP popup."* The old rule had four cases (the popup's own
position crossed with the text's, with a flip when the bar's edge was in the way), and in a match it read as random.
One rule cannot disagree with itself.

**What went with it.** `CFG.trackerPos`, `CONFIG.trackerPos`, `S.SetTrackerPos`, the `trackerpos` store key, the row,
and the reset lines for it. A settings file from v26 with `trackerpos=...` in it is read with that key ignored (an
unknown key is not an error - `applyStored` simply does not count it).

**Decision 2 - the halo is part of the text row.** `fitGlow` cached on the light's width and centre, and `reanchor`
placed it at `GLOW_NEAR..GLOW_FAR` without the row's drop. So `Bar: OFF` moved the text and the popup down 10 px and
left the soft light where the text used to be - the purple band above the text in the user's screenshot. Now:

- `fitGlow`'s cache key includes `textDrop()`, and it places the light at `GLOW_NEAR - drop .. GLOW_FAR - drop`;
- `reanchor` places the light with the same drop, so a re-place cannot put it back where it was.

Either fix alone is enough to move it, which is why the replay only fails when **both** are reverted:
`FAIL and the halo behind the text moves with it, on the same press ([-44, -8], [-44, -8])` (297 / 298).

**Tests.** `Bar OFF` now asserts the halo moves 10 px with the label and the popup, and `Bar ON` asserts it comes back
with them; the popup is asserted pinned at three text positions (left, centre, right), and the XP Popup tab is asserted
to have exactly four rows.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (`placeTracker`, `fitGlow`, `reanchor`, the `XP Popup` rows);
`verify.py` sections 7 and 15; `verify.cmd` -> **298 / 298**.

---

## D31 - v1.0: one release number, and the discovery scaffolding out of the file (2026-11-05)

**Decision 1 - the version is `v1.0`.** The script's `VERSION`, `mod.json`'s `version` and the load line are `v1.0`
from here. Build numbers (`v1`..`v27`) were the development sequence; the mod is now one release with a version a user
can read.

**Decision 2 - the code is a shipped file, not a workbench.** Removed from `zm_xp_hud_post.lua`:

- `CONFIG.debug` and its two users: the bounded `build <type> id=<id>` log (it existed to find the pause hook) and the
  `storage:` / `FileStorage members:` probe at the end of the file. The hook now reports itself with one line,
  `pause-menu row hooked (n path(s))`, or says the VM has no `MenuBuilder`.
- The dead style art: `zmhud_paw.png`, `zmhud_scale.png` and `zmhud_tick.png` are gone from `mod\images` and from
  `make_images.py`; the `paws` / `dragon` entries in `LOOK_PITCH`, `LOOK_GLYPH`, `LOOK_ALPHA`, `LOOK_EMPTY_ALPHA` and
  `LOOK_MAT` went with them. Those two styles are strips, drawn by their own branch, and never read the glyph tables.
- Every comment that told the project's story instead of the code's: decision ids, "the user's", "used to", "shipped",
  "a previous launch", "for two builds". The mechanism comments stayed (Lua 5.1 arithmetic, xhash member lookup, the
  stencil crop, the fill band, the ladder, the drop).

`S.seen` and `S.loggedN` - the fields that only served the build log - are gone with it.

**Why.** *"Lets change the version to v1.0 now across the board to this overall hud mod, and clear up any testing or
unwanted commentary inside the code for this mod."* A shipped file that prints widget ids and storage internals is a
debugging tool, and a comment that explains what the file used to do is a claim about a file that no longer exists.

**What this costs.** The build log was the only way to tell "no widget reached the hook" from "the widget did, under
another id" without a debugger. If the pause row ever goes missing again, that line has to be re-added - the decision
record above says exactly what it printed, so re-adding it is a copy, not an investigation.

**Tests.** `verify.py` lost the two build-log assertions and the `CONFIG.debug` check, and now also fails if
`S.seen`, `loggedN` or `CFG.debug` come back. The image list is the nine files the mod actually draws. The replay is
**295 / 295**.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (90,557 B, `B7CED61F850D0450`); `mod\mod.json` (`version: "1.0"`);
`mod\images\` (9 files); `make_images.py`; `verify.cmd` -> **295 / 295**.

---

## D32 - `CONFIG` and `CUSTOM` are gone: the page is the settings screen (2026-11-05, v1.1)

**Decision.** The 55-line `CONFIG` block and the `CUSTOM` colour table are replaced by one `DEFAULTS` table: the
starting values, one short line each, with the tab each one lives on. `makeConfig(DEFAULTS)` validates them once into
the live `CFG`, and every Reset row calls the same function, so "reset" means the same numbers as a fresh install.

**Why.** *"Lets also remove the configuration settings from the lua as we do that in game now, there is excessive
commentary related to that."* Every key in that block had a row in the page and a line of explanation in the file, in
two places at once: a comment nobody reads and a setting nobody edits. The page sets the value, the settings file
remembers it, and the table is only what a first launch starts from.

**What went with it.**

- `CUSTOM` and the `"custom"` colour mode. It was configurable only from the file, had no row, and its four values
  defaulted to nil - an unreachable branch behind a `colour = "custom"` that no page could produce. `SetColour` and the
  store reader now accept `"auto"` or a preset name and nothing else.
- `CONFIG.colour == "custom"` in `colours()`, and the two validators that mentioned it.
- `fileSettings()`, which existed only to re-read CONFIG for the resets - now `defaults()`, one call to the same
  `makeConfig`.
- The duplicated `textSize = 11` that the old block carried twice.

**What stays.** `DEFAULTS` (14 keys, one line each), the four tabs and their rows, the settings file, and `font` /
`textSize` / `trackerSize`, which are defaults for the page's own rows.

**Tests.** Two custom-colour tests went with the feature; the section-1 check now reads `DEFAULTS` and asserts that
neither `local CONFIG`, `local CUSTOM` nor `"custom"` is in the file. Replay **293 / 293**.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` (87,876 B, `72DCDB76F3FC31D3`, `VERSION = "v1.1"`); `mod\mod.json`
(`version: "1.1"`); `verify.cmd` -> **293 / 293**.

---

## D33 - The store's call shape is verified against the shipped client; the write is still unproven (2026-11-05, no build)

**Why this exists.** D29 rests on three citations into `ui\utils\hudeditorutils.dec.lua` (`:2719`, `:2875`) and on a
member dump from a launch. Neither the file nor its line numbers could be checked here: the decompiled tree was not
extracted, and `bo7.rar` holds LuaJIT bytecode, not text, so a plain `Select-String` over it finds nothing. This entry
records the check, so the next reader does not have to redo it.

**The tree, extracted.** `k's discord\lua_decompile.rar` -> 12,582 `.dec.lua`, 114.8 MB, extracted for this check to
`%LOCALAPPDATA%\Temp\opencode\bo7-dec\`. `ui\utils\hudeditorutils.dec.lua` is 2,966 lines and carries all four sites:

| Line | Code |
|---|---|
| 2206 | `HUDEDITOR.filestorage = "hud_editor_config"` |
| 2719 | `local readallfilecontent = FileStorage.readallfilecontent( f0_local0, HUDEDITOR.filestorage )` |
| 2841 | `FileStorage.writeallfilecontent( f0_local0(), HUDEDITOR.filestorage, "" )` |
| 2875 | `FileStorage.writeallfilecontent( f0_local0, HUDEDITOR.filestorage, f10_local5 )` |

**What that settles.**

1. **The argument order is `(controller, name, text)`**, which is the mod's primary call (`zm_xp_hud_post.lua:182`
   read, `:273` write) with `(name)` kept only as the fallback. The decompiler's mangled first argument at the client's
   own call site is therefore no longer a reason to doubt the order: the same expression, called twice, at two sites.
2. **The name is a plain string with no extension and no path** — `"hud_editor_config"`. A mod name
   (`"zm_xp_hud_config"`) is the same kind of key, so nothing about the store requires a shipped name.
3. **The payload is the caller's business.** The client sends JSON and parses it with
   `JSON.trycastjsonstringtoluatable` (`:2724`), inside a `pcall` that resets to defaults on failure (`:2743`). The
   store does not parse, so the mod's `key=value` lines are legal — they are only ever read by the mod itself.
4. **The two member names are right**, recomputed here rather than trusted: FNV-1a-64(`readallfilecontent`) =
   `0x0469f6d351feeeaab`, FNV-1a-64(`writeallfilecontent`) = `0x193258999f89095e`, both matching the live dump
   (`trace\p5s\console.txt:39-41`, wrapped and called at `trace\p5y\console.txt:311`).

**The client has exactly one user of it.** A string scan of all 12,582 decompiled chunks finds `FileStorage` in one
file, `ui\utils\hudeditorutils.dec.lua`, and the member names in none (they are called by xhash). One precedent, and
it is this shape — not a second, differently-shaped caller to imitate.

**The gap, named precisely.** What has *not* been observed is a write. `call FileStorage` appears three times in every
console paste on this machine (`trace\p5y\console.txt:311`, `trace\p7\console.txt:723`, `trace\p7b\console.txt:1042`)
and all three are the **read** member, returning an empty string: `rets=1 [string:]`. So neither "the write reaches
disk" nor "it is read back after the process exits" has any evidence behind it yet. The read also cannot distinguish
"no file" from "empty file", which is why `readStore()` treats both as nil and logs
`settings: no zm_xp_hud_config yet` — correct on a first launch, indistinguishable from a store that never kept
anything.

**Where it would land, and what to look for.** The profile directory holds 76 files
(`C:\Users\main\AppData\Local\Activision\Call of Duty\players\76561199298356590\` and `403685425\`) and **none** is
named for a store, so the on-disk name of a `FileStorage` entry is not observed for any caller, including the client's
own. The answer, therefore, is one press and one restart, with the file list captured either side of it.

**What this does not change.** No code. The mod's call is already the client's call, so any edit made before a write is
observed would be a guess dressed as a fix. `verify.cmd` still **293 / 293** against the unchanged v1.1.

**Evidence.** `lua_decompile.rar` -> `ui\utils\hudeditorutils.dec.lua:2206,2719,2841,2875`; `bo7.rar` ->
`bo7\luafile\ui\utils\hudeditorutils.lua` (the same file compressed, 27,885 B, zlib; its bytecode strings carry
`FileStorage`, `[HUDEditor] Failed to parse config JSON:` and `SaveStyleConfig produced empty JSON`); FNV-1a-64
recomputation; `trace\p5s\console.txt:39-41`; `trace\p5y\console.txt:311`; `trace\p7\console.txt:723`;
`trace\p7b\console.txt:1042`; `players\` listing.

---

## D34 - The release number is 1.0 until the mod is finished; a build is its size and SHA-256 (2026-11-05, the 88,089 B build)

**Decision (the user's).** `VERSION` stays `"v1.0"` and `mod.json` stays `"1.0"` for every build up to release. The
number is what ships, so it does not move while the mod is still being cut. Build identity moves to the only other
thing already recorded: the file's size and SHA-256, in `PROGRESS.md`'s build log and in `install.cmd`'s read-back.

**What this reverses.** AGENTS.md said "bump `VERSION` on every build (the reload guard keys on it)", which made the
console's first line the proof of *which* build loaded - `[ZmXpHud] v1.1 loaded: bottom, green`. With the number frozen,
three different files all announce `v1.0`, and that line stops distinguishing them. The replacement proof is the pair:
the install's hash read-back (does the game hold the repo's file) plus the mod's own load line (did the loader parse
it).

**What breaks, and how it is handled.** The guard at the top of the script is unchanged:
`if old and old.version == VERSION then return end`. Two consequences:

1. **A changed file under the same number loads on a restart, not on a mod toggle.** Toggling the mod off and on in the
   Mods menu re-runs `postload()` in the same process, the guard sees the same `VERSION`, and the old code stays live.
   That is a known cost of the rule, recorded so it is not a mystery for the next session - it is also why X7/X8 name a
   restart rather than a toggle.
2. A second copy of this bar from another mod is still silenced, because that check compares two different files'
   `VERSION` strings, which remain different (D4, X4).

**What changed.** One line and a two-line comment in the script (`VERSION = "v1.0"`, and the note beside it saying why
it does not move), `mod.json` `1.1` -> `1.0`, and the two expected load lines in `verify.py`. **No behaviour changed**:
the 88,089 B build is the 87,876 B build with the number and the note changed, so a launch against either answers the
same question - X8 can be run before or after the reinstall.

**Evidence.** `mod\lua\zm_xp_hud_post.lua` 88,089 B /
`3EC8910A6572FCEF7DD151439E7336193407244E87CA5E61E0DACFA004AADE6D`, `:113` (the constant), `:117` (the guard), `:2019`
(the load line); `mod\mod.json` 380 B / `7CAD5A0F3233B555A239060BED2F3B577A26BBBA5A8C2BFA37A999DB87AFC048`, version
`1.0`; `verify.cmd` -> **293 / 293** with both load-line checks moved to `v1.0`.

---

## D35 - The store refused the write; the instrument now names the reason (2026-11-05, the 90,449 B build)

**The launch.** v1.1 (87,876 B) in a match, one press: `Colour` -> violet. The console:

    [ZmXpHud] v1.1 loaded: bottom, green
    [ZmXpHud] settings: no zm_xp_hud_config yet - the defaults stand
    [ZmXpHud] colour: violet
    [ZmXpHud] settings: the zm_xp_hud_config write did not read back

**And nothing reached disk.** `trace\2026-11-05-profile-before-x8.txt` listed 76 files with their hashes before the
launch; afterwards it is still 76, with no new file in either profile directory and the only writes being the game's own
`*.csf`. So this is not "the read-back was impatient" - the store kept nothing at all. D29's write path, correct in
shape (D33) and exercised by a real press, does not save.

**What the log cannot say, which is the actual defect.** `persist()` discarded `pcall`'s message, tried two shapes and
printed one sentence for both. Three different causes were therefore indistinguishable:

1. the call **raised** - a wrong argument count, or a name of the wrong type;
2. the call was accepted but the store keys by **xhash**, so a plain-string name was written somewhere the read never
   looks (the one observed call, `trace\p5y\console.txt:311`, passes a xhash name - though that may be the probe's own
   call, which is exactly why it cannot be leaned on);
3. the store takes the call and keeps nothing for a name the client never registered.

**The instrument.** Inside the store block only, so the bar, the page and the contract are untouched:

- **four shapes, not two** - `(controller, name, text)`, `(controller, xhash, text)`, `(name, text)`, `(xhash, text)`;
  a read tries all four, a write uses the known shape or walks the rest;
- **a verdict one tick late** - a store that flushes at the end of a frame cannot be read inside it, which is the whole
  difference between "saved" and "saved nowhere";
- **the reason kept** - `pcall`'s message survives into the log;
- **the working shape named** - `settings: saved to zm_xp_hud_config via controller+name (N bytes)`, or
  `settings: the zm_xp_hud_config write did not read back - <shape> raised: <error>; <shape> read back nothing; ...`

**What stays.** One store, one name (`zm_xp_hud_config`), one payload (`key=value`, closed key set), two members, no
dvar, no exec, no path. `verify.py` still pins all of that; three assertions were **added** (296 / 296, up from 293):
the plain stub adopts `controller+name`, a stub that answers only a xhash name is found and named, and a stub that keeps
nothing yields one line listing every shape and never the word `saved`.

**Not claimed.** That the matrix finds a shape that works in the game. If all four fail there, this store is the wrong
tool and the next decision is a different store - not another variation of this call.

**Evidence.** `trace\2026-11-05-launch-3-settings-write.md` (the paste, the disk diff, the reading);
`trace\2026-11-05-profile-before-x8.txt`; `mod\lua\zm_xp_hud_post.lua` 90,449 B /
`3A43D079F237451D86747CE2DAB462AFDB9C2E203C13EBDD880E174C9A438930`; `verify.cmd` -> **296 / 296**.

---

## Closed 2026-11-05 by D29: `FileStorage`'s two hashed members are `readallfilecontent` / `writeallfilecontent`

Was open: naming them needed the PNDB database. **Answered**: both are FNV-1a-64 of those two names, and the store is
implemented in v26 (D29). The record of the question:

The launch printed:

    storage: FileStorage (table), PlayerData (table), GAMERPROFILE (table), DvarUtils (table)
    FileStorage members: xhash: #x0193258999f89095e:function xhash: #x0469f6d351feeeaab:function

Two functions, names hashed, and the hash is all the launch needed to print. PNDB turned out to be a name blob rather
than a keyed table, but the names were recoverable anyway: `readallfilecontent` occurs in it as plain text, and
FNV-1a-64 of that name is exactly `0x0469f6d351feeeaab`; the other member's key is FNV-1a-64 of `writeallfilecontent`.
Both calls are now in the mod, with a read-back check (D29).


## D36 - All four FileStorage write shapes raise; stop guessing at this call (2026-11-06)

See trace\2026-11-06-launch-4-write-raises.md. Second failed attempt on X8 (D35 was the first). The write member rejects the name argument in every shape; a plain string with the controller from Engine.GetFirstActiveController() is the client's own form and has not been tried yet. No further variants without the user's go-ahead.


## D37 - The xhash-first lookup changed nothing; even the client's own file cannot be read (2026-11-06)

The 91,889 B build looked members up by xhash first and logged a probe. Result: byte-identical failure, and `read hud_editor_config` (the client's own file) raised too, with a 62 B error string. FileStorage is unusable from this mod's VM for every name. Third failed attempt on the same criterion; the route is closed.

## D38 - Persist through one dvar and a GSC store; the "no dvar" rule is narrowed (2026-11-06)

Route: the Lua writes the dvar `zm_xp_hud_cfg` (13 `key=value` pairs joined with `,`, about 170 chars) with `Dvar.SetDvarString(HD(name), text)`, the form `Assets\Lua\bo6_zombie_builds_post.lua:54` uses. `mod\scripts\zm_xp_hud_store.gsc`, modelled on `custom_scripts\mp_bo6_store.gsc`, mirrors that dvar to `kronos\zmxphud\settings.json` with `nengine_store_load/get/set/save`, and puts it back into an empty dvar at start. The Lua adopts it once, at the first non-empty read in its tick.

Contract amendment (needs the user's explicit OK, flagged in PROGRESS.md): the "calls no setter" rule becomes "sets exactly one dvar, `zm_xp_hud_cfg`, and no XP, profile or other value". `verify.py` asserts this on both the Lua and the GSC source and still asserts the XP/profile guarantee.

UNVERIFIED until a launch: (a) the mod's `scripts\` folder is compiled and run, (b) the Lua `SetDvarString` member resolves under `H("SetDvarString")` or the plain name, (c) the GSC sees the Lua-set dvar. Evidence to look for: `[ZmXpHud] settings: wrote zm_xp_hud_cfg ... reads back identical`, then `kronos\zmxphud\settings.json`, then `settings: 13 read from zm_xp_hud_cfg` after a full restart.

D38 approval: the user accepted the narrowed rule on 2026-11-06 ("I dont remember setting up that contract, so its fine").

## D39 - Renamed to xp_hud_overlay; the GSC registers the dvar (2026-11-06)

Launch 5 (the 87,369 B build) proved the mod's `scripts\` folder is compiled and run (`compiling zm_xp_hud_store.gsc`, `placed`, `link ... -> 0`) and that `Dvar.SetDvarString` does not raise, but the dvar read back **nothing** right after the write. Working theory: a Lua set of a dvar that does not exist yet is ignored, so the GSC now creates it at start (the saved text, else `none`), and the Lua logs the read-back a second time one tick later to tell "ignored" from "lands late".

Rename, at the user's request ("a platform for further changes"): mod id and install folder `xp_hud_overlay`; `lua\xp_hud_overlay_post.lua`; `scripts\xp_hud_overlay_store.gsc`; dvar `xp_hud_overlay_cfg`; store `kronos\xphudoverlay\settings.json`; log prefix `[XpHudOverlay]`; global `XpHudOverlay`. Kept: the `zmhud_*.png` texture names (internal asset names, no visible effect). Entries D1-D38 and `trace\` keep the old names on purpose: they are the record of what ran. `install.cmd` removes the pre-rename `mods\zm_xp_hud` so two copies never load.

## D40 - Launch 6: the dvar write lands; the file does not appear (2026-11-06)

The 87,762 B / `E63C5A9A3076F262` build: `settings: wrote xp_hud_overlay_cfg (157 bytes), reads back identical`, and again one tick later. So D39's theory held (the GSC creates the dvar, the Lua set then sticks), and `settings: 0 read from xp_hud_overlay_cfg` shows the Lua read the GSC's `none`. But `kronos\xphudoverlay\` did not exist minutes later, while the other stores wrote at match start (`bo6\picks.json` 00:27:39). Either this GSC's loop never saw the Lua's value, or the save did not land. A GSC cannot print here (no .gsc under custom_scripts does), so the GSC now saves once at start and refreshes `beat` / `seen` keys every 10 s; the file itself says which. Diagnostic keys come out once persistence is confirmed.

## D41 - Persistence confirmed across a restart; diagnostics removed (2026-11-06)

Launch 7 (GSC 47CCB21BF16D7B33): kronos\xphudoverlay\settings.json held cfg and seen equal to the last press. The user then restarted the game and reported the overlay config restored. So D38's route (Lua SetDvarString -> GSC dvar loop -> store file -> GSC creates the dvar from the file at start) persists settings end to end. The D40 beat/seen keys and the start-up save are removed from the GSC (cleanup build, not yet launched); verify.py 300 / 300. Evidence: user's report plus the settings.json read on disk.

## D42 - The cleaned GSC did not create the dvar (2026-11-06)

Launch 8 (cleanup GSC C3302F229918838A, 933 B compiled): compiled, placed, linked, but the Lua write read back nothing and there was no 'settings: N read' line, so the dvar was never created and the bar loaded on defaults. kronos\xphudoverlay\settings.json still held the saved cfg, so the data was intact. The only functional change from the working launch-7 GSC was the stored value moving from level.xp_hud_overlay_stored to a local. UNVERIFIED hypothesis: that local broke the script under this compiler. The level variable is restored (1,639 B / 1522B47B2A5F2CE0), diagnostics stay out. Settles it: one launch showing 'settings: 13 read'.

## D43 - Cleaned GSC confirmed; restart read works (2026-11-06)

Launch 9 (GSC 1,639 B / 1522B47B2A5F2CE0, no diagnostics): compiled fresh (968 B placed), linked, and the Lua logged 'settings: 13 read from xp_hud_overlay_cfg' at start-up, then 'wrote xp_hud_overlay_cfg (155 bytes), reads back identical' (and one tick later) on a press of bar look: paws. This confirms D42's hypothesis in effect: with the stored value held on level.xp_hud_overlay_stored the GSC creates the dvar; with a local it did not. Keep it a level variable - do not 'tidy' it. Persistence is final: no diagnostics left in the GSC.

## D44 - Release trim: HUD-font option, shadow rows and dead constants removed (2026-11-06)

The in-game page never exposed CFG.font and the 13 saved keys do not carry it, so 'hud' (the soe_rf PNG glyph face) was reachable only by editing DEFAULTS in the source: dead for every user. Removed with it: glyphRow, the ADV advance table, fontAvailable, nullRow, and the labelShadow/gainShadow rows (always no-op stubs, because the engine text draws its own shadow), the preset 'shadow' colours and popupColours (now popupColour, accent only), plus the unused LOOK_POOL and TRACK_ALPHA. The default face (engine text) and every user-visible behaviour are unchanged. verify.py: 295 / 295; the 5 dropped checks were the glyph-face ones (section 5b, DEFAULTS.font, the 'plain text' attach-log wording). make_mock.py keeps its own ADV copy to size text in the picture and draws a black shadow. Lua 1,997 -> 1,862 lines, 86,861 -> 79,067 B. New tool: make_index.py writes release\index_entry.json (the kronos-data entry, sizes and sha256 read from mod\) and release\upload\ (flat names for the GitHub release).

## D45 - The load log no longer implies a colour is drawn at boot (2026-11-06)

The line 'v1.0 loaded: bottom, green' printed the compiled-in DEFAULTS at script load, before the GSC fills xp_hud_overlay_cfg (that happens when a level starts), and looked like a green bar at boot. Nothing is drawn in the frontend (poll(): inFrontend() hides it). The line now reads 'loaded; nothing is drawn until a match starts (settings so far: ...)' and is logged after the first applyStored. Two verify.py checks pinned the old wording and were updated to it; no assertion was weakened.
