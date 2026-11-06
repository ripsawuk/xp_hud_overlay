# PLAN - xp_hud_overlay

**Goal:** a Kronos mod that puts the operator's level and XP on screen, and **only** that - released on its own,
independent of the weapon-level, camo and tuning work in the parent project.

**Method:** read the shipped client and the parent project's evidence, change the script, then prove it with
`verify.cmd` (logic and argument shapes) and with one launch (the game actually draws it). Nothing is installed
without the user's word and a closed `cod25-cod.exe`.

Status: `todo` / `doing` / `blocked` / `done`. One row is `doing`; that row names the next action.

---

### X1 - Extract the operator layer into its own project

- **Question:** which parts of `..\zm_hud\zm_hud_post.lua` v26 belong to the operator bar alone, and what has to
  come out so the file is a complete mod on its own?
- **Status:** **done 2026-11-05.**
- **Result:** one coupling and one geometry block. `CONFIG.layout` + `_G.ZMHUD_LAYOUT` existed only to place the
  weapon bar above this one, and the text row cleared a pill that is no longer drawn. Everything else is the bar.
  The file carries no setter, no accrual, no channel dvar - which is what makes it shippable alone.
- **Done when:** the script loads without any weapon-side reference and the replay still covers the model, the
  dvars, the attach, the geometry, the tracker, the colours and the idle-is-silent regression.
- **Evidence:** `mod\lua\xp_hud_overlay_post.lua` (named `zm_hud_post.lua` in v1); `verify.cmd` -> **192 / 192** at v1,
  **196 / 196** now; `docs\DECISIONS.md` D1/D2.
