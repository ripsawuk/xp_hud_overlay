"""Generate the PNGs xp_hud_overlay_post.lua draws with. Output: mod/images/.

Kronos decodes every PNG in a mod's images/ folder into a material named after the file (no extension), at game
start. v12 look (user, 2026-10-28): a PILL-shaped bar (rounded capsule ends), 1000 px wide, in the colour of the
selected HUD; a soft light behind the label. Nothing is copied from the MW3 reference any more.

  zmhud_track  1004x12  the pill (near-black outline + dark fill), 2 px margin, never resized
  zmhud_cap    4x8      WHITE, left half-pill of the fill   (tinted with the theme accent by the script)
  zmhud_body   8x8      WHITE, the straight middle          (stretched between cap and tip)
  zmhud_tip    4x8      WHITE, right half-pill of the fill
  zmhud_glow   512x64   WHITE soft ellipse, alpha 0 on every border (additive, tinted)

cap/body/tip share ONE smooth vertical gradient (255 -> 222), so the three pieces join without a seam and there is no
hard band or line through the fill.
"""
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).parent / "mod" / "images"
OUT.mkdir(exist_ok=True)
SS = 8
W, H, MARGIN = 1000, 8, 2
R = H // 2          # = the cap / tip width in px


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def pill_mask(size, box):
    m = Image.new("L", (size[0] * SS, size[1] * SS), 0)
    x0, y0, x1, y1 = (v * SS for v in box)
    ImageDraw.Draw(m).rounded_rectangle((x0, y0, x1 - 1, y1 - 1), radius=(y1 - y0) // 2, fill=255)
    return m


def down(m, size):
    return m.resize(size, Image.LANCZOS)


def track():
    size = (W + 2 * MARGIN, H + 2 * MARGIN)
    shape = pill_mask(size, (MARGIN, MARGIN, MARGIN + W, MARGIN + H))
    outline = shape.filter(ImageFilter.MaxFilter(2 * SS + 1))           # grown by 1 px
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    o = Image.new("RGBA", size, (5, 5, 5, 0))
    o.putalpha(down(outline, size).point(lambda v: int(v * 0.85)))
    f = Image.new("RGBA", size, (20, 20, 20, 0))
    f.putalpha(down(shape, size).point(lambda v: int(v * 0.80)))
    img.alpha_composite(o)
    img.alpha_composite(f)
    img.save(OUT / "zmhud_track.png")


def gradient_piece(size, mask):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    px = img.load()
    m = down(mask, size).load()
    for y in range(size[1]):
        v = int(round(255 - 33 * (y / (size[1] - 1))))
        for x in range(size[0]):
            px[x, y] = (v, v, v, m[x, y])
    return img


def cap():
    size = (R, H)
    full = pill_mask((2 * R, H), (0, 0, 2 * R, H))                       # a full-size pill 2R wide = a circle
    left = full.crop((0, 0, R * SS, H * SS))
    gradient_piece(size, left).save(OUT / "zmhud_cap.png")


def tip():
    size = (R, H)
    full = pill_mask((2 * R, H), (0, 0, 2 * R, H))
    right = full.crop((R * SS, 0, 2 * R * SS, H * SS))
    gradient_piece(size, right).save(OUT / "zmhud_tip.png")


def body():
    size = (8, H)
    gradient_piece(size, Image.new("L", (size[0] * SS, size[1] * SS), 255)).save(OUT / "zmhud_body.png")


def glow():
    w, h = 512, 64
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    px = img.load()
    cx, cy = (w - 1) / 2, (h - 1) / 2
    sx, sy = 0.27 * w, 0.30 * h
    for y in range(h):
        for x in range(w):
            g = math.exp(-(((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2))
            taper = smooth(x / (0.14 * w)) * smooth((w - 1 - x) / (0.14 * w)) * smooth(y / (0.22 * h)) * smooth((h - 1 - y) / (0.22 * h))
            px[x, y] = (255, 255, 255, int(round(255 * g * taper)))
    img.save(OUT / "zmhud_glow.png")


# --- bar styles ------------------------------------------------------------------------------------------------
# Each is WHITE with an alpha mask, so the script tints it with the accent. They all live inside the same 8 px fill
# band as cap/body/tip: a style changes the fill's texture, never its geometry.

def white_mask(size, draw):
    big = Image.new("L", (size[0] * SS, size[1] * SS), 0)
    draw(ImageDraw.Draw(big), SS)
    mask = down(big, size)
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    img.putalpha(mask)
    return img




# --- a very small SVG rasteriser --------------------------------------------------------------------------------
# Enough for the two user-supplied bars: groups with translate/rotate, absolute path commands M/L/C/Z, and ellipses.
# It renders a white mask, because the script tints these with the bar's accent.

def _nums(txt):
    return [float(v) for v in txt.replace(",", " ").split()]


def _transform(pts, tx, ty, ang, cx=0.0, cy=0.0):
    import math as _m
    r = _m.radians(ang)
    ca, sa = _m.cos(r), _m.sin(r)
    out = []
    for x, y in pts:
        x, y = x - cx, y - cy
        out.append((cx + tx + x * ca - y * sa, cy + ty + x * sa + y * ca))
    return out


def _path_points(d):
    """Flat polygon list for M/L/C/H/V/Z (absolute; the files only use absolute commands)."""
    toks = d.replace(",", " ").split()
    i, pts, poly, polys = 0, [], [], []
    cmd = None
    cur = (0.0, 0.0)
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in ("Z", "z"):
                if poly:
                    polys.append(poly)
                    poly = []
                continue
            continue
        if cmd in ("M", "L"):
            x, y = float(toks[i]), float(toks[i + 1]); i += 2
            if cmd == "M":
                if poly:
                    polys.append(poly)
                poly = [(x, y)]
                cmd = "L"
            else:
                poly.append((x, y))
        elif cmd == "C":
            x1, y1, x2, y2, x, y = (float(v) for v in toks[i:i + 6]); i += 6
            x0, y0 = poly[-1] if poly else (0.0, 0.0)
            for k in range(1, 9):
                t2 = k / 8.0
                mt = 1 - t2
                poly.append((mt ** 3 * x0 + 3 * mt ** 2 * t2 * x1 + 3 * mt * t2 ** 2 * x2 + t2 ** 3 * x,
                             mt ** 3 * y0 + 3 * mt ** 2 * t2 * y1 + 3 * mt * t2 ** 2 * y2 + t2 ** 3 * y))
        elif cmd == "H":
            x = float(toks[i]); i += 1
            poly.append((x, poly[-1][1]))
        elif cmd == "V":
            y = float(toks[i]); i += 1
            poly.append((poly[-1][0], y))
        else:
            i += 1
    if poly:
        polys.append(poly)
    return polys


def svg_mask(path, size, ss=3):
    """Rasterise the white shape(s) of a small SVG into an alpha mask of `size`."""
    src = Path(path).read_text(encoding="utf-8")
    mask = Image.new("L", (size[0] * ss, size[1] * ss), 0)
    dr = ImageDraw.Draw(mask)
    for g in re.finditer(r'<g\b([^>]*)>(.*?)</g>', src, re.S):
        attrs, body = g.group(1), g.group(2)
        m = re.search(r'transform="([^"]*)"', attrs)
        gtr = m.group(1) if m else ""
        m = re.search(r"translate\(([-0-9.]+)[ ,]+([-0-9.]+)\)", gtr)
        tx, ty = (float(m.group(1)), float(m.group(2))) if m else (0.0, 0.0)
        m = re.search(r"rotate\(([-0-9.]+)", gtr)
        ang = float(m.group(1)) if m else 0.0
        for p in re.finditer(r'<path\b[^>]*?\sd="([^"]*)"', body, re.S):
            for poly in _path_points(p.group(1)):
                pts = _transform([(x * ss, y * ss) for x, y in poly], tx * ss, ty * ss, ang)
                if len(pts) >= 3:
                    dr.polygon(pts, fill=255)
        for e in re.finditer(r'<ellipse\b[^>]*?cx="([-0-9.]+)"[^>]*?cy="([-0-9.]+)"[^>]*?rx="([-0-9.]+)"[^>]*?ry="([-0-9.]+)"[^>]*?(?:transform="rotate\(([-0-9.]+)[ ,]+([-0-9.]+)[ ,]+([-0-9.]+)\)")?', body):
            cx, cy, rx, ry = (float(e.group(i)) for i in range(1, 5))
            rot = float(e.group(5)) if e.group(5) else 0.0
            # sample the ellipse, turn it by its own rotate(), then by the group's translate+rotate
            pts = []
            for k in range(24):
                a = 2 * math.pi * k / 24
                px_, py_ = cx + rx * math.cos(a), cy + ry * math.sin(a)
                pts.append(_transform([(px_, py_)], 0.0, 0.0, rot, cx, cy)[0])
            pts = _transform([(x * ss, y * ss) for x, y in pts], tx * ss, ty * ss, ang)
            dr.polygon(pts, fill=255)
    return mask.resize(size, Image.LANCZOS)



def strips():
    """The user's own bar art. `assets/zmhud_*strip.png` is authored at 4x (4800x64); it is downsampled to the
    bar's exact box, 1200x16, and forced to white so the script can tint it like every other fill asset."""
    src = Path(__file__).parent / "assets"
    for name, out in (("zmhud_pawstrip.png", "zmhud_pawstrip.png"),
                      ("zmhud_dragonstrip.png", "zmhud_dragonstrip.png")):
        f = src / name
        if not f.exists():
            print("strip missing:", f)
            continue
        im = Image.open(f).convert("RGBA").resize((1200, 16), Image.LANCZOS)
        white = Image.new("RGBA", im.size, (255, 255, 255, 0))
        white.putalpha(im.getchannel("A"))
        white.save(OUT / out)


def save_mask(mask_big, size, name):
    mask = mask_big.resize(size, Image.LANCZOS)
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    img.putalpha(mask)
    img.save(OUT / name)


def seg():
    """One slab of the 'divided' (MW2) style: a parallelogram, slanted ends, at the fill's own height (44x6).
    The 6 px over 10 px slope of the old 44x10 slab is kept (4/6), so the ends lean exactly as they did before the
    bar got shorter."""
    size = (44, 6)
    def d(dr, s):
        skew = 4 * s
        dr.polygon([(skew, 0), (44 * s - 1, 0), (44 * s - 1 - skew, 6 * s - 1), (0, 6 * s - 1)], fill=255)
    white_mask(size, d).save(OUT / "zmhud_seg.png")


def stripe():
    """The 'blocks' (loading) style: one thin vertical stripe, 4x5 - the shorter, closer tick the bar uses now."""
    size = (4, 5)
    def d(dr, s):
        dr.rectangle((0, 0, 4 * s - 1, 5 * s - 1), fill=255)
    white_mask(size, d).save(OUT / "zmhud_stripe.png")


def strips():
    """The user's own bar art. `assets/zmhud_*strip.png` is authored at 4x (4800x64); it is downsampled to the
    bar's exact box, 1200x16, and forced to white so the script can tint it like every other fill asset."""
    src = Path(__file__).parent / "assets"
    for name, out in (("zmhud_pawstrip.png", "zmhud_pawstrip.png"),
                      ("zmhud_dragonstrip.png", "zmhud_dragonstrip.png")):
        f = src / name
        if not f.exists():
            print("strip missing:", f)
            continue
        im = Image.open(f).convert("RGBA").resize((1200, 16), Image.LANCZOS)
        white = Image.new("RGBA", im.size, (255, 255, 255, 0))
        white.putalpha(im.getchannel("A"))
        white.save(OUT / out)


def save_mask(mask_big, size, name):
    mask = mask_big.resize(size, Image.LANCZOS)
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    img.putalpha(mask)
    img.save(OUT / name)


def seg():
    """One slab of the 'divided' (MW2) style: a parallelogram, slanted ends, at the fill's own height (44x6).
    The 6 px over 10 px slope of the old 44x10 slab is kept (4/6), so the ends lean exactly as they did before the
    bar got shorter."""
    size = (44, 6)
    def d(dr, s):
        skew = 4 * s
        dr.polygon([(skew, 0), (44 * s - 1, 0), (44 * s - 1 - skew, 6 * s - 1), (0, 6 * s - 1)], fill=255)
    white_mask(size, d).save(OUT / "zmhud_seg.png")


def stripe():
    """The 'blocks' (loading) style: one thin vertical stripe, 4x5 - the shorter, closer tick the bar uses now."""
    size = (4, 5)
    def d(dr, s):
        dr.rectangle((0, 0, 4 * s - 1, 5 * s - 1), fill=255)
    white_mask(size, d).save(OUT / "zmhud_stripe.png")


def tick():
    """The 'divided' separator: 2 px wide, one px taller than the fill on each side."""
    size = (2, H + 2)
    def d(dr, s):
        dr.rectangle((0, 0, 2 * s - 1, (H + 2) * s - 1), fill=255)
    white_mask(size, d).save(OUT / "zmhud_tick.png")


def paw():
    """One paw of the user's cat-paw-trail.svg: the pad blob and FOUR toes, kept at 16x16 so it fits between the
    text row and the bar's edge. Drawn upright for a straight trail."""
    size = (16, 16)
    big = Image.new("L", (size[0] * SS, size[1] * SS), 0)
    dr = ImageDraw.Draw(big)
    S = SS
    dr.rounded_rectangle((4.6 * S, 5.2 * S, 11.4 * S, 12.4 * S), radius=3.0 * S, fill=255)          # pad
    toes = [(-5.6, -1.4, 1.9, 2.3, -28), (-2.2, -4.9, 2.0, 2.5, -10),
            (2.2, -4.9, 2.0, 2.5, 10), (5.6, -1.4, 1.9, 2.3, 28)]
    for cx, cy, rx, ry, ang in toes:
        w, h = rx * S, ry * S
        box = Image.new("L", (int(w * 2) + 2, int(h * 2) + 2), 0)
        ImageDraw.Draw(box).ellipse((1, 1, int(w * 2), int(h * 2)), fill=255)
        box = box.rotate(ang, resample=Image.BICUBIC, expand=False)
        big.paste(box, (int(8 * S + cx * S) - box.width // 2, int(8 * S + cy * S) - box.height // 2), box)
    save_mask(big, size, "zmhud_paw.png")


def scale():
    """One link of the user's dragon-tail.svg chain: a pointed ring with a lattice cross, 16x16, so a row of them
    interlocks into a scaly line."""
    size = (16, 16)
    big = Image.new("L", (size[0] * SS, size[1] * SS), 0)
    dr = ImageDraw.Draw(big)
    S = SS
    outer = [(8, 0.6), (15.4, 8), (8, 15.4), (0.6, 8)]
    dr.polygon([(x * S, y * S) for x, y in outer], outline=255, width=int(3.0 * S))
    dr.line([(4.8 * S, 5.6 * S), (11.2 * S, 12.4 * S)], fill=255, width=int(1.3 * S))
    dr.line([(11.2 * S, 5.6 * S), (4.8 * S, 12.4 * S)], fill=255, width=int(1.3 * S))
    save_mask(big, size, "zmhud_scale.png")


if __name__ == "__main__":
    for p in OUT.glob("*.png"):
        p.unlink()
    track()
    cap()
    body()
    tip()
    glow()
    seg()
    stripe()
    strips()
    for p in sorted(OUT.glob("*.png")):
        im = Image.open(p)
        print(p.name, im.size, p.stat().st_size, "B", "alpha range", im.getchannel("A").getextrema())
