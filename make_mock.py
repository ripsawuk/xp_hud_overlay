"""Preview of the operator bar, drawn from the real images and the real HUD-font glyphs (soe_rf_*).

Reads the config and every layout constant out of `mod/lua/xp_hud_overlay_post.lua`, so the picture cannot drift from what
ships. Usage: python make_mock.py out.png

A picture of the intended result, not a screenshot of the game. The glyphs here are the condensed HUD face; the
default face in the game is the engine text face, which reads a little wider.
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops

HERE = Path(__file__).parent
SRC = (HERE / "mod" / "lua" / "xp_hud_overlay_post.lua").read_text(encoding="utf-8")
# The condensed HUD face ships as one PNG per character. Where the client keeps it depends on the install: loose in
# Assets\Images, or inside a HUD pack mod. Any of these answers; with none of them the preview draws the bar alone.
GLYPH_DIRS = (
    Path(r"D:\Games\Shrekinator\Call of Duty\cod25\kronos\Assets\Images"),
    Path(r"D:\Games\Shrekinator\Call of Duty\cod25\kronos\mods\bo3_hud\images"),
)
GLYPHS = next((p for p in GLYPH_DIRS if (p / "soe_rf_76.png").exists()), None)


def num(pat, src=SRC):
    m = re.search(pat, src)
    assert m, pat
    return tuple(int(x) for x in m.groups())


WIDTH = num(r"local WIDTH = (\d+)")[0]
CAPW = num(r"local CAPW = (\d+)")[0]
BAR_NEAR, BAR_FAR = num(r"local BAR_NEAR, BAR_FAR = (\d+), (\d+)")
TRACK_NEAR, TRACK_FAR = num(r"local TRACK_NEAR, TRACK_FAR = (\d+), (\d+)")
LABEL_NEAR, LABEL_FAR = num(r"local LABEL_NEAR, LABEL_FAR = (\d+), (\d+)")
TRACKER_NEAR, TRACKER_FAR = num(r"local TRACKER_NEAR, TRACKER_FAR = (\d+), (\d+)")
GLOW_NEAR, GLOW_FAR = num(r"local GLOW_NEAR, GLOW_FAR = (\d+), (\d+)")
GLOW_GROW, GLOW_PAD = (float(x) for x in re.search(r"local GLOW_GROW, GLOW_PAD = ([0-9.]+), ([0-9.]+)", SRC).groups())
TRACKER_GAP = num(r"local TRACKER_GAP = (\d+)")[0]
# advance widths of the game's condensed face, used only to size text in this picture
ADV = {int(a): float(b) for a, b in re.findall(r"\[(\d+)\] = ([0-9.]+)", ' [32] = 0.1667, [33] = 0.1842, [34] = 0.307, [35] = 0.4298, [36] = 0.3684, [37] = 0.5263, [38] = 0.4912, [39] = 0.1842, [40] = 0.1842, [41] = 0.1842, [42] = 0.2895, [43] = 0.386, [44] = 0.1491, [45] = 0.2281, [46] = 0.1579, [47] = 0.2544, [48] = 0.3684, [49] = 0.2895, [50] = 0.3684, [51] = 0.3684, [52] = 0.3596, [53] = 0.3684, [54] = 0.3684, [55] = 0.3333, [56] = 0.3684, [57] = 0.3684, [58] = 0.1579, [59] = 0.1579, [60] = 0.386, [61] = 0.386, [62] = 0.386, [63] = 0.3246, [64] = 0.4825, [65] = 0.3596, [66] = 0.3684, [67] = 0.3684, [68] = 0.3684, [69] = 0.307, [70] = 0.307, [71] = 0.3684, [72] = 0.3684, [73] = 0.1579, [74] = 0.3246, [75] = 0.3684, [76] = 0.307, [77] = 0.4649, [78] = 0.3684, [79] = 0.3684, [80] = 0.3421, [81] = 0.3684, [82] = 0.3684, [83] = 0.3684, [84] = 0.3246, [85] = 0.3684, [86] = 0.3596, [87] = 0.5351, [88] = 0.3596, [89] = 0.3246, [90] = 0.3333, [91] = 0.2018, [92] = 0.2544, [93] = 0.2368, [94] = 0.2456, [95] = 0.3772, [96] = 0.3246, [97] = 0.3246, [98] = 0.3246, [99] = 0.3246, [100] = 0.3246, [101] = 0.3246, [102] = 0.2281, [103] = 0.3246, [104] = 0.3246, [105] = 0.1491, [106] = 0.1491, [107] = 0.2895, [108] = 0.1491, [109] = 0.4825, [110] = 0.3246, [111] = 0.3246, [112] = 0.3246, [113] = 0.3246, [114] = 0.2193, [115] = 0.3246, [116] = 0.2281, [117] = 0.3246, [118] = 0.307, [119] = 0.4386, [120] = 0.307, [121] = 0.307, [122] = 0.2807, [123] = 0.2105, [124] = 0.1053, [125] = 0.2105, [126] = 0.2719 ')}
PRESETS = {}
for m in re.finditer(r"^\s+(\w+) = \{ accent = (0x[0-9A-Fa-f]+), text = (0x[0-9A-Fa-f]+), glow = (0x[0-9A-Fa-f]+) \}", SRC, re.M):
    _a, _t, _g = (((int(g, 16) >> 16) & 255, (int(g, 16) >> 8) & 255, int(g, 16) & 255) for g in m.groups()[1:])
    PRESETS[m.group(1)] = (_a, _t, (0, 0, 0), _g)      # the engine's own shadow is black


def place(cv, img, l, r, near, far, hc, cx, top, tint=None, alpha=1.0, add=False):
    w, h = max(1, r - l), max(1, far - near)
    im = img.convert("RGBA").resize((w, h), Image.LANCZOS)
    if tint is not None:
        s = Image.new("RGBA", im.size, (*tint, 255))
        s.putalpha(im.getchannel("A"))
        im = s
    a = im.getchannel("A").point(lambda v: int(v * alpha))
    x = cx + l
    y = hc + near if top else hc - far
    if add:
        layer = Image.new("RGB", im.size, (0, 0, 0))
        layer.paste(im.convert("RGB"), (0, 0), a)
        cv.paste(ImageChops.add(cv.crop((x, y, x + w, y + h)).convert("RGB"), layer), (x, y))
    else:
        im.putalpha(a)
        cv.alpha_composite(im, (x, y))


def row(cv, text, l, r, near, far, hc, cx, align, tint, top, offset=0):
    if GLYPHS is None:
        return
    h = far - near
    total = sum(ADV[ord(c)] * h for c in text)
    x = l + offset + ((r - l - total) / 2 if align == 1 else (r - l - total) if align == 2 else 0)
    for c in text:
        a = ADV[ord(c)] * h
        if c != " ":
            place(cv, Image.open(GLYPHS / f"soe_rf_{ord(c)}.png"), int(x), int(x) + max(1, int(a)),
                  near + offset, far + offset, hc, cx, top, tint)
        x += a


def bar(cv, frac, accent, hc, cx, top):
    img = lambda n: Image.open(HERE / "mod" / "images" / f"zmhud_{n}.png")
    L, R = -WIDTH // 2, WIDTH // 2
    place(cv, img("track"), L, R, TRACK_NEAR, TRACK_FAR, hc, cx, top)
    w = round(WIDTH * frac)
    tip = min(CAPW, w // 2)
    cap = min(CAPW, w - tip)
    body = w - tip - cap
    place(cv, img("cap"), L, L + cap, BAR_NEAR, BAR_FAR, hc, cx, top, accent)
    if body > 0:
        place(cv, img("body"), L + cap, L + cap + body, BAR_NEAR, BAR_FAR, hc, cx, top, accent)
    if w >= 3:
        place(cv, img("tip"), L + w - tip, L + w, BAR_NEAR, BAR_FAR, hc, cx, top, accent)


def text_w(text, near, far):
    return sum(ADV[ord(c)] * (far - near) for c in text)


def glow(cv, text, centre_x, tint, hc, cx, top):
    """The soft light behind the label: fitted to the text's width, then pushed inside the bar."""
    tw = text_w(text, LABEL_NEAR, LABEL_FAR)
    half = min(int(tw / 2 * GLOW_GROW + GLOW_PAD + 0.5), WIDTH // 2)
    lo, hi = -WIDTH // 2 + half, WIDTH // 2 - half
    centre_x = max(lo, min(hi, centre_x))
    place(cv, Image.open(HERE / "mod" / "images" / "zmhud_glow.png"), centre_x - half, centre_x + half,
          GLOW_NEAR, GLOW_FAR, hc, cx, top, tint, 0.30, add=True)


def draw(cv, preset, frac, label, gain, hc, cx, top=False, show_text=True):
    accent, text, shadow, glowc = PRESETS[preset]
    L, R = -WIDTH // 2, WIDTH // 2
    if show_text:
        glow(cv, label, 0, glowc, hc, cx, top)
    bar(cv, frac, accent, hc, cx, top)
    if not show_text:
        return
    # The label is centred on the bar and the popup sits immediately right of it, from the label's own width.
    ow = text_w(label, LABEL_NEAR, LABEL_FAR)
    row(cv, label, L, R, LABEL_NEAR, LABEL_FAR, hc, cx, 1, shadow, top, 1)
    row(cv, label, L, R, LABEL_NEAR, LABEL_FAR, hc, cx, 1, text, top)
    if gain:
        gx = int(ow / 2 + TRACKER_GAP)
        row(cv, gain, gx, gx + 150, TRACKER_NEAR, TRACKER_FAR, hc, cx, 0, shadow, top, 1)
        row(cv, gain, gx, gx + 150, TRACKER_NEAR, TRACKER_FAR, hc, cx, 0, accent, top)


def background(w, h, tone):
    bg = Image.new("RGBA", (w, h), tone)
    px = bg.load()
    for y in range(h):
        for x in range(w):
            n = ((x * 37 + y * 91) % 23) - 11
            px[x, y] = (max(0, tone[0] + n), max(0, tone[1] + n // 2), max(0, tone[2] + n // 2), 255)
    return bg


if __name__ == "__main__":
    if "--page" in sys.argv:
        # The settings popup, at true scale on a 1920x1080 frame, from the page constants in the script.
        PANEL_L, PANEL_T, PANEL_R, PANEL_B = num(r"local PANEL_L, PANEL_T, PANEL_R, PANEL_B = (\d+), (\d+), (\d+), (\d+)")
        TAB_L, TAB_TOP, TAB_H, TAB_W, TAB_GAP = num(r"local TAB_L, TAB_TOP, TAB_H, TAB_W, TAB_GAP = (\d+), (\d+), (\d+), (\d+), (\d+)")
        ROW_L, ROW_R, ROW_TOP, ROW_H, ROW_GAP = num(r"local ROW_L, ROW_R, ROW_TOP, ROW_H, ROW_GAP = (\d+), (\d+), (\d+), (\d+), (\d+)")
        TABS = re.findall(r'\{ "(\w+)", "([^"]+)" \}', SRC.split("local TABS = {")[1].split("\n}")[0])
        accent = PRESETS["green"][0]
        rows = ["BAR LENGTH: 1000", "BAR: ON", "COLOUR: GREEN", "LOOK: LINE", "POSITION: BOTTOM", "RESET BAR"]

        from PIL import ImageDraw

        cv = background(1920, 1080, (74, 64, 52))
        cv.alpha_composite(Image.new("RGBA", (1920, 1080), (0, 0, 0, 110)))
        d = ImageDraw.Draw(cv)
        d.rectangle([PANEL_L, PANEL_T, PANEL_R, PANEL_B], fill=(0, 0, 0, 158))
        d.rectangle([PANEL_L, PANEL_T, PANEL_R, PANEL_T + 3], fill=(*accent, 230))
        row(cv, "OPERATOR XP HUD", PANEL_L + 20, PANEL_R - 20, PANEL_T + 12, PANEL_T + 40, 0, 0, 0, (255, 255, 255), True)
        row(cv, "L1 / R1", PANEL_L + 20, PANEL_R - 20, TAB_TOP, TAB_TOP + TAB_H, 0, 0, 2, (154, 154, 154), True)
        for i, (key, name) in enumerate(TABS):
            l = TAB_L + i * (TAB_W + TAB_GAP)
            on = i == 1
            row(cv, name.upper(), l, l + TAB_W, TAB_TOP, TAB_TOP + TAB_H, 0, 0, 0,
                accent if on else (154, 154, 154), True)
            if on:
                d.rectangle([l, TAB_TOP + TAB_H + 2, l + TAB_W, TAB_TOP + TAB_H + 5], fill=(*accent, 230))
        for i, label in enumerate(rows):
            t = ROW_TOP + i * (ROW_H + ROW_GAP)
            d.rectangle([ROW_L, t, ROW_R, t + ROW_H], fill=(38, 42, 47, 220), outline=(74, 79, 85, 255))
            if i == 0:
                # the length row is an arrow control: its title on the left, the value on the right
                row(cv, "BAR LENGTH", ROW_L + 52, ROW_R, t + 7, t + 27, 0, 0, 0, (236, 236, 236), True)
                row(cv, "<   1000   >", ROW_R - 150, ROW_R - 24, t + 7, t + 27, 0, 0, 2, (236, 236, 236), True)
            else:
                row(cv, label, ROW_L + 52, ROW_R, t + 7, t + 27, 0, 0, 0, (236, 236, 236), True)
        out = next((a for a in sys.argv[1:] if not a.startswith("--")), "preview-page.png")
        cv.convert("RGB").save(out)
        print("saved", out, cv.size)
        sys.exit(0)

    if "--styles" in sys.argv:
        # The five bar styles at true scale. A styled bar has no black pill: the style is the bar. Filled pieces take
        # the accent at the style's alpha, the rest a dim tint at its empty alpha.
        order = ["line", "divided", "blocks", "paws", "dragon"]
        pitch = {"divided": 48, "blocks": 7}
        glyph = {"divided": 44, "blocks": 4}
        band = {"divided": (4, 10), "blocks": (5, 10), "paws": (1, 17), "dragon": (1, 17)}
        alpha = {"divided": 0.55, "blocks": 1.0}
        empty = {"divided": 0.22, "blocks": 1.0}
        mat = {"divided": "zmhud_seg", "blocks": "zmhud_stripe"}
        accent, text, shadow, glowc = PRESETS["green"]
        dim = tuple(int(v * 0.30) for v in accent)
        frac = 0.6
        sheet = Image.new("RGB", (1920, 90 * len(order)))
        for k, style in enumerate(order):
            cv = background(1920, 90, (46, 44, 52))
            hc, cx = 90, 960
            w = round(WIDTH * frac)
            if style == "line":
                place(cv, Image.open(HERE / "mod" / "images" / "zmhud_track.png"), -500, 500, TRACK_NEAR, TRACK_FAR, hc, cx, False, tuple(int(v * 0.30) for v in accent))
                tip = min(CAPW, w // 2)
                cap = min(CAPW, w - tip)
                body = w - tip - cap
                place(cv, Image.open(HERE / "mod" / "images" / "zmhud_cap.png"), -500, -500 + cap, BAR_NEAR, BAR_FAR, hc, cx, False, accent)
                if body > 0:
                    place(cv, Image.open(HERE / "mod" / "images" / "zmhud_body.png"), -500 + cap, -500 + cap + body, BAR_NEAR, BAR_FAR, hc, cx, False, accent)
                place(cv, Image.open(HERE / "mod" / "images" / "zmhud_tip.png"), -500 + w - tip, -500 + w, BAR_NEAR, BAR_FAR, hc, cx, False, accent)
            elif style in ("paws", "dragon"):
                n0, n1 = band[style]
                strip = "zmhud_pawstrip.png" if style == "paws" else "zmhud_dragonstrip.png"
                # dim copy over the whole bar, bright copy cropped to the progress - the stencil's behaviour
                img = Image.open(HERE / "mod" / "images" / strip).convert("RGBA")   # 1200x16, drawn 1:1
                w_, h_ = 1200, n1 - n0
                def tinted(im, col, a):
                    lay = Image.new("RGBA", im.size, (*col, 255))
                    lay.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
                    return lay
                cv.alpha_composite(tinted(img.crop((0, 0, min(1200, 1000), h_)), dim, 0.9), (cx - 500, hc - n1))
                cv.alpha_composite(tinted(img.crop((0, 0, max(1, w), h_)), accent, 1.0), (cx - 500, hc - n1))
            else:
                p_, g_ = pitch[style], glyph[style]
                n0, n1 = band[style]
                n = WIDTH // p_
                filled = min(n, round(w / p_))
                for i in range(n):
                    x = -500 + i * p_ + (p_ - g_) // 2
                    place(cv, Image.open(HERE / "mod" / "images" / (mat[style] + ".png")), x, x + g_,
                          n0, n1, hc, cx, False,
                          accent if i < filled else dim,
                          alpha[style] if i < filled else empty[style])
            label = "LVL 47   |   2,800 / 35,500 XP"
            row(cv, label, -500, 500, LABEL_NEAR, LABEL_FAR, hc, cx, 1, shadow, False, 1)
            row(cv, label, -500, 500, LABEL_NEAR, LABEL_FAR, hc, cx, 1, text, False)
            sheet.paste(cv.convert("RGB"), (0, k * 90))
        out = next((a for a in sys.argv[1:] if not a.startswith("--")), "preview-styles.png")
        sheet.save(out)
        print("saved", out, sheet.size)
        sys.exit(0)

    out = sys.argv[1]
    # True scale: a 1920-wide frame, so a 1000 px bar is exactly the share of the screen it is in the game. Each tile
    # is a strip of the bottom of the screen; the bar sits where it sits and the text is the size it is.
    W, Hc = 1920, 96
    tiles = [
        ("green", (70, 58, 46), 0.62, "LVL 2   |   3,177 / 5,000 XP", "+20 XP", False, True),
        ("green", (40, 46, 56), 0.30, "PM   LVL 57   |   2,400 / 8,000 XP", None, False, True),
        ("green", (34, 40, 52), 0.45, "P2   LVL 5   |   2,475 / 5,500 XP", None, True, True),
        ("green", (60, 52, 44), 1.00, "LVL 55   |   MAX", None, False, True),
        ("green", (48, 46, 58), 0.00, "LVL 1   |   0 / 4,500 XP", None, False, True),
    ]
    sheet = Image.new("RGB", (W, Hc * len(tiles)))
    for i, (preset, tone, frac, label, gain, top, text) in enumerate(tiles):
        cv = background(W, Hc, tone)
        draw(cv, preset, frac, label, gain, 0 if top else Hc, W // 2, top, text)
        sheet.paste(cv.convert("RGB"), (0, i * Hc))
    sheet.save(out)
    print("saved", out, sheet.size)