- **Ruled out:** keeping `layout` as a vestigial knob (a config line that changes nothing is a trap for the next
  reader); carrying `zwxp.gsc` or any `scripts\` file over "in case" (this mod reads dvars the client already
  writes).

---

### X1b - Rename to the mod's own name and strip the code

- **Question:** what in the v1 file is history rather than behaviour, and does the file name still have to be the
  parent's?
- **Status:** **done 2026-11-05.**
- **Result:** the file is `mod\lua\xp_hud_overlay_post.lua` and the log prefix is `[XpHudOverlay]`. Removed: the `HEIGHT`
  constant, `local P` and its assignments, every `v16`..`v26` / `D355` / `PROGRESS.md` marker, and the `png = true`
  on a missing optional layer. Fixed: the `+N XP` popup outliving the bar, `SetAnchor` not moving a built bar, and a
  width estimate that disagreed with the row it estimates. The bar's geometry and behaviour are unchanged.
- **Done when:** the replay is green, the harness fails when either of the two fixed defects is put back, and the
  preview is byte-identical to v1's.
- **Evidence:** `verify.cmd` -> **196 / 196**; mutation run in which removing the two fixes fails 3 assertions
  (`193 / 196`); `make_mock.py` output hashed identical to `preview.png` (`280BB5A0EB74E01F`); `docs\DECISIONS.md`
  D4/D5.
- **Ruled out:** keeping `zm_hud_post.lua` "so the other mod still finds it" (the two mods are separate folders and
  the loader takes any `*_post.lua`); renaming `_G.XpHudOverlay` (it is the documented API and the reload guard that
  silences the older copy when both load).

---

### X2 - One launch: does the standalone mod load, draw, and open its page

- **Status:** **done 2026-11-05** (v4). The row, the page and every toggle were confirmed in a match; the trace is
  `trace\2026-11-05-launch-2-v4.md`. Everything since is X7.
- **Question:** with `mods\xp_hud_overlay\` installed and `mods\xp_hud`'s copy of this bar disabled, does the client load
  the mod's Lua, decode the five PNGs, attach the bar, move it on a kill, and put a working `OPERATOR XP HUD` row in
  the Zombies pause panel?
- **Install:** `install.cmd` (`cod25-cod.exe` closed). Rollback: delete `cod25\kronos\mods\xp_hud_overlay\`.
- **Predictions:** `[XpHudOverlay] v4 loaded: bottom, green`; `pause hook armed (n)`; `build <type> id=<id>` lines on
  pause; `settings row added to the pause menu (<path>)`; `settings page opened (general)` when the row is pressed,
  with the page drawn over the pause. v3's launch already confirmed the bar and the dvar source
  (`trace\2026-11-05-launch-1-v3.md`); this launch is about the row.
- **Done when:** the console paste and two screenshots (the bar, the page) are in `trace\`, and each prediction is
  confirmed or refuted.
- **Ruled out:** reading a silent log as a negative; installing to `Assets\Lua` as a "second try" (that path is the
  pre-mod home, and a copy there beside the mod is a double draw, not a fallback).

---

### X3 - Release the mod

- **Status:** `todo`, after X2.
- **Question:** what does the published folder look like, and what does a stranger need to install it?
- **Shape:** `mod\` is the mod (`mod.json`, `lua\`, `images\`), copied to `mods\xp_hud_overlay\`. The README carries
  install, the config table, the presets and the four things the row can say. A zip of `mod\` is the release
  artifact; hashes go beside it.
- **Done when:** a zip exists whose unpacked contents are exactly the four allowed shapes, its hashes are recorded
  here, and the README's install steps are the ones X2 actually used.
- **Ruled out:** shipping the docs, the replays or `trace\` inside the mod folder (the Kronos format allows only
  `mod.json`, `lua\`, `scripts\`, `images\`).

---

### X5 - A settings page you can open in a match

- **Status:** **done 2026-11-05 at the desk** (built and replayed); the in-game half is X2's single launch, not a
  row of its own.
- **Question:** can this mod give the user a settings menu inside a match, with tabs, where a change to the text row
  takes effect on the bar already on screen - without writing a dvar, a file or a profile value?
- **Result:** yes, three findings.
  1. **The entry is the client's own pause list.** The ZM pause panel is a `LUI.UIVerticalList` with
     `id = "zmpausemenubuttons"` (`ui\generated\widgets\ingame\zm\zmpausemenubuttons.dec.lua:233-236`), built through
     `MenuBuilder.BuildRegisteredType` - the call this mod already wraps for the bar. Appending one `genericbutton`
     whose `button_action` opens a page needs no input code of ours; the panel already navigates its list.
  2. **The page is built from widgets that panel itself builds in this VM**: `LUI.UIVerticalList` and
     `MenuBuilder.BuildRegisteredType("genericbutton", ...)`. That is deliberate: the frontend's
     `GenericButtonListFlyIn` (`ui\generated\widgets\frontend\genericbuttonlistflyin.dec.lua`) is a frontend widget
     and may not be loaded in the match VM, while `genericbutton` is proven there by the pause panel itself.
     The page is registered with `MenuBuilder.registerType(id, build)` and opened with
     `LUI.FlowManager.RequestPopupMenu(nil, id, true, ctrl, false, {})` - the shape a shipped mod on this client
     family uses (`Warzone Progression 1.0\Assets\Lua\wzprogression_post.lua:1762-1786, 4448-4452`).
  3. **"Live" is a repaint, not a rebuild.** The label, the tracker and the soft light are built with every bar and
     hidden with `SetAlpha`; a row's action calls `repaint(bar)`, so `Text: OFF` is three cached `SetAlpha` calls on
     the elements that are already drawing. Nothing is created, nothing is duplicated, and the row updates its own
     text in place.
- **The four Appearance rows:** `Text`, `XP popup`, `Position` (bottom/top) and `Colour` (cycles the ten presets).
  General carries the version, the live XP source, the bar count and `Reset the file's settings`.
- **Also exposed to another script:** `XpHudOverlay.Menu(tab)`, `XpHudOverlay.CloseMenu()`, `XpHudOverlay.SetText(on)`,
  `XpHudOverlay.SetTracker(on)`, `XpHudOverlay.Reset()`, beside the existing `SetColour` / `SetAnchor`.
- **Done when:** the replay covers the page (registered type, popup request, row list, a toggle that leaves the bar
  element itself untouched, the pause entry, and idle staying silent), and one launch shows the page. The desk half
  is done: `verify.cmd` -> **225 / 225**.
