# trace - 2026-11-05 - v7: the bar length slider, text pinned

Desk only (v4 is what last ran in the game). Follows `trace\2026-11-05-launch-2-v4.md`.

## The ask

> "I also would like adjustment for maybe a slider of how long the bar is, but the text has to still be pinned in the
> same place it was."

## The geometry decision

The bar was centred: `-WIDTH/2 .. WIDTH/2`. Changing the length there moves **both** ends, and the label is placed at
the left end, so any length change drags the text. v7 fixes the left end and grows the bar to the right:

    local WIDTH = 1000                 -- default
    local WIDTH_MIN, WIDTH_MAX, WIDTH_STEP = 600, 1200, 50
    local BAR_L = -WIDTH / 2           -- -500, fixed
    local LABEL_X = BAR_L              -- the label starts here, always

At 1000 the widget is pixel-identical to v6 (`make_mock.py` still hashes `280BB5A0EB74E01F`). At 800 the pill is
-500..300 and the label, the `+N XP` popup and the soft light keep their x.

## The control

`GenericArrowButton` + `LUI.AddUIArrowTextButtonLogic` - the client's own left/right option row, the same pair
`ui\generated\widgets\frontend\genericbuttonlistflyin.dec.lua:28-40` uses to build an arrow row:

    labels = 600, 650, ... 1200     (13)
    action = function(value) S.SetWidth(600 + (value - 1) * 50) end
    defaultValue = index of the current length

Both calls are inside `pcall`, and a failure falls back to a `genericbutton` row that steps the length and wraps:
`GenericArrowButton` is a *different* widget family from `genericbutton`, and only `genericbutton` is proven in the
match VM (launch 2).

## Replay

    > .\verify.cmd
    253 / 253

The width cases assert the geometry rather than the intent: index 5 gives `geo(track) == [-500, 300]`, the label's and
the popup's x are unchanged, the fill's tip lands at `-500 + round(800 * 221 / 5000)`, index 13 gives `[-500, 700]`,
and `Reset` puts it back to `[-500, 500]`.

## Preview

    python make_mock.py preview-page.png --page

The page mock now draws `BAR LENGTH` with `< 1000 >` on the row, from `PANEL_*` / `ROW_*` in the script.

## Hashes

    mod\lua\zm_xp_hud_post.lua   62,415 B  4F971DF135FEBA602FC3F0FA790617063345EA6868681D0ACEAA4C4A8F8D843A
    mod\mod.json                    378 B  47317BAFC7A60FCAA1A209779F2D00BE71FE21DB4D4B78BD2AFDEDD8A487BDEC

## Launch 3 - what to read

1. `Appearance` opens with `BAR LENGTH  < 1000 >` as an arrow row. Left/right changes the value and the bar's right
   end moves; the label and `+N XP` must not move at all.
2. If the row reads `Bar length: 1000` and only steps when pressed, the arrow widget or its logic is not in the match
   VM - the fallback is doing its job, and that is the report to make.
3. `Text: OFF` then a kill: `+N XP` still appears, at the bar's left end (the v6 fix).
