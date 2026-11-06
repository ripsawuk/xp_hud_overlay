# trace - 2026-11-05 - v3, the in-game settings page

Desk only. Nothing was installed and the game was not launched. These are the commands that produced the numbers in
`PROGRESS.md` and `docs\DECISIONS.md` D6/D7.

## Build

    VERSION v2 -> v3 in mod\lua\zm_xp_hud_post.lua
    mod\mod.json version 2 -> 3, description names the settings page

## Replay

    > .\verify.cmd
    225 / 225
    exit 0

225 = 196 (v2) + 29 new assertions for the settings page and the built-but-hidden rows.

## The new assertions bite (mutation run)

One switch removed from `lookVisible` (`setAlpha(bar.label.group, text and 1 or 0)` -> `setAlpha(bar.label.group, 1)`),
file restored from a byte copy afterwards:

    FAIL text hidden: both rows are built but invisible (a live toggle needs no rebuild) [1, 0]
    FAIL text hidden: an XP change does not light a hidden row [1, 0]
    FAIL Text OFF hides the label, the popup and the soft light, live (1, 0, 0)
    222 / 225

## The look did not move

    > python make_mock.py preview.png
    saved preview.png (1920, 480)
    > Get-FileHash preview.png
    280BB5A0EB74E01F8EF93BB032288B4574FCA5CD50289C59FD99D424BFB60A0C

Byte-identical to v1 and v2's preview: the default bar is the same pixels.

## Hashes of this build

    mod\lua\zm_xp_hud_post.lua   51,771 B  1862EEA509129B9F095D867A60C73E459143A19333DC0DFB8A0E238CB0D34CAD
    mod\mod.json                    378 B  284121A2668D869427E65B9B2AF94E0E0183D1F0CD7A68EB7356C8A9FE2C2A2E

## What is still UNVERIFIED, and the line that settles it

| Claim | Artifact |
|---|---|
| `LUI.FlowManager.RequestPopupMenu` exists and works in the **match** VM | `[ZmXpHud] settings page opened (general)`, or `settings page: LUI.FlowManager is not in this VM` |
| `LUI.UIVerticalNavigatorMenu` exists in the match VM | the page draws; without it the log says `no UIVerticalNavigatorMenu, rows will not navigate` and the page still draws as a plain element |
| the pause panel is caught by `widget.id == "zmpausemenubuttons"` | `[ZmXpHud] settings row added to the pause menu` on the first pause |
| a row appended after the build is navigable | the row takes focus in the pause list |
| a toggle repaints the live bar | screenshot: label gone, track and fill still drawn |

## Install (2026-11-05, user's word, cod25-cod.exe not running)

    cmd /c install.cmd
    -> D:\Games\Shrekinator\Call of Duty\cod25\kronos\mods\zm_xp_hud

Read back independently from the installed folder:

    1862EEA509129B9F095D867A60C73E459143A19333DC0DFB8A0E238CB0D34CAD  mods\zm_xp_hud\lua\zm_xp_hud_post.lua   51,771 B
    284121A2668D869427E65B9B2AF94E0E0183D1F0CD7A68EB7356C8A9FE2C2A2E  mods\zm_xp_hud\mod.json                    378 B

Both equal the repo copy. Seven files: mod.json, lua\zm_xp_hud_post.lua, the five PNGs.

Two facts about the client's mod list, read from cod25\kronos\mods.json (not in launcher_manifest.txt or
launcher_hashes.txt, so it is a client-written config, not a pinned file):

    "xp_hud": false      <- the duplicate operator bar (X4) cannot draw this launch
    (no "zm_xp_hud" key) <- the new mod has no enable entry yet; enable it in KronosLauncher first

## Launch (the user's, not yet done)

Look for, in order:

    [ZmXpHud] v3 loaded: bottom, green
    [ZmXpHud] bar attached at the bottom (images, plain text)
    [ZmXpHud] xp source: dvar
    [ZmXpHud] settings row added to the pause menu
    [ZmXpHud] settings page opened (general)
