# trace - 2026-11-05 - v9: mouse tabs, Esc, bar switch, 200 px floor

Desk only; v8 is what is installed. Four asks in one build.

| Ask | Change |
|---|---|
| "I should be able to press the mouse to go between General and Appearance tab" | an invisible `LUI.UIButton` over each tab label: `SetFocusable(false)`, `addEventHandler("button_action")` + `registerEventHandler("mousedownleft")` -> `switchTabTo(key)` |
| "Pressing Esc should close this menu, instead of having to press Close manually" | `menu:AddGamepadEventCallback("button_secondary", closeMenu)` |
| "Lets also allow disabling the bar ... just see text ... or just the xp popup" | `CONFIG.showBar` / `CFG.showBar` / `ZMHud.SetBar(on)` and a `Bar: ON` row |
| "Bar Length should be adjustable down to 200px" | `WIDTH_MIN = 200` (was 600) |

## Why the tab buttons are mouse-only and why `SetBar` is not just an alpha

- A focusable button outside the vertical list would take the pad's focus as it moves; `SetFocusable(false)` keeps the
  list as the focus chain while the element still receives mouse events. `LUI.UIButton` enables mouse handling for
  itself (`ui\luibutton.dec.lua:901-902`) and `mousedownleft` on a mouse-enabled element is the client's own pattern
  (`ui\widgets\arrowbuttonlogic.dec.lua:320-339`).
- `setFill` caches by width, so `S.SetBar` resets `bar.fillW` and repaints; `setFill` also refuses to draw while
  `CFG.showBar` is false, so an XP change cannot bring the fill back on its own.

## The 200 px case

A 200 px pill cannot hold the centred label plus a 150 px popup box, so the popup is clamped inside the bar
(`x + 150 <= half`). It is the one length where the popup's x moves; the replay asserts the clamp.

## Appearance now has seven rows

Length, Bar, Text, XP popup, Position, Colour, Close. `ROW_H` 38 and `PANEL_B` 760 keep the window compact
(620x388).

## Replay

    > .\verify.cmd
    264 / 264

New assertions: the Appearance list is `Bar/Text/XP popup/Position/Colour/Close`; the arrow row starts at 200 and
defaults to index 17; each tab has a mouse-only button with a `mousedownleft` handler; clicking a tab closes and
re-opens; Esc closes; `Bar: OFF` hides the pill and the fill, keeps the label, and an XP change cannot restore the
fill; the 200 px floor and its clamp; `Reset` restores the bar and the length.

## Hashes

    mod\lua\zm_xp_hud_post.lua   64,386 B  EDB2ED0997410014159D3DD139DFCA8B1166512D4A4ED25A231D93F9F39A26B0
    mod\mod.json                    378 B  82A51FA4436A8C83F21ED138A027BD0226DF0B70B2648E1F967E1206B1592BAC

## Launch 4 - what to check

1. Click `GENERAL` / `APPEARANCE`: the page re-opens on the clicked tab.
2. Esc closes the page; the `Close` row and the pad's back still work.
3. `Bar: OFF` leaves the text (and `+N XP`) with no pill; `Bar: OFF` + `Text: OFF` leaves only `+N XP`.
4. `Bar length` goes to 200; the text stays centred, the popup slides inside the pill at the smallest sizes.
