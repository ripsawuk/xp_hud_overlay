# trace - 2026-11-05 - v12: popup beside the text, glow uncapped, drop with the bar off

v11 ran; six geometry reports. Installed 2026-11-05 (game closed).

| Report | Cause | Fix |
|---|---|---|
| "Background hue doesnt fully follow the text when positioning Left/Right" | `fitGlow` clamped the centre inside the pill, which pushed the light toward the middle near an edge | centre it on the text and let it bleed past the bar's ends |
| "XP popup positioned right leaves a lot of empty space, it should be right beside the XP text" | the popup took the far end of the bar for a differing slot | the popup is always adjacent: right of the text for `right`, left of it for `left`/`center`, flipping when there is no room |
| "positioned Center ... a lot of empty space before XP TEXT starts" | the 150 px box with its text stuck to the left edge | the popup's own text is aligned toward the label (align 2 on the left, 0 on the right), so only the 16 px gap remains |
| "move the text down ... if the bar is disabled" | the 18..39 band exists only to clear the pill | `textDrop()` moves the text and the popup 10 px down when `Bar: OFF` |
| "add an option for Text size on the XP Popup, Auto matches XP Text" | new | `XP Popup > Size: AUTO/11..15`, `S.SetTrackerSize` |

## Replay

    > .\verify.cmd
    258 / 258

The popup now asserts `align 2` (hugging the label) at `-tw/2 - 16 - 150` for LEFT/CENTER and `align 0` at
`tw/2 + 16` for RIGHT; the size row steps AUTO -> 11 and Reset popup restores size, colour and position.

## The storage answer

    storage: FileStorage (table), PlayerData (table), GAMERPROFILE (table), DvarUtils (table)
    FileStorage members: xhash: #x0193258999f89095e:function xhash: #x0469f6d351feeeaab:function

Two hashed members, both functions. Neither hash is in the decompiled UI dump; naming them needs the PNDB database
(`hashes-solved-bo7 (3).cdb`) and a reader that does not exist yet. Persistence stays blocked on that, deliberately:
calling an unnamed engine function is not something to guess at.

## Hashes

    mod\lua\zm_xp_hud_post.lua   78,676 B  DE0A9B9019B6CEC4A1A18C25683D442ED55AC2E778A19FCBC4EE6FD7E581640D
    mod\mod.json                    379 B  71FC685DA42A9C62721E3CBB9AE6FBFD4B43753E098A195A7CDF9629F937BD38

## Launch 6 - what to check

1. XP Text LEFT / RIGHT: the glow sits on the text, not lagging toward the middle.
2. XP Popup LEFT / CENTER / RIGHT: the `+N XP` hugs the text on that side; no far-end gaps, no empty box.
3. `Bar: OFF`: the text and popup drop down; `Bar: ON` puts them back.
4. XP Popup `Size`: AUTO follows the XP Text size; a number sticks.

## v13 - the drop did not happen on the bar switch

The launch showed Bar: OFF hiding the pill but leaving the text in place; it dropped only after a width change, and
Bar: ON did not bring it back. Cause: 	extDrop() is applied where the rows are **placed** (uild, eanchor,
placeTracker, itGlow) and S.SetBar called none of them - only the fill's alpha.

    S.SetBar -> reanchor(bar) + repaint(bar)      # v13

Replay **259 / 259**: toggling Bar moves the label and the popup by +10 on the press, and back on the second press,
measured against the pre-toggle coordinates.

    mod\lua\zm_xp_hud_post.lua   78,649 B  AD45B6B6FE1A738770329745CCCEA26A3DD6F8E9F289A9C6C9E63A6016A4EF91
    mod\mod.json                    379 B  4D476FD988DE55E798FB51630EDC042D4530892B0B7F938EE74C159A57764C49
