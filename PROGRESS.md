# xp_hud_overlay - progress

Updated: 2026-11-05

## Current verified state

**v1.0 (90,449 B) is BUILT and replayed with the store instrument; the game still holds the 87,876 B file, and the one
launch made on 2026-11-05 ran that one.** Its verdict: the bar, the pause row, the page and the tabs all work, a press
reaches the setter, and then **the settings store refuses the write** - `settings: the xp_hud_overlay_config write did not
read back`, with the profile directory unchanged at 76 files afterwards (D35,
`trace\2026-11-05-launch-3-settings-write.md`). The instrument in the 90,449 B build exists to say *why*, in one press,
instead of one launch per guess.

The release number stays **1.0 until the mod is finished** (D34), so a build is identified by its size and SHA-256,
not by `VERSION`. v1.0 also replaced the `CONFIG` / `CUSTOM` blocks with one short `DEFAULTS` table: the page is the
settings screen (D32). v4 was the last build before the page work (row, page and
every toggle confirmed). Since then: the page became a compact tabbed popup (v5), `Text` and `XP popup` became
independent switches (v6), the length became a slider (v7), and the label is now centred on a centred bar with the
empty row under it closed up (v8) - `trace\2026-11-05-launch-2-v4.md`, `trace\2026-11-05-v7-length-slider.md`.

| Field | Value |
|---|---|
| Script | `mod\lua\xp_hud_overlay_post.lua`, `VERSION = "v1.0"` - **90,449 B / `3A43D079F237451D`** |
| Manifest | `mod\mod.json`, 380 B / `7CAD5A0F3233B555` - id `xp_hud_overlay`, name "Operator XP HUD", version `1.0` |
| Replay | `.\verify.cmd` -> **296 / 296**, exit 0 (196 at v2, 225 at v3, 236 at v4, 241 at v5, 244 at v6, 253 at v7/v8, 264 at v9, 272 at v19/v20/v21, 279 at v22/v23, 282 at v24, 284 at v25, 296 at v26, 298 at v27, 295 at the 90,557 B build, 293 at the 87,876 B and 88,089 B builds, 296 at the 90,449 B build) |
| Preview | `python make_mock.py preview.png` -> `CFB462D35A150AFD...` (the new centred baseline, D12); `python make_mock.py preview-page.png --page` draws the popup from its own constants |
| Launched | **v3: bar ok, pause row missing. v4: row, page and every toggle confirmed. v10: five bugs found (D15). v22: the styles drew nothing (D27). v25: installed, never launched. v27: installed, never launched. v1.0 (90,557 B): installed, never launched. The 87,876 B build (logged as v1.1): **LAUNCHED 2026-11-05** - row, page and tabs fine, `colour: violet` reached the setter, and the store then refused the write with nothing on disk (D35, `trace\2026-11-05-launch-3-settings-write.md`). v1.0 (88,089 B, renumbered): never installed. v1.0 (90,449 B, the instrument): replayed, **not installed**.** |
| Log prefix | `[XpHudOverlay]` - tells this mod's lines apart from `mods\xp_hud`'s `[XpHudOverlay]` |
| Reads | `zm_local_rankxp` / `zm_local_rank` / `zm_local_prestige` (Zombies), `PROGRESSION.GetPlayerXP` /
  `GetPlayerRank` (MP / Endgame). Display only: no setter anywhere in the file |
| Live settings | `XpHudOverlay.SetText` / `SetTextPos` / `SetTextSize` / `SetTracker` / `SetTrackerSize` / `SetTrackerColour` / `SetBar` / `SetPrestige` / `SetWidth` / `SetAnchor` / `SetColour` / `SetLook` / `Reset*`, and the page itself. Every one writes the store (D29) |
| Menu entry | three hooks, all aimed at the client's `zmpausemenubuttons` list: the build wrapper (id),
  its registered constructor, and `MenuBuilder.registerType`; `XpHudOverlay.Menu()` also opens the page |