- **Ruled out:** a hotkey for now - `bind` is unproven in this client and a keypress would have to be read through
  `LUI.UIRoot.ProcessEvent`, which is a second unverified surface. The pause row needs none of that. Also ruled out:
  persisting the settings (a dvar or a file write breaks the display-only contract and `verify.py`'s no-write check);
  hiding a tab's rows with alpha instead of rebuilding (they would still take focus in the same list).

---

### X6 - The tab strip, and a key

- **Status:** `todo`, after X2/X5 are seen in a match.
- **Question:** should the two rows marked `[x] General` / `[ ] Appearance` become the client's real tab bar
  (`LUI.TabManager`, which Kronos itself wraps: `kronos\Assets\Lua\ui\LUIFPSCounter.lua:5126-5154`), and is a hotkey
  reachable at all?
- **Shape:** a `LUI.TabManager.SetTabs` page if the match VM has it; otherwise the rows stay. A hotkey needs either a
  proven `bind` that flips a dvar this mod polls, or an input event read from `LUI.UIRoot.ProcessEvent`. Both are
  desk questions first (`ui\widgets\tabmanager.dec.lua`, `ui\luielement.dec.lua`, `ui\flowmanager.dec.lua`).
- **Done when:** either is answered by a launch, or recorded as unproven with the file that would settle it.

---

### X7 - Every row applies on the press, in a match

- **Status:** `todo` - needs one session with screenshots. The 2026-11-05 launch confirmed the entry (row hooked, row
  added, page opened on two tabs) and that a press reaches the setter (`colour: violet`); what it did not capture is the
  picture: a colour re-tinting a styled bar, a style swapping live, the two strips drawing, and `Bar: OFF` taking the
  halo down with the text. The live save-state work is X8.
- **Question:** does a settings press change what is on screen *on that press* - a colour re-tinting a `Blocks` bar,
  a style swapping live, the two strips drawing - with the level text and `+N XP` staying exactly where they are?
- **Install:** `install.cmd` (`cod25-cod.exe` closed). Rollback: delete `cod25\kronos\mods\xp_hud_overlay\`.
- **Predictions:** `[XpHudOverlay] v1.0 loaded: bottom, green`; `Colour` re-tints a styled bar immediately (D27);
  `Look: Cats` / `Look: DraGON` draw the user's 1200x16 art cropped, not squeezed; `Divided` is 6 px and `Blocks`
  5 px on a 7 px pitch (D28); the text does not move.
- **Done when:** a console paste or screenshot shows the colour and the style changing without a reload, and the two
  strips drawing.
- **Ruled out:** rebuilding the whole bar per press (it would reset the popup's timer and move the text); calling
  `SetDvar` to persist the choice (`verify.py` bans it, and the mod must not write).

---

### X4 - Settle the duplicate with `mods\xp_hud`

- **Status:** `todo`, needs the user's decision.
- **Question:** `mods\xp_hud` still carries `lua\zm_hud_post.lua` (the parent's v26 of this bar). With `xp_hud_overlay`
  installed, one of the two has to stop loading it, or the screen carries two operator bars.
- **Options:** (a) `xp_hud` keeps only the weapon files - drop this script from that mod's build; (b) `xp_hud` is
  retired entirely and the weapon work gets its own mod id; (c) both stay and the user enables one at a time.
- **Done when:** the chosen option is written into the other project's `mods\STATE.md` and one launch confirms a
  single bar.
- **Ruled out:** the two scripts coordinating at runtime (they are different files with different `VERSION`s; the
  reload guard cannot stop a second file drawing). The v2 rename gives the two files distinct names, which makes
  the duplicate visible in the log - it does not remove it.

---

### X8 - A settings press survives a restart

- **Status:** `done` 2026-11-06 (D41). The route changed to a dvar + GSC store (D38); launch 7 wrote the file and the
  user's restart restored the settings. The text below is the original FileStorage plan, kept as history.
- **Question:** does a press on the settings page reach disk, and does the next process read it back? D29 built the
  write, D33 confirms the call is the client's own `(controller, name, text)`, and the first real press answered
  **no**: nothing reached disk and the profile directory did not change.
- **Shape:** **no new store, no second mechanism.** The 90,449 B build keeps the one store and makes the failure
  legible - four call shapes, a verdict one tick late (a store that flushes at the end of a frame cannot be read
  inside it), `pcall`'s reason kept, and the line naming the shape that answered.
- **Predictions:** one press prints either
  `settings: saved to xp_hud_overlay_config via <shape> (N bytes)` - then the restart is the only thing left, and it must
  print `settings: 13 read from xp_hud_overlay_config` with the bar in the saved colour -
  or `settings: the xp_hud_overlay_config write did not read back - <shape> raised: <error>; <shape> read back nothing; ...`
  naming every shape and its reason.
- **Done when:** the restart shows the saved values and the file the store creates is named, or all four shapes are
  recorded as refused and D35's third candidate is confirmed - in which case the next row is a different store, decided
  on that evidence.
- **Ruled out:** a second store or a dvar chosen before the line is read; treating D29's in-process read-back as proof
  of persistence (it proves the store answered, not that it kept anything); editing the payload or the store name, both
  of which the replay pins and neither of which the log implicated.