| Writes | the settings file only (`xp_hud_overlay_config`, through the client's `FileStorage`, D29). No dvar, no profile value, no `SetDvar`, no `exec` |

Full SHA-256: `mod\lua\xp_hud_overlay_post.lua` =
`3A43D079F237451D86747CE2DAB462AFDB9C2E203C13EBDD880E174C9A438930`;
`mod\mod.json` = `7CAD5A0F3233B555A239060BED2F3B577A26BBBA5A8C2BFA37A999DB87AFC048`.
(The build the game currently holds is `72DCDB76...` / `AB47BB52...`, the 87,876 B file with `VERSION = "v1.1"`; the
next install replaces it.)

## What changed (v4-v6)

| Change | Why |
|---|---|
| **A style now *is* the bar**: the black pill is hidden and the style draws across the whole width, filled pieces in the accent and the rest at 30 % of it | *"you still have a flat black bar behind it ... This currently doesnt look good"* - and the reference images have no pill |
| Styles may use the pill's height (3..11) instead of the thin 4..10 fill band | a paw or a scale at 6 px was unreadable; the text still starts at 18, so nothing collides |
| `Divided` = 25 segments at 40 px pitch, 80 % alpha (MW2), `Blocks` = 100 thin stripes at 10 px, `Cat paws` = 38 paws at 26 px, `Dragon` = 45 scales at 22 px | the four references: segments, loading stripes, a paw trail, a scale line |
| `SetFill` now owns the track's visibility (`CFG.look == "line"`), in `setFill` **and** `lookVisible` | otherwise `applyAll`/`repaint` re-showed the pill over a styled bar |

**Settings: built, call shape verified, still never written in anger.** The store was implemented at v26 (D29) and its
call is now confirmed to be the client's own - `FileStorage(controller, "name", text)` at three shipped sites in
`ui\utils\hudeditorutils.dec.lua` (`:2206`, `:2719`, `:2841`, `:2875`), with a plain unextended name and a payload
format the store never parses (D33). What has **no** evidence yet is a write reaching disk: every console paste on
this machine shows only the *read* member being called, returning `""`. That is row **X8**, and it is one press and
one restart, not a build.

## Build log

| Build | Date | Size / SHA-256 (16) | Replay | Notes |
|---|---|---|---|---|
| v1 | 2026-11-05 | 38,820 B / `F4D21982FFD505AA` | 192 / 192 | Extracted from `..\zm_hud` v26. Never installed |
| v2 | 2026-11-05 | 39,610 B / `9EC96545D89CDB9E` | 196 / 196 | Renamed, history stripped, dead code removed, three defects fixed (D4/D5). Never installed |
| v3 | 2026-11-05 | 51,771 B / `1862EEA509129B9F` | 225 / 225 | The settings page (D6/D7). **Installed and launched**: bar drawn, pause row did not appear |
| v4 | 2026-11-05 | 55,821 B / `5D1672AD6FAAC214` | 236 / 236 | Three pause hooks + a bounded build log (D8). **Installed and launched**: row added by the *register* hook, page opened, every row worked |
| v5 | 2026-11-05 | 58,551 B / `9B85AC9DD5885D11` | 241 / 241 | The compact tabbed popup (D9). Never installed - superseded by v6 |
| v6 | 2026-11-05 | 58,780 B / `AE3F6EC9B10DD60F` | 244 / 244 | Text and the popup are independent (D10). Never installed - superseded by v7 |
| v7 | 2026-11-05 | 62,415 B / `4F971DF135FEBA60` | 253 / 253 | The `Bar length` slider (D11). Never installed - superseded by v8 |
| v8 | 2026-11-05 | 62,228 B / `B7210131E14A77ED` | 253 / 253 | Centred label, gap closed (D12). **Installed 2026-11-05**, never launched |
| **v9** | 2026-11-05 | 64,386 B / `EDB2ED0997410014` | 264 / 264 | Mouse tabs, Esc, `Bar: ON/OFF`, 200 px floor (D13). Never installed - superseded by v10 |
| v11 | 2026-11-05 | 76,673 B / `C644E12D219900D1` | 257 / 257 | The five launch-2 bugs (D15). Ran; the six geometry points of D16 came from it |
| v12 | 2026-11-05 | 78,676 B / `DE0A9B9019B6CEC4` | 258 / 258 | Adjacent popup, uncapped glow, text drop, popup size (D16). Ran: the drop did not apply on the bar switch |
| v13 | 2026-11-05 | 78,649 B / `AD45B6B6FE1A7387` | 259 / 259 | `SetBar` re-places the rows, so the drop is immediate (D17). Never installed - superseded by v14 |
| v14 | 2026-11-05 | 82,049 B / `AE9AD9BD7F5355B9` | 268 / 268 | Bar styles over the black pill (D18). Ran: the pill showed through and made them look stuck on |
| v15 | 2026-11-05 | 82,381 B / `3C9DABD0AC5677D6` | 269 / 269 | A style IS the bar (D19). Ran: the art was wrong - squashed paws, unslanted MW2 segments |
| v16 | 2026-11-05 | 82,749 B / `56A98E9DA0FCE9F0` | 270 / 270 | Slanted MW2 segments, 45-degree paws, a scale chain (D20). Ran: the MW2 bar read shorter than the default and the paw was not a paw |
| v17 | 2026-11-05 | 82,749 B / `8DA4A011CE6333D4` | 270 / 270 | MW2 at the pill's height, a four-toed paw, a scale link (D21). Ran: the SVGs were the whole design, not a palette |
| v18 | 2026-11-05 | 84,446 B / `FA61E038C8A4A8CE` | 271 / 271 | The strips as the bar (D22). Ran: the art was squashed into the bar box and a plate read as a black bar again |
| v19 | 2026-11-05 | 85,304 B / `EAB0BAFB563A351F` | 272 / 272 | Strips tiled 1:1, translucent pill (D23). Superseded by the user's own 1200x16 art |
| v20 | 2026-11-05 | 85,303 B / `BA4C84B74A45D186` | 272 / 272 | The user's strips at 1200x16, one tile each (D24). Ran: the pill was still black |
| v21 | 2026-11-05 | 85,473 B / `007FC8500DB8C2B6` | 272 / 272 | The pill uses the dim accent base colour (D25). **Did not load**: `>>` is Lua 5.3, the client is 5.1 |
| v22 | 2026-11-05 | 85,596 B / `8021A94082162189` | 279 / 279 | Lua 5.1 syntax fixed (D26). Ran: the styles drew nothing at all |
| v23 | 2026-11-05 | 85,885 B / `F6F8F12E2A8A7A3E` | 279 / 279 | Strip tiles moved into their stencil; `Cats` / `DraGON`. **Never installed** - the anchoring was still wrong (D27) |
| v24 | 2026-11-05 | 86,439 B / `F1CFCEB43BF5D0DE` | 282 / 282 | Stencil children anchored like the glyph rows; the fill cache keys on the colour too (D27). **Never launched** - superseded by v25 |
| v25 | 2026-11-05 | 86,622 B / `5FF3DE236AA464E8` | 284 / 284 | `Divided` and `Blocks` shorter, in the fill band (D28). **Never launched** - superseded by v26 |
| v26 | 2026-11-05 | 94,066 B / `E964DCF69E0D5384` | 296 / 296 | Settings persist through the client's own `FileStorage`, `xp_hud_overlay_config` (D29). **Never installed** - superseded by v27 |
| v27 | 2026-11-05 | 92,993 B / `982390FAD2C5483D` | 298 / 298 | `+N XP` pinned right of the text, its Position row gone; the halo drops with the text (D30). **Never launched** - superseded by v1.0 |
| v1.0 | 2026-11-05 | 90,557 B / `B7CED61F850D0450` | 295 / 295 | First release number: the debug flag, the build log, the storage probe, three unused PNGs and the history in the comments gone (D31). **Never launched** - superseded by the 87,876 B build |
| v1.1 *(renumbered)* | 2026-11-05 | 87,876 B / `72DCDB76F3FC31D3` | 293 / 293 | `CONFIG` and `CUSTOM` replaced by one `DEFAULTS` table: the page is the settings screen (D32). **Installed 2026-11-05** (both hashes read back), never launched. Its `VERSION` said `v1.1`; D34 renumbers it |
| v1.0 | 2026-11-05 | 88,089 B / `3EC8910A6572FCEF` | 293 / 293 | The renumber itself (D34): `VERSION = "v1.0"` and `mod.json` `1.0`, plus the two-line note beside `VERSION` saying why it does not move. **No behavioural change** - the same code as the 87,876 B build. Never installed. |
| v1.0 | 2026-11-05 | 90,449 B / `3A43D079F237451D`** | **296 / 296** | The store instrument (D35): four call shapes, a verdict one tick late, `pcall`'s reason kept, and the line naming the shape that answered. Driven by the 87,876 B launch, where the write was refused and nothing reached disk (`trace\2026-11-05-launch-3-settings-write.md`). **NOT INSTALLED** |

| **v1.0** | 2026-11-06 | **87,369 B / `360C2491A515252C`** | **300 / 300** | D38: dvar `xp_hud_overlay_cfg` + `scripts\xp_hud_overlay_store.gsc`; FileStorage removed. **NOT INSTALLED** |
| **v1.0** | 2026-11-06 | 87,762 B / `E63C5A9A3076F262` + GSC 1,639 B / `1522B47B2A5F2CE0` | 300 / 300 | D43: **INSTALLED and confirmed in game** - restart read `13`, press writes back identical. No diagnostics. |
| **v1.0** | 2026-11-06 | 86,861 B / `074B16988F048B7A` + GSC 1,624 B / `019AB29DD28A3779` | 300 / 300 | Release pass: header cut from 31 lines to 12, internal D-refs removed from comments (comments only, no code change). verify.py header assertion now pins what the new header says. **NOT INSTALLED** (game has the 87,762 B build, same behaviour). |
| **v1.0** | 2026-11-06 | 79,067 B / `AECDE765E22BEA63` + GSC 1,538 B / `228C785B1E718FA2` | 295 / 295 | D44: dead-code pass (HUD-font option, shadow rows, unused constants), comments and blanks tidied. **NOT INSTALLED** (game has the 87,762 B build; same behaviour). |

## Next action

**Persistence is done (D41-D43), installed and confirmed.** Remaining: publish when the user says it is ready (PR to Divity/kronos-data + a stable host URL such as a GitHub Release; recompute sizes and sha256 first), and rename the folder `zm_xp_hud` -> `xp_hud_overlay` once this session is closed (then fix the parent AGENTS.md / PROGRESS.md references).`n`n(Older text below is the pre-D38 state.)

Old: **Close the game, then ask for the install.** Build: 87,369 B / `360C2491A515252C` (script), `scripts\xp_hud_overlay_store.gsc` `14EC322831250A5D`.

**Why a new route (D36-D38).** FileStorage raises for every name, even the client's own file. Settings now go through
the dvar `xp_hud_overlay_cfg` and a GSC store (`kronos\xphudoverlay\settings.json`). This narrows the "no SetDvar" rule (approved by the user 2026-11-06) to
one dvar.

**Then one press, one restart.** Launch, change one setting, copy the `[XpHudOverlay] settings:` lines. Expect
`settings: wrote xp_hud_overlay_cfg (N bytes), reads back identical`, and `kronos\xphudoverlay\settings.json` on disk.
Close the game completely, relaunch: expect `settings: 13 read from xp_hud_overlay_cfg` and the bar in the saved state.
If the GSC folder is not compiled, the dvar line appears but no json does - that is the finding to report.
## Open questions

- **The settings store refuses the write** (D35, X8). Observed, not suspected: `settings: the xp_hud_overlay_config write
  did not read back` on a real press, and the profile directory unchanged at 76 files, so nothing reached disk. The call
  shape itself is the client's own (D33), so the remaining candidates are a raised call, an xhash-keyed name, or a
  store that keeps nothing. The 90,449 B build distinguishes all three in one press. **Do not claim persistence, and do
  not add a second store until that line has been read.**
- Whether `Prestige: OFF` should also hide the `PM` marker (it hides both, since both are the same prefix).
- `Look` has five styles (`Line`, `Divided`, `Blocks`, `Cats`, `DraGON`); the last two are the 1200x16 strip art,
  cropped by two stencils and never scaled (D24/D27). A taller band would be the only way to draw that art bigger -
  the text row starts at 18, so the art has 16 px.
- The 8 px gap above the pill (12 -> 20) is a choice, not a measurement: the eye in a match is the test.


