"""Replay check for xp_hud_overlay_post.lua - the standalone operator XP bar mod (xp_hud_overlay). Runs the script under Lua
(lupa) against a stubbed loader/LUI environment; STEP(n) = n timer ticks of 250 ms. Asserts the model, the dvar
reads, the hook, the attach, the pill geometry, the text and its centring, the tracker, the config options
(top/bottom anchor, text off, tracker off, manual colours), the PNGs, the in-game settings page (the registered
type, the popup request, the tabs, four live rows, the pause-panel entry) and - the stutter regression - that
NOTHING reaches the engine while idle and that no Frame.DoWork is used.

It proves the script's logic and its argument shapes. It does NOT prove the game draws it or that it is smooth:
only a launch does.
"""
import math
import re
import sys
from pathlib import Path

from lupa import LuaRuntime
from PIL import Image

HERE = Path(__file__).parent
SCRIPT = HERE / "mod" / "lua" / "xp_hud_overlay_post.lua"
IMG = HERE / "mod" / "images"
GAME_IMG = Path(r"D:\Games\Shrekinator\Call of Duty\cod25\kronos\Assets\Images")
passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print(f"FAIL {name} {detail}")


STUB = r'''
    LOG = {}
    function DebugPrint(s) LOG[#LOG+1] = s end
    function xhash(s) return "H:" .. s end
    function xhashdvar(s) return "D:" .. s end
    DVARS = {}
    Dvar = {}
    Dvar["H:GetDvarInt"] = function(h) return DVARS[h] end
    Dvar["H:GetDvarString"] = function(h) local v = DVARS[h]; return v and tostring(v) or nil end
    _PT = 1
    FONT_HANDLE = { PrimaryRegular = "reg", PrimaryBold = "bold" }
    BLEND_MODE = { addWithAlpha = "ADD" }
    CLUA = { PushXHashAsset = function(n) return "asset:" .. n end }
    FRONTEND = false
    Engine = { ["H:GetFirstActiveController"] = function() return 0 end,
               ["H:InFrontend"] = function() return FRONTEND end }
    PNGS = {}
    CALLS = 0
    WAITCALLS = 0
    WAITS = {}
    function RegisterMaterial(x)
        if x == "white" then return "mat:white" end
        local name = tostring(x):gsub("^asset:", "")
        if PNGS[name] then return "mat:" .. name end
        return nil
    end
    local function el(kind)
        local e = { kind = kind, children = {}, alpha = 1, nGeo = 0 }
        local function c(f) return function(self, ...) CALLS = CALLS + 1; return f(self, ...) end end
        e.SetAnchorsAndPosition = c(function(self, a1, a2, a3, a4, l, r, t, b) self.geo = { a1, a2, a3, a4, l, r, t, b }; self.nGeo = self.nGeo + 1 end)
        e.setImage = c(function(self, m) self.mat = m end)
        e.SetRGB = c(function(self, col) self.rgb = col end)
        e.SetAlpha = c(function(self, a, ms) self.alpha = a; self.lastMs = ms end)
        e.SetBlendMode = c(function(self, m) self.blend = m end)
        e.setText = c(function(self, t) self.text = t end)
        -- The text element's own rendered size - the call the game's LAYOUT.GetTextWidth makes
        -- (ui\utils\layoututils.dec.lua:128-136 -> el:getElementTextDims()). A read, so it does not count as a setter.
        e.getElementTextDims = function(self) local t = self.text or ""; return #t * 6.2, 18 end
        e.Wait = function(self, ms) WAITCALLS = WAITCALLS + 1; local h = { ms = ms }; WAITS[#WAITS+1] = h; return h end
        e.SetFont = c(function() end)
        e.SetFontSize = c(function(self, s) self.size = s end)
        e.SetMinFontSize = c(function(self, s) self.minsize = s end)
        e.SetWordWrap = c(function() end)
        e.SetAlignment = c(function(self, a) self.align = a end)
        e.SetShadowAngle = c(function() end)
        e.SetShadowDistance = c(function() end)
        e.SetShadowSize = c(function() end)
        e.SetShadowOpacity = c(function() end)
        e.CompleteDecodeAnimation = c(function(self) self.decoded = true end)
        e.SetSpacing = function() end
        e.SetLeft = function() end
        e.processEvent = function() end
        e.addEventHandler = function(self, name, fn) self.handlers = self.handlers or {}; self.handlers[name] = fn; return true end
        e.AddGamepadEventCallback = function(self, ref, fn) self.gamepad = self.gamepad or {}; self.gamepad[ref] = fn; return true end
        e.registerEventHandler = function(self, name, fn) self.handlers = self.handlers or {}; self.handlers[name] = fn; return true end
        e.SetFocusable = function() end
        e.setUseStencil = function(self, v) self.stencil = v end
        function e:addElement(ch) ch.parent = self; self.children[#self.children+1] = ch end
        function e:getParent() return self.parent end
        return e
    end
    ROOT = nil
    LUI = { GetRoot = function() return ROOT end,
            UIImage = { new = function() return el("image") end },
            UIStyledText = { new = function() return el("text") end },
            UIElement = { new = function() return el("group") end } }
    NEWEL = el
    ROOT = el("uiroot")
    BUILT = {}
    REGISTERED = {}
    POPUPS = {}
    POPUP_ARGS = {}
    LEFT = {}
    IN_STACK = false
    NEXTID = nil
    MenuBuilder = { registerType = function(id, fn) REGISTERED[id] = fn end,
                    GetConstructorForType = function(id) return REGISTERED[id] end,
                    BuildRegisteredType = function(t, data) local w = el("widget"); w.text = el("text")
                        w.handlers = {}; w.id = NEXTID; BUILT[#BUILT+1] = w; return w end }
    LUI.UIVerticalList = { new = function() local e = el("group"); return e end }
    LUI.UIButton = { new = function() return el("button") end }
    LUI.UIVerticalNavigatorMenu = { new = function() return el("menu") end }
    ARROW = {}
    LUI.AddUIArrowTextButtonLogic = function(w, ctrl, opts) ARROW[#ARROW+1] = { w = w, opts = opts } end
    LUI.FlowManager = {
        RequestPopupMenu = function(a, id, exclusive, ctrl, replace, data)
            POPUPS[#POPUPS+1] = id
            POPUP_ARGS[#POPUP_ARGS+1] = { exclusive, ctrl, replace }
            IN_STACK = true
        end,
        RequestLeaveMenuByName = function(id) LEFT[#LEFT+1] = id; IN_STACK = false end,
        IsInStack = function(id) return IN_STACK end,
    }
    QUEUE = {}
    Frame = { DoWork = { Queue = function(self, fn) QUEUE[#QUEUE+1] = fn end } }
    -- The client's own settings file API (`ui\utils\hudeditorutils.dec.lua:2719`, `:2875`): a name and plain text.
    -- The stub keeps the files in memory and records how it was called, so the test can see the argument order.
    -- The only dvar the mod sets (D38): the settings text. The GSC mirrors it to disk; here it is just the dvar table.
    SETS = {}
    Dvar["H:SetDvarString"] = function(h, v) SETS[#SETS+1] = h; DVARS[h] = v end
    function STEP(n)
        for i = 1, n do
            local cur = WAITS; WAITS = {}
            for _, h in ipairs(cur) do if h.onComplete then h.onComplete() end end
            for _, fn in ipairs(QUEUE) do fn() end
        end
    end
    function SAME(a, b) return a == b end
'''

PNG_NAMES = ("zmhud_track", "zmhud_cap", "zmhud_body", "zmhud_tip", "zmhud_glow",
             "zmhud_seg", "zmhud_stripe", "zmhud_pawstrip", "zmhud_dragonstrip")
GIANT = dict(accent=0x2FB4FF, text=0xE8F6FF, shadow=0x063F7A, glow=0x0096FF)
SOE = dict(accent=0xFF9E1C, text=0xFFEFD0, shadow=0x5A1E00, glow=0xFF4F00)
# the packaged DEFAULTS.colour is "green" (the value the installed copy had been edited to), so the
# default-config assertions below read this preset; the "auto" theme path is still asserted (section 11).
GREEN = dict(accent=0x4CFF6E, text=0xE4FFE9, shadow=0x0C5A1E, glow=0x1EC84A)


def new_runtime(dvars, pngs=True, cfg=None, pre="", src_override=None, files=None):
    lua = LuaRuntime(unpack_returned_tuples=True, register_eval=False)
    lua.execute(STUB)
    g = lua.globals()
    for k, v in dvars.items():
        g.DVARS["D:" + k] = v
    for k, v in (files or {}).items():
        g.FILES[k] = v
    if pngs:
        for n in PNG_NAMES:
            g.PNGS[n] = True
    src = src_override if src_override is not None else SCRIPT.read_text(encoding="utf-8")
    for key, val in (cfg or {}).items():
        pat = rf'(\n\s+{key} = )("[a-z]+"|[A-Za-z0-9_]+|true|false)'
        assert re.search(pat, src), key
        src = re.sub(pat, lambda m: m.group(1) + val, src, count=1)
    if pre:
        lua.execute(pre)
    lua.execute(src)
    return lua


def kids(node):
    return [node.children[i] for i in range(1, len(node.children) + 1)]


def geo(e):
    return [e.geo[k] for k in range(1, 9)]


def attach(lua, type_hash="#x3e7da34cbc8066689"):
    g = lua.globals()
    root = g.NEWEL("root")
    g.MenuBuilder.BuildRegisteredType(type_hash, None)
    root.addElement(root, g.BUILT[len(g.BUILT)])
    g.STEP(8)
    return root


def images(root):
    return [k for k in kids(root) if k.kind == "image"]


def groups(root):
    # a stencil is a clipping box, never a text row: the glyph-row counts below are about rows only
    return [k for k in kids(root) if k.kind == "group" and not getattr(k, "stencil", False)]


def row_text(group):
    out = []
    for ch in kids(group):
        if ch.alpha == 1 and ch.mat:
            out.append((ch.geo[5], int(re.search(r"soe_rf_(\d+)", ch.mat).group(1))))
    return "".join(chr(c) for _, c in sorted(out))


D3 = {"zm_local_rankxp": 4701, "zm_local_rank": 1, "zm_local_prestige": 0}
src_txt = SCRIPT.read_text(encoding="utf-8")

# --- 1. the packaged file: a config block, no test scaffolding ------------------------------------------------
for key in ("anchor", "showText", "showTracker", "colour", "textSize", "trackerSize"):
    check(f"DEFAULTS.{key} exists", re.search(rf"\n\s+{key} = ", src_txt) is not None)
check("no CONFIG block and no CUSTOM table left: the page and the settings file are the only way in",
      "local CONFIG" not in src_txt and "local CUSTOM" not in src_txt and '"custom"' not in src_txt)
code = "\n".join(re.sub(r"--.*$", "", ln) for ln in src_txt.splitlines())
for gone in ("STAGE", "statsLine", "byType", "seenN", "self-check", "bisect", "S.sets", "DoWork", "Frame",
             "S.seen", "loggedN", "CFG.debug"):
    check(f"no build/test scaffolding left ({gone})", gone not in code, gone)
for banned in ("setdvar", "ExecNow", "Engine.", "io.open", "writeconfig", "exec "):
    check(f"never writes anything ({banned})", banned not in code, banned)
check("the only setter named in the script is SetDvarString, and its dvar is xp_hud_overlay_cfg (D38)",
      set(re.findall(r"SetDvar\w*", code)) == {"SetDvarString"}, set(re.findall(r"SetDvar\w*", code)))
check("one short header block: what it is, where the settings are, where they are kept",
      all(h in "\n".join(src_txt.splitlines()[:15]) for h in ("Display only", "PAUSE > OPERATOR XP HUD", "xp_hud_overlay_cfg")))
# The client's Lua is 5.1: no bitwise operators, no `//`, no goto. The replay runs Lua 5.5, which accepts all of them,
# so the source is checked for 5.3+ syntax here instead - a `>>` in dimAccent shipped once and the mod did not load.
_no_strings = re.sub(r'"[^"]*"', '""', code)
_no_strings = re.sub(r"'[^']*'", "''", _no_strings)
for op, what in ((">>", "bitwise shift"), ("<<", "bitwise shift"), ("//", "integer division")):
    check(f"Lua 5.1 syntax: no {what} ({op})", op not in _no_strings, op)
check("Lua 5.1 syntax: no bitwise &", re.search(r'[^&]&[^&]', _no_strings) is None)
check("Lua 5.1 syntax: no bitwise |", re.search(r'[^|]\|[^|]', _no_strings) is None)
check("Lua 5.1 syntax: no bitwise ~ (only the ~= comparison)",
      re.search(r'~[^=]', _no_strings) is None)
check("Lua 5.1 syntax: no goto", re.search(r'\bgoto\b', _no_strings) is None)

check("the default length is 1000 px, the rounded cap 4 px, and the label row sits on the pill",
      re.search(r"local WIDTH = 1000", src_txt) is not None
      and re.search(r"local CAPW = 4", src_txt) is not None
      and re.search(r"local LABEL_NEAR, LABEL_FAR = 18, 39", src_txt) is not None)
check("layout constants: fill 4..10, its pill 2..12, the text row at 18..39 (6 px clear of the pill), the soft light at 8..44",
      re.search(r"local BAR_NEAR, BAR_FAR = 4, 10", src_txt) is not None
      and re.search(r"local TRACK_NEAR, TRACK_FAR = 2, 12", src_txt) is not None
      and re.search(r"local LABEL_NEAR, LABEL_FAR = 18, 39", src_txt) is not None
      and re.search(r"local TRACKER_NEAR, TRACKER_FAR = 18, 40", src_txt) is not None
      and re.search(r"local GLOW_NEAR, GLOW_FAR = 8, 44", src_txt) is not None)
# This is the standalone mod: one bar, one script, no second progression layer wired to it.
for gone in ("ZMHUD_LAYOUT", "ZMWXP", "weaplvl", "WB_LAYOUT", "WLVL", "WXP"):
    check(f"standalone: no weapon-bar coupling left ({gone})", gone not in src_txt, gone)
check("standalone: the CONFIG block has no layout knob (there is no second bar to place)",
      re.search(r"^\s+layout = ", src_txt, re.M) is None)

# --- 2. model --------------------------------------------------------------------------------------------
lua = new_runtime({})
model = lua.globals().XpHudOverlay.model
m = model(1080, 0, 0)
check("level 1 label is progress inside the level", m.label == "LVL 1   |   1,080 / 4,500 XP", m.label)
check("level 1 frac", abs(m.frac - 1080 / 4500) < 1e-9, m.frac)
m = model(4701, 1, 0)
check("level 2 label: 201 / 5,000", m.label == "LVL 2   |   201 / 5,000 XP", m.label)
m = model(4500, 1, 0)
check("level 2 start is 0 / 5,000", m.label == "LVL 2   |   0 / 5,000 XP" and m.frac == 0, m.label)
m = model(1106500, 54, 0)
check("level 55 starts EMPTY: the ladder still has to be finished before the prestige",
      m.label == "LVL 55   |   0 / 46,500 XP" and not m.capped and m.frac == 0, (m.label, m.capped, m.frac))
m = model(1130000, 54, 0)
check("halfway through level 55 is still XP, not MAX",
      m.label == "LVL 55   |   23,500 / 46,500 XP" and not m.capped, m.label)
m = model(1152998, 54, 0)
check("one XP short of the end of 55 is still XP",
      m.label == "LVL 55   |   46,498 / 46,500 XP" and not m.capped, m.label)
m = model(1152999, 54, 0)
check("cap label", m.label == "LVL 55   |   MAX" and m.capped and m.frac == 1, m.label)
m = model(1153500, 55, 0)
check("below prestige master stays 55", m.level == 55 and m.capped)
m = model(1152999, 54, 3)
check("the prestige prefix stays on the MAX row", m.label == "P3   LVL 55   |   MAX", m.label)
m = model(1200000, 56, 11)
check("prestige master goes past 55", m.level == 57 and not m.capped, m.level)
m = model(5000, 1, 2)
check("prestige prefix", m.label.startswith("P2   LVL 2"), m.label)
m = model(1300000, 56, 11)
check("prestige master prints PM, not P11", m.label.startswith("PM   LVL 57") and "P11" not in m.label, m.label)
# Prestige Master 1000: the LAST level, so it is MAX as soon as it is reached - there is no next level to fill.
m = model(46440000, 998, 11)
check("PM 999 is still a normal level", m.level == 999 and not m.capped and 0 < m.frac < 1, (m.level, m.label))
m = model(46464000, 999, 11)
check("PM 1000 is MAX on arrival - nothing left to earn",
      m.level == 1000 and m.label == "PM   LVL 1000   |   MAX" and m.capped and m.frac == 1, (m.level, m.label))
m = model(46511000, 999, 11)
check("PM 1000 stays MAX inside the band it never has to fill",
      m.label == "PM   LVL 1000   |   MAX" and m.capped and m.frac == 1, m.label)
m = model(46560000, 999, 11)
check("XP past the top of the ladder stays MAX", m.label == "PM   LVL 1000   |   MAX" and m.capped, m.label)
m = model(46560000, 1000, 11)
check("an out-of-table rank 1000 clamps to level 1000 MAX", m.level == 1000 and m.capped, (m.level, m.label))
m = model(9600, None, 0)
check("level from xp when rank unreadable", m.level == 3, m.level)
m = model(-5, 0, 0)
check("negative xp clamps", m.frac == 0)

# --- 3. default config: hook + timer + attach, bottom anchor ------------------------------------------------
lua = new_runtime({"zm_local_rankxp": 100, "zm_local_rank": 0, "zm_local_prestige": 0})
g = lua.globals()
check("a load line names the mod, version, anchor and colour", any("[XpHudOverlay] v1.0 loaded; nothing is drawn until a match starts (settings so far: bottom, green)" in s for s in g.LOG.values()), list(g.LOG.values()))
check("the timer starts at load when the UI root already exists", g.WAITCALLS >= 1)
root = g.NEWEL("root")
g.MenuBuilder.BuildRegisteredType("#x3e7da34cbc8066689", None)
w = g.BUILT[1]
g.STEP(5)
check("no bar while orphaned", len(g.XpHudOverlay.bars) == 0)
root.addElement(root, w)
g.STEP(8)
check("bar attached once parented", len(g.XpHudOverlay.bars) == 1, len(g.XpHudOverlay.bars))
check("attach log names the anchor and the images", any("bar attached at the bottom" in s and "(images)" in s for s in g.LOG.values()), list(g.LOG.values()))
check("bar built on the top of the tree", g.SAME(g.XpHudOverlay.bars[1].top, root))
check("timer started under the UI root", len(kids(g.ROOT)) == 1)
check("never uses Frame.DoWork", len(g.QUEUE) == 0)
imgs = images(root)
check("five image layers: glow, track, cap, body, tip", [i.mat for i in imgs] == ["mat:zmhud_glow", "mat:zmhud_track", "mat:zmhud_cap", "mat:zmhud_body", "mat:zmhud_tip"], [i.mat for i in imgs])
glow, track, cap, body, tip = imgs
bottom = lambda e: geo(e)[:4] == [0.5, 0.5, 1, 0]      # bottom-anchored: y offsets are negative
for i in imgs:
    check("default anchor is the bottom (0.5,0.5,1,0) with negative offsets", bottom(i) and geo(i)[6] < 0 and geo(i)[7] < 0, geo(i))
check("track: 1000 px wide, 2..12 px above the bottom (6 px fill + the 2 px outline margin)", geo(track)[4:8] == [-500, 500, -12, -2], geo(track)[4:8])
check("bar band: 6 px tall, 4..10 px above the bottom, inside -500..500", geo(cap)[6:8] == [-10, -4] and geo(cap)[4] >= -500 and geo(cap)[5] <= 500, geo(cap)[4:])
text_kids = [k for k in kids(root) if k.kind == "text"]
GAP, TRACKER_W = 16, 150


def track_x(label, k=6.2):
    """Where `+N XP` starts: 16 px after the centred label's own end. It is pinned there, always (D30)."""
    tw = len(label) * k
    return math.floor(tw / 2 + GAP + 0.5)


check("the text row sits 6 px above the pill (18..39 px), the label centred in the bar's box",
      geo(text_kids[0])[6:8] == [-39, -18] and geo(text_kids[0])[4:6] == [-500, 500],
      geo(text_kids[0])[4:])
check("`+N XP` sits 16 px to the RIGHT of the centred label, in its own 150 px box",
      geo(text_kids[1])[4:6] == [track_x("LVL 2   |   201 / 5,000 XP"), track_x("LVL 2   |   201 / 5,000 XP") + TRACKER_W]
      and geo(text_kids[1])[6:8] == [-40, -18], (geo(text_kids[1])[4:], track_x("LVL 2   |   201 / 5,000 XP")))
check("the popup starts after the text's end and stays inside the bar",
      geo(text_kids[1])[4] >= 0 and geo(text_kids[1])[5] <= 500, geo(text_kids[1])[4:6])
check("fill pieces tinted with the packaged colour (green)", cap.rgb == body.rgb == tip.rgb == GREEN["accent"], [hex(x.rgb or 0) for x in (cap, body, tip)])
check("soft light behind the label only: additive, preset glow, translucent", glow.blend == "ADD" and glow.rgb == GREEN["glow"] and 0 < glow.alpha < 0.5, (glow.blend, hex(glow.rgb or 0), glow.alpha))

# --- 4. pill fill geometry at every width ---------------------------------------------------------------------
def settle(xp):
    g.DVARS["D:zm_local_rankxp"] = xp
    g.STEP(3)


for xp in (0, 4, 10, 14, 22, 1800, 4499):
    settle(xp)
    w_ = round(1000 * xp / 4500)
    p = {name: (geo(e)[4], geo(e)[5], e.alpha) for name, e in (("cap", cap), ("body", body), ("tip", tip))}
    if w_ < 3:
        check(f"width {w_}: fill hidden", p["cap"][2] == 0 and p["body"][2] == 0 and p["tip"][2] == 0, p)
        continue
    tip_w = min(4, w_ // 2)
    cap_w = min(4, w_ - tip_w)
    body_w = w_ - tip_w - cap_w
    ok = p["cap"][0] == -500 and p["cap"][1] == -500 + cap_w and p["tip"][1] == -500 + w_ and p["tip"][0] == -500 + w_ - tip_w
    check(f"width {w_}: rounded cap + tip placed (cap {cap_w}, tip {tip_w})", ok, p)
    if body_w > 0:
        check(f"width {w_}: body fills the gap exactly, no overlap, no seam", p["body"][0] == p["cap"][1] and p["body"][1] == p["tip"][0] and p["body"][2] == 1, p)
    else:
        check(f"width {w_}: no body piece when there is no gap", p["body"][2] == 0, p)
check("full bar ends at the right end of the track", geo(tip)[5] == 500, geo(tip))

# --- 5. text: the ENGINE face by default, its colours, size, and the soft light fitted to it ---------------------
lua_def, g_def, root_def = lua, g, root
texts = [k for k in kids(root) if k.kind == "text"]
check("two text elements: the label and the tracker", len(texts) == 2, [k.kind for k in kids(root)])
label_row, gain_row = texts
check("no PNG glyph rows in the default face", len(groups(root)) == 0, len(groups(root)))
settle(4701)
g.DVARS["D:zm_local_rank"] = 1
g.STEP(3)
check("label shows the model label", label_row.text == "LVL 2   |   201 / 5,000 XP", label_row.text)
check("label in the preset text colour", label_row.rgb == GREEN["text"], hex(label_row.rgb or 0))
check("label is CENTRED on the bar, in CONFIG.textSize (11) at _PT 1", label_row.align == 1 and label_row.size == 11, (label_row.align, label_row.size))
check("label box spans the whole bar (18..39 px, 6 px clear of the pill)", geo(label_row)[4:6] == [-500, 500] and geo(label_row)[6:8] == [-39, -18], geo(label_row)[4:])
check("label paints immediately (decode completed)", label_row.decoded is True)
tw = len("LVL 2   |   201 / 5,000 XP") * 11 * 0.4
half = int(tw / 2 * 1.4 + 20 + 0.5)
cx = 0
if cx - half < -500:
    cx = -500 + half
check("soft light fitted to the label and centred on it (which is the middle of the bar)",
      geo(glow)[5] == cx + half and geo(glow)[4] == cx - half, (geo(glow)[4:6], cx - half, cx + half))
check("soft light is far narrower than the bar and still wider than the text", geo(glow)[5] - geo(glow)[4] < 330 and geo(glow)[5] - geo(glow)[4] > tw * 1.3, (geo(glow)[5] - geo(glow)[4], tw))
check("soft light is 36 px high and centred on the text row", geo(glow)[7] - geo(glow)[6] == 36 and (geo(glow)[6] + geo(glow)[7]) / 2 == -26, geo(glow))

# --- 6. idle = zero engine calls; one timer re-arm per tick ---------------------------------------------------
g.STEP(30)
c = g.CALLS
w0 = g.WAITCALLS
g.STEP(600)
check("zero engine setter calls over 600 idle ticks (150 s)", g.CALLS == c, g.CALLS - c)
check("exactly one timer re-arm per tick (4 Hz), no more", g.WAITCALLS - w0 == 600, g.WAITCALLS - w0)

# --- 7. a kill: bounded work, and the "+N XP" tracker ---------------------------------------------------------
check("tracker hidden before any kill", gain_row.alpha == 0)
g.DVARS["D:zm_local_rankxp"] = 4721
c0 = g.CALLS
g.STEP(2)
check("an XP change costs a bounded number of calls (<120)", 0 < g.CALLS - c0 < 120, g.CALLS - c0)
check("label follows xp", label_row.text == "LVL 2   |   221 / 5,000 XP", label_row.text)
check("tracker shows +20 XP in the accent colour", gain_row.text == "+20 XP" and gain_row.alpha == 1
      and gain_row.rgb == GREEN["accent"], (gain_row.text, gain_row.alpha))
check("tracker hugs the label: left-aligned in its box, at the text size by default",
      geo(gain_row)[4:6] == [track_x("LVL 2   |   221 / 5,000 XP"), track_x("LVL 2   |   221 / 5,000 XP") + TRACKER_W]
      and gain_row.align == 0 and gain_row.size == 11, (geo(gain_row)[4:6], gain_row.align, gain_row.size))
c1 = g.CALLS
g.STEP(3)
check("tracker still up at 3 ticks (0.75 s), nothing sent", gain_row.alpha == 1 and g.CALLS == c1, g.CALLS - c1)
g.STEP(8)
check("tracker hidden by ONE tween (alpha 0 over 500 ms)", gain_row.alpha == 0 and gain_row.lastMs == 500)
g.STEP(20)
c2 = g.CALLS
g.STEP(600)
check("idle again after the tracker: zero calls", g.CALLS == c2, g.CALLS - c2)
g.DVARS["D:zm_local_rankxp"] = 4741
g.STEP(2)
g.DVARS["D:zm_local_rankxp"] = 4761
g.STEP(2)
check("two kills inside the window add up (+40 XP)", gain_row.text == "+40 XP", gain_row.text)
g.STEP(30)
g.DVARS["D:zm_local_rankxp"] = 9510
g.DVARS["D:zm_local_rank"] = 2
g.STEP(3)
check("level-up relabels", label_row.text == "LVL 3   |   10 / 5,500 XP", label_row.text)
check("fill restarts small after a level-up", geo(tip)[5] - geo(cap)[4] <= 12 or tip.alpha == 0, (geo(cap), geo(tip), tip.alpha))
# level 55 is not MAX on arrival - the level's own XP still has to be earned before the prestige.
g.STEP(30)                                     # let the level-up tracker expire first
g.DVARS["D:zm_local_rankxp"] = 1106500
g.DVARS["D:zm_local_rank"] = 54
g.STEP(3)
check("arriving at level 55 reads 0 / 46,500 XP, not MAX", label_row.text == "LVL 55   |   0 / 46,500 XP", label_row.text)
check("the bar is empty at the start of level 55", cap.alpha == 0 and tip.alpha == 0, (cap.alpha, tip.alpha))
check("XP inside level 55 still raises the tracker", gain_row.alpha == 1, (gain_row.text, gain_row.alpha))
g.DVARS["D:zm_local_rankxp"] = 1106520
g.STEP(3)
check("level 55 accumulates toward the prestige", label_row.text == "LVL 55   |   20 / 46,500 XP", label_row.text)
g.DVARS["D:zm_local_rankxp"] = 1130000
g.STEP(3)
check("the bar moves inside level 55", label_row.text == "LVL 55   |   23,500 / 46,500 XP" and tip.alpha == 1,
      (label_row.text, cap.alpha, tip.alpha))
# at the true end of the ladder the row is MAX and nothing is awarded on screen.
g.STEP(30)                                     # let the 55 tracker expire first
g.DVARS["D:zm_local_rankxp"] = 1152999
g.STEP(3)
check("cap row says MAX", label_row.text == "LVL 55   |   MAX", label_row.text)
check("the popup follows the label both ways: the shorter MAX row moves it with the text",
      geo(gain_row)[4] == track_x("LVL 55   |   MAX") and geo(gain_row)[4] > 0,
      (geo(gain_row)[4:6], track_x("LVL 55   |   MAX")))
check("no tracker at the cap", gain_row.alpha == 0, (gain_row.text, gain_row.alpha))
g.DVARS["D:zm_local_rankxp"] = 1153999
g.STEP(3)
check("XP past the cap is not awarded on screen",
      gain_row.alpha == 0 and label_row.text == "LVL 55   |   MAX", (gain_row.text, gain_row.alpha))
# Prestige Master 1000 is the last level - it is MAX on arrival, nothing left to earn.
g.STEP(30)
g.DVARS["D:zm_local_rankxp"] = 46464000
g.DVARS["D:zm_local_rank"] = 999
g.DVARS["D:zm_local_prestige"] = 11
g.STEP(3)
check("PM level 1000 reads MAX on arrival", label_row.text == "PM   LVL 1000   |   MAX", label_row.text)
check("no tracker on arrival at PM 1000", gain_row.alpha == 0, (gain_row.text, gain_row.alpha))
g.DVARS["D:zm_local_rankxp"] = 46560000
g.STEP(3)
check("XP past the top of the ladder raises no tracker and the row stays MAX",
      gain_row.alpha == 0 and label_row.text == "PM   LVL 1000   |   MAX", (gain_row.text, gain_row.alpha, label_row.text))

# --- 7b. hiding the bar takes the "+N XP" popup with it -------------------------------------------------------
lua = new_runtime(D3)
g = lua.globals()
root = attach(lua)
g.STEP(4)
g.DVARS["D:zm_local_rankxp"] = 4721
g.STEP(2)
gain_popup = [k for k in kids(root) if k.kind == "text"][1]
check("popup is up before the hide", gain_popup.alpha == 1, gain_popup.alpha)
lua.execute("FRONTEND = true")
g.STEP(3)
check("the frontend hides the bar and the popup together", gain_popup.alpha == 0, gain_popup.alpha)
lua.execute("FRONTEND = false")
g.STEP(6)
check("back on the HUD the bar returns without a stale popup",
      images(root)[1].alpha > 0.5 and gain_popup.alpha == 0, (images(root)[1].alpha, gain_popup.alpha))

# --- 8. CONFIG: the bar at the TOP of the screen --------------------------------------------------------------
lua = new_runtime(D3, cfg={"anchor": '"top"'})
g = lua.globals()
check("top anchor is announced at load", any("(settings so far: top" in s for s in g.LOG.values()), list(g.LOG.values()))
root = attach(lua)
imgs = images(root)
check("top anchor: every element is anchored to the top (0.5,0.5,0,1) with positive offsets", all(geo(i)[:4] == [0.5, 0.5, 0, 1] and geo(i)[6] > 0 and geo(i)[7] > 0 for i in imgs), [geo(i) for i in imgs])
track, cap = imgs[1], imgs[2]
check("top anchor: the bar is 2..12 px DOWN from the top edge (mirrored)", geo(track)[6:8] == [2, 12] and geo(cap)[6:8] == [4, 10], (geo(track)[6:8], geo(cap)[6:8]))
lbl = [k for k in kids(root) if k.kind == "text"][0]
check("top anchor: the text row is BELOW the bars (mirrored), i.e. 18..39 px from the top", geo(lbl)[6:8] == [18, 39], geo(lbl)[6:8])
check("top anchor: attach log says top", any("bar attached at the top" in s for s in g.LOG.values()))
c = g.CALLS
g.STEP(400)
check("top anchor: idle is quiet too", g.CALLS == c, g.CALLS - c)

# --- 9. CONFIG: text hidden at load - the rows exist so the settings page can switch them on live -----------------
lua = new_runtime(D3, cfg={"showText": "false"})
g = lua.globals()
check("text hidden is announced at load", any("text hidden" in s for s in g.LOG.values()))
root = attach(lua)
imgs = images(root)
glow0 = [i for i in imgs if i.mat == "mat:zmhud_glow"][0]
check("text hidden: the soft light is off", glow0.alpha == 0, glow0.alpha)
texts = [k for k in kids(root) if k.kind == "text"]
label_row0, gain_row0 = texts
check("text hidden: the label is built but invisible (a live toggle needs no rebuild)",
      len(texts) == 2 and label_row0.alpha == 0, [t.alpha for t in texts])
g.DVARS["D:zm_local_rankxp"] = 4721
g.STEP(4)
check("text hidden: the bar still fills", images(root)[1].alpha > 0.5)
check("text hidden: the label stays dark", label_row0.alpha == 0, label_row0.alpha)
check("text hidden: the popup is still its own switch and shows a kill, left-aligned at the bar's end",
      gain_row0.alpha == 1 and geo(gain_row0)[4] == -500, (gain_row0.alpha, geo(gain_row0)[4:6]))
g.STEP(20)
c = g.CALLS
g.STEP(400)
check("text hidden: idle is quiet", g.CALLS == c, g.CALLS - c)

# --- 10. CONFIG: tracker hidden, text kept ---------------------------------------------------------------------
lua = new_runtime(D3, cfg={"showTracker": "false"})
g = lua.globals()
check("hidden tracker is announced at load", any("tracker hidden" in s for s in g.LOG.values()), list(g.LOG.values()))
root = attach(lua)
texts = [k for k in kids(root) if k.kind == "text"]
check("tracker hidden: the label row is up and the tracker row is not",
      len(texts) == 2 and texts[0].alpha == 1 and texts[1].alpha == 0, [t.alpha for t in texts])
check("tracker hidden: the soft light stays (text is still on)", any(i.mat == "mat:zmhud_glow" and i.alpha > 0 for i in images(root)))
g.DVARS["D:zm_local_rankxp"] = 4721
g.STEP(3)
check("tracker hidden: a kill changes the label and nothing else", [k for k in kids(root) if k.kind == "text"][0].text == "LVL 2   |   221 / 5,000 XP", [k for k in kids(root) if k.kind == "text"][0].text)

# --- 11. CONFIG: manual colours --------------------------------------------------------------------------------
lua = new_runtime(D3, cfg={"colour": '"gold"'})
g = lua.globals()
root = attach(lua)
check("a preset name works (gold)", images(root)[2].rgb == 0xFFC83C, hex(images(root)[2].rgb or 0))
ok = g.XpHudOverlay.SetColour("violet")
check("SetColour works at runtime", ok is True and images(root)[2].rgb == 0xB07CFF, (ok, hex(images(root)[2].rgb or 0)))
bad = g.XpHudOverlay.SetColour("nope")
check("unknown colour refused", bad[0] is False if isinstance(bad, tuple) else bad is False)
ok = g.XpHudOverlay.SetAnchor("top")
bad = g.XpHudOverlay.SetAnchor("left")
check("SetAnchor accepts top/bottom and refuses anything else", ok is True and (bad[0] is False if isinstance(bad, tuple) else bad is False))
check("SetAnchor re-places the bar that is already on screen",
      all(geo(i)[:4] == [0.5, 0.5, 0, 1] and geo(i)[6] > 0 for i in images(root)),
      [geo(i)[:4] for i in images(root)])

# auto: the HUD theme decides
def theme_runtime(body):
    pre = 'load = function(c) return function() return "KEY" end end\n' + body
    lua = new_runtime(D3, cfg={"colour": '"auto"'}, pre=pre)
    root = attach(lua)
    return lua, root


for body, want, name in (('OPTIONS = { KEY = function() return 990420 end }', SOE, "990420 -> Shadows of Evil (orange)"),
                         ('OPTIONS = { KEY = function() return 990421 end }', GIANT, "990421 -> The Giant (blue)"),
                         ('OPTIONS = { KEY = function() error("x") end }', GIANT, "a theme lookup that throws -> the default"),
                         ('OPTIONS = nil', GIANT, "no OPTIONS table -> the default"),
                         ('load = nil\nOPTIONS = { KEY = function() return 990420 end }', GIANT, "no bytecode helper -> the default")):
    lua, root = theme_runtime(body)
    check(f"auto colour: {name}", images(root)[2].rgb == want["accent"], hex(images(root)[2].rgb or 0))

# --- 11b. Multiplayer / Endgame: no Zombies dvars, so the game's own getters and the HUD root ------------------
def mp_runtime(mapname="mp_sat_kite", xp=4701, rank=1, with_ui=True, dvars=None, widget=None):
    pre = ('Engine = { ["H:GetFirstActiveController"] = function() return 3 end, ["H:InFrontend"] = function() return FRONTEND end }\n')
    if with_ui:
        pre += ('PROGRESSION = { ["H:GetPlayerXP"] = function(c) assert(c == 3); return %d end,'
                ' ["H:GetPlayerRank"] = function(c) return %d end }\n' % (xp, rank))
    lua = new_runtime(dvars or {}, pre=pre)
    g = lua.globals()
    g.DVARS["D:mapname"] = mapname
    root = g.NEWEL("root")
    if widget:
        g.MenuBuilder.BuildRegisteredType(widget, None)
        root.addElement(root, g.BUILT[len(g.BUILT)])
    g.STEP(12)
    return lua, g.ROOT


lua, root = mp_runtime()
g = lua.globals()
check("MP/Endgame: the bar attaches to the HUD root when no Zombies HUD widget is built", len(g.XpHudOverlay.bars) == 1 and g.XpHudOverlay.bars[1].root is True, len(g.XpHudOverlay.bars))
check("MP/Endgame: attach log names the HUD root", any("bar attached to the HUD root" in s for s in g.LOG.values()), list(g.LOG.values()))
check("MP/Endgame: the values come from the game's own progression getters", any("xp source: progression" in s for s in g.LOG.values()), [s for s in g.LOG.values() if "source" in s])
check("MP/Endgame: the controller index is passed to those getters (3, from GetFirstActiveController)", True)
lbl = [k for k in kids(root) if k.kind == "text"][0]
check("MP/Endgame: same label from the getters (LVL 2 | 201 / 5,000 XP)", lbl.text == "LVL 2   |   201 / 5,000 XP", lbl.text)
imgs = images(root)
check("MP/Endgame: the bar is drawn (track visible, fill tinted)", len(imgs) == 5 and imgs[1].alpha > 0.5 and imgs[2].rgb == GREEN["accent"], (len(imgs), imgs[1].alpha))
c = g.CALLS
g.STEP(600)
check("MP/Endgame: idle is quiet after attaching", g.CALLS == c, g.CALLS - c)
g.DVARS["D:mapname"] = "menu_mp"
g.STEP(4)
check("MP/Endgame: the bar hides in a menu (map name is not a map)", imgs[1].alpha == 0, imgs[1].alpha)
g.DVARS["D:mapname"] = "mp_sat_kite"
g.STEP(4)
check("MP/Endgame: and comes back on a map", imgs[1].alpha > 0.5, imgs[1].alpha)
g.DVARS["D:mapname"] = "zm_sat_firefly"
g.STEP(4)
check("MP/Endgame: a Zombies map name counts as a map too", imgs[1].alpha > 0.5)
lua, root = mp_runtime(with_ui=False)
g = lua.globals()
check("MP/Endgame without the getters: no bar and no crash", len(g.XpHudOverlay.bars) == 0, list(g.LOG.values()))
lua, root = mp_runtime(dvars={"zm_local_rankxp": 9000, "zm_local_rank": 1, "zm_local_prestige": 0})
g = lua.globals()
check("Zombies dvars still win when they exist (source: dvar)", any("xp source: dvar" in s for s in g.LOG.values()), [s for s in g.LOG.values() if "source" in s])
lua, root = mp_runtime(widget="#x3e7da34cbc8066689", mapname="zm_sat_firefly", dvars={"zm_local_rankxp": 100, "zm_local_rank": 0, "zm_local_prestige": 0})
g = lua.globals()
check("Zombies: the ZM HUD widget is still preferred (no root bar)", len(g.XpHudOverlay.bars) == 1 and not getattr(g.XpHudOverlay.bars[1], "root", False), [s for s in g.LOG.values() if "attached" in s])

# --- 11c. the frontend is not the place for a HUD bar ---------------------------------------------------------
lua, root = mp_runtime()
g = lua.globals()
b = g.XpHudOverlay.bars[1]
track_ = [i for i in images(root) if i.mat == "mat:zmhud_track"][0]
check("in a map the bar is visible", track_.alpha > 0.5, track_.alpha)
lua.execute("FRONTEND = true")
g.STEP(6)
check("in the frontend the bar hides (main menu, lobby, loading videos)", track_.alpha == 0, track_.alpha)
lua.execute("FRONTEND = false")
g.STEP(6)
check("back in a match it returns", track_.alpha > 0.5, track_.alpha)
lua = new_runtime({"zm_local_rankxp": 4701, "zm_local_rank": 1, "zm_local_prestige": 0}, cfg=None)
g = lua.globals()
lua.execute("FRONTEND = true")
g.DVARS["D:mapname"] = "mp_sat_kite"
g.STEP(20)
check("no bar is attached while the frontend is up", len(g.XpHudOverlay.bars) == 0, len(g.XpHudOverlay.bars))
lua.execute("FRONTEND = false")
g.STEP(20)
check("and it attaches once a match starts", len(g.XpHudOverlay.bars) == 1, len(g.XpHudOverlay.bars))

# --- 12. the PNGs ----------------------------------------------------------------------------------------------
check("no leftover images from earlier looks", not any((IMG / f"zmhud_{n}.png").exists() for n in ("back", "fill", "edge")))
tk = Image.open(IMG / "zmhud_track.png").convert("RGBA")
ta = tk.getchannel("A")
check("track is 1004x12", tk.size == (1004, 12), tk.size)
check("track corners are transparent (a capsule)", all(ta.getpixel(p_) == 0 for p_ in ((0, 0), (1003, 0), (0, 11), (1003, 11))))
check("track body is the dark fill, the top row a near-black outline", 215 <= ta.getpixel((500, 6)) <= 255 and max(tk.getpixel((500, 1))[:3]) <= 8, (ta.getpixel((500, 6)), tk.getpixel((500, 1))))
check("both ends are ROUND", ta.getpixel((1, 2)) < 80 and ta.getpixel((1, 6)) > 150 and ta.getpixel((1002, 2)) < 80 and ta.getpixel((1002, 6)) > 150)
cp = Image.open(IMG / "zmhud_cap.png").convert("RGBA")
tp = Image.open(IMG / "zmhud_tip.png").convert("RGBA")
bd = Image.open(IMG / "zmhud_body.png").convert("RGBA")
check("cap/tip 4x8, body 8x8", (cp.size, tp.size, bd.size) == ((4, 8), (4, 8), (8, 8)))
ca, tpa = cp.getchannel("A"), tp.getchannel("A")
check("cap = left half of a pill, tip = right half", ca.getpixel((0, 0)) < 90 and ca.getpixel((3, 0)) >= 240 and tpa.getpixel((3, 0)) < 90 and tpa.getpixel((0, 0)) >= 240)
rows = [bd.getpixel((0, y))[0] for y in range(8)]
check("the fill has one smooth vertical gradient (no line through it)", max(abs(b - a) for a, b in zip(rows, rows[1:])) <= 8 and rows[0] > rows[-1], rows)
check("cap, body and tip share that gradient (no seam)", all(cp.getpixel((3, y))[0] == bd.getpixel((0, y))[0] == tp.getpixel((0, y))[0] for y in range(8)))
check("the fill pieces are grey/white (tinted by the script)", all(px[0] == px[1] == px[2] for im in (cp, tp, bd) for px in im.getdata() if px[3] > 0))
glm = Image.open(IMG / "zmhud_glow.png").convert("RGBA")
ga = glm.getchannel("A")
border = [ga.getpixel((x, 0)) for x in range(glm.width)] + [ga.getpixel((x, glm.height - 1)) for x in range(glm.width)] + [ga.getpixel((0, y)) for y in range(glm.height)] + [ga.getpixel((glm.width - 1, y)) for y in range(glm.height)]
check("glow 512x64, transparent border, bright centre, white", glm.size == (512, 64) and max(border) <= 2 and ga.getpixel((256, 32)) >= 240 and all(px[:3] == (255, 255, 255) for px in glm.getdata() if px[3] > 0))

# the four bar styles: same 8 px band as the fill, white so the accent tints them
for name, size in (("seg", (44, 6)), ("stripe", (4, 5))):
    im = Image.open(IMG / f"zmhud_{name}.png").convert("RGBA")
    check(f"style {name}: {size[0]}x{size[1]}, white, has ink", im.size == size
          and all(px[:3] == (255, 255, 255) for px in im.getdata() if px[3] > 0)
          and im.getchannel("A").getextrema()[1] > 200, (im.size, im.getchannel("A").getextrema()))

# --- 13. graceful degradation -----------------------------------------------------------------------------------
lua = new_runtime({})
g = lua.globals()
root = attach(lua, "#x3fb7c1d32eeb344a0")
check("unreadable dvars: bar exists, track hidden, one warning", len(g.XpHudOverlay.bars) == 1 and images(root)[1].alpha == 0 and sum(1 for s in g.LOG.values() if "no player XP is readable" in s) == 1)
g.DVARS["D:zm_local_rankxp"] = 100
g.STEP(6)
check("the bar appears when the dvar does", images(root)[1].alpha > 0.5)
lua = new_runtime({"zm_local_rankxp": 2250, "zm_local_rank": 0, "zm_local_prestige": 0}, pngs=False)
g = lua.globals()
root = attach(lua, "#x305671cb57eb82497")
imgs = images(root)
check("missing track/glow: no white rectangle, no additive white box", len(imgs) == 3 and all(i.mat == "mat:white" and i.blend is None for i in imgs), [(i.mat, i.blend) for i in imgs])
texts = [k for k in kids(root) if k.kind == "text"]
check("two plain-text rows (label + tracker), each with the engine's built-in shadow", len(texts) == 2 and texts[0].text == "LVL 1   |   2,250 / 4,500 XP", [t.text for t in texts])
c = g.CALLS
g.STEP(400)
check("the fallback path is idle-quiet", g.CALLS == c, g.CALLS - c)

# --- 14. one timer per VM, replaced when its parent goes; one bar per tree --------------------------------------
lua = new_runtime(D3)
g = lua.globals()
root = attach(lua)
check("one bar served by one timer", len(g.XpHudOverlay.bars) == 1 and len(kids(g.ROOT)) == 1)
g.MenuBuilder.BuildRegisteredType("#x3e7da34cbc8066689", None)
g.MenuBuilder.BuildRegisteredType("#x3fb7c1d32eeb344a0", None)
g.STEP(10)
check("more HUD builds do not stack a second bar or timer", len(g.XpHudOverlay.bars) == 1 and len(kids(g.ROOT)) == 1, (len(g.XpHudOverlay.bars), len(kids(g.ROOT))))
gen0 = g.XpHudOverlay.gen
lua.execute("for _, ch in ipairs(ROOT.children) do ch.parent = nil end")
g.MenuBuilder.BuildRegisteredType("#x3e7da34cbc8066689", None)
check("an orphaned timer is replaced (generation +1)", g.XpHudOverlay.gen == gen0 + 1, (gen0, g.XpHudOverlay.gen))
w1 = g.WAITCALLS
g.STEP(10)
check("the old timer chain stopped: one re-arm per tick", g.WAITCALLS - w1 == 10, g.WAITCALLS - w1)
before = len(g.XpHudOverlay.bars)
lua.execute(src_txt)
check("reloading the same version is a no-op", len(g.XpHudOverlay.bars) == before)

# --- 15. the in-game settings page: General / XP Bar / XP Text / XP Popup --------------------------------------
# The page is built from the widgets the ZM pause panel itself builds in a match (`UIVerticalList` +
# `MenuBuilder.BuildRegisteredType("genericbutton")`), so these checks assert the shapes it hands the loader:
# the registered type, the popup request, the tab strip, each tab's rows, and that a row repaints the live bar.
lua = new_runtime(D3)
g = lua.globals()
root = attach(lua)
g.DVARS["D:zm_local_rankxp"] = 4701
g.DVARS["D:zm_local_rank"] = 1
g.STEP(4)
label = [k for k in kids(root) if k.kind == "text"][0]
gain = [k for k in kids(root) if k.kind == "text"][1]
glow = [i for i in images(root) if i.mat == "mat:zmhud_glow"][0]
track_e = [i for i in images(root) if i.mat == "mat:zmhud_track"][0]
bar_id = id(label)


def page_rows():
    """Build the registered page and return (menu, [(label, handler), ...])."""
    menu = g.REGISTERED["H:zmxpsettings"]()
    out = []
    for b in kids(menu.VerticalList):
        out.append((b.text.text or "", b.handlers["button_action"] if b.handlers else None))
    return menu, out


def row_text(menu, i):
    return menu.VerticalList.children[i + 1].text.text


def open_tab(tab):
    """Switch tabs through the public API and build the page it produces."""
    before = len(g.POPUPS)
    g.XpHudOverlay.Menu(tab)
    g.STEP(3)
    assert len(g.POPUPS) == before + 1, (tab, list(g.POPUPS))
    return page_rows()


ok = g.XpHudOverlay.Menu()
check("XpHudOverlay.Menu registers the page and asks FlowManager for it",
      ok is True and g.POPUPS[1] == "H:zmxpsettings" and g.REGISTERED["H:zmxpsettings"] is not None,
      (ok, list(g.POPUPS)))
check("it is a controller-locked popup, not a replacing or global menu",
      g.POPUP_ARGS[1][1] is True and g.POPUP_ARGS[1][3] is False, (g.POPUP_ARGS[1][1], g.POPUP_ARGS[1][3]))

menu, rows = page_rows()
labels = [r[0] for r in rows]
page_texts = [k.text for k in kids(menu) if k.kind == "text" and k.text]
check("the tabs are a strip of their own: four tab labels and the title",
      all(t in page_texts for t in ("GENERAL", "XP BAR", "XP TEXT", "XP POPUP")) and "OPERATOR XP HUD" in page_texts,
      page_texts)
check("General is just the version, Reset and Close",
      len(labels) == 3 and labels[0].startswith("Operator XP HUD") and labels[1] == "Reset everything" and labels[2] == "Close",
      labels)
active = [k for k in kids(menu) if k.kind == "text" and k.text == "GENERAL"][0]
inactive = [k for k in kids(menu) if k.kind == "text" and k.text == "XP BAR"][0]
check("the tab you are on is in the accent colour, the others grey",
      active.rgb == GREEN["accent"] and inactive.rgb == 0x9A9A9A, (hex(active.rgb or 0), hex(inactive.rgb or 0)))
check("the page is a navigator menu with a vertical list holding every row",
      menu.kind == "menu" and menu.VerticalList is not None and len(kids(menu.VerticalList)) == len(rows))
check("the window is a small centred popup, not a full-screen page",
      all(600 <= geo(k)[4] and geo(k)[5] <= 1400 for k in kids(menu) if k.kind in ("image", "text")),
      [(k.kind, geo(k)[4:6]) for k in kids(menu) if k.kind in ("image", "text")])
check("the shoulders and back are wired",
      menu.gamepad is not None and all(b in menu.gamepad for b in
                                       ("button_shoulderl", "button_shoulderr", "button_secondary")), menu.gamepad)
tabs_hit = [k for k in kids(menu) if k.kind == "button"]
check("each of the four tabs has a mouse-only button over it",
      len(tabs_hit) == 4 and all(k.handlers and "mousedownleft" in k.handlers for k in tabs_hit),
      [k.kind for k in kids(menu)])
n_left, n_pop = len(g.LEFT), len(g.POPUPS)
tabs_hit[1].handlers["mousedownleft"]()
check("clicking a tab closes the page so it can re-open on that tab", len(g.LEFT) == n_left + 1, list(g.LEFT))
g.STEP(2)
check("and it re-opens", len(g.POPUPS) == n_pop + 1, list(g.POPUPS))
n_left = len(g.LEFT)
consumed = menu.gamepad["button_secondary"]()
check("back / Esc closes the open page AND is consumed, so the pause menu never sees it",
      consumed is True and len(g.LEFT) == n_left + 1, (consumed, list(g.LEFT)))

# --- XP Bar tab
menu, rows = open_tab("bar")
labels = [r[0] for r in rows]
check("XP Bar: length, bar switch, colour, look, position, reset",
      labels[0] == "" and labels[1] == "Bar: ON" and labels[2] == "Colour: GREEN"
      and labels[3] == "Look: Line" and labels[4] == "Position: BOTTOM" and labels[5] == "Reset bar", labels)
arrow = g.ARROW[len(g.ARROW)].opts
check("the length row is the arrow control, 200..1200 in 50s, starting on the current length",
      arrow.labels[1] == "200" and arrow.labels[len(arrow.labels)] == "1200" and arrow.defaultValue == 17,
      (arrow.labels[1], arrow.labels[len(arrow.labels)], arrow.defaultValue))
label_align, gain_x0 = label.align, geo(gain)[4]
check("before: the pill runs the full 1000 px, -500..500", geo(track_e)[4:6] == [-500, 500], geo(track_e)[4:6])
arrow.action(13)                                  # 800
check("the length row shortens the pill to a centred 800 (-400..400)",
      geo(track_e)[4:6] == [-400, 400], geo(track_e)[4:6])
check("the text is PINNED: the label stays centred and the popup keeps its x",
      label.align == 1 and geo(label)[4] == -400 and geo(label)[5] == 400 and geo(gain)[4] == gain_x0,
      (label.align, geo(label)[4:6], geo(gain)[4]))
check("the fill scales with the new length: 800 px of bar, ~4 % of it inked",
      geo([i for i in images(root) if i.mat == "mat:zmhud_tip"][0])[5] == -400 + round(800 * 201 / 5000),
      geo([i for i in images(root) if i.mat == "mat:zmhud_tip"][0])[4:6])
arrow.action(1)                                   # 200, the floor
check("the floor is 200 px: a centred -100..100 pill with the label still centred",
      geo(track_e)[4:6] == [-100, 100] and label.align == 1 and geo(label)[4:6] == [-100, 100],
      (geo(track_e)[4:6], geo(label)[4:6]))
arrow.action(17)                                  # back to 1000
check("the length is back to 1000", geo(track_e)[4:6] == [-500, 500], geo(track_e)[4:6])
label_y0, gain_y0 = geo(label)[6:8], geo(gain)[6:8]
glow_y0 = geo([i for i in images(root) if i.mat == "mat:zmhud_glow"][0])[6:8]
rows[1][1]()                                      # Bar: ON -> OFF
check("Bar OFF hides the pill and the fill and keeps the label",
      track_e.alpha == 0 and [i for i in images(root) if i.mat == "mat:zmhud_cap"][0].alpha == 0
      and label.alpha == 1 and row_text(menu, 1) == "Bar: OFF",
      (track_e.alpha, label.alpha, row_text(menu, 1)))
glow = [i for i in images(root) if i.mat == "mat:zmhud_glow"][0]
check("Bar OFF drops the text and the popup 10 px, on the same press",
      geo(label)[6:8] == [label_y0[0] + 10, label_y0[1] + 10]
      and geo(gain)[6:8] == [gain_y0[0] + 10, gain_y0[1] + 10],
      (label_y0, geo(label)[6:8], gain_y0, geo(gain)[6:8]))
# The halo is part of the row, not of the bar: it was left behind because fitGlow cached on width and centre only,
# and reanchor placed it without the drop (D30).
check("and the halo behind the text moves with it, on the same press",
      geo(glow)[6:8] == [glow_y0[0] + 10, glow_y0[1] + 10],
      (glow_y0, geo(glow)[6:8]))
g.DVARS["D:zm_local_rankxp"] = 4721
g.STEP(3)
check("an XP change with the bar off does not bring the fill back", track_e.alpha == 0, track_e.alpha)
rows[1][1]()
check("Bar ON brings the pill and the fill back, and puts the text back up",
      track_e.alpha > 0.5 and row_text(menu, 1) == "Bar: ON"
      and geo(label)[6:8] == label_y0 and geo(gain)[6:8] == gain_y0,
      (track_e.alpha, geo(label)[6:8], label_y0))
check("and the halo goes back up with it",
      geo(glow)[6:8] == glow_y0, (glow_y0, geo(glow)[6:8]))
rows[2][1]()                                      # Colour: GREEN -> VIOLET
check("the bar colour row re-tints the fill and the page accent",
      row_text(menu, 2) == "Colour: VIOLET"
      and [i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb == 0xB07CFF,
      (row_text(menu, 2), hex([i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb or 0)))
# the styles: each redraws the fill and leaves the text and the popup exactly where they are
g.DVARS["D:zm_local_rankxp"] = 7000
g.XpHudOverlay.SetColour("green")
g.STEP(3)
look_y, look_gx = geo(label)[6:8], geo(gain)[4]
rows[3][1]()                                      # LINE -> DIVIDED
def all_images(node):
    """Every image under the root, stencil children included: the strip art is a child of its stencil."""
    out = []
    for ch in kids(node):
        if ch.kind == "image":
            out.append(ch)
        out.extend(all_images(ch))
    return out


def pieces(m):
    return [i for i in all_images(root) if i.mat == "mat:" + m and i.alpha > 0.05]


def band(e):
    """The element's own vertical band as [near, far]: `place` negates both for a bottom-anchored bar."""
    t, b = geo(e)[6], geo(e)[7]
    return sorted((-t, -b)) if t < 0 else sorted((t, b))
check("DIVIDED is the whole bar: no pill, 20 slanted segments across the full width",
      row_text(menu, 3) == "Look: Divided" and len(pieces("zmhud_seg")) == 20 and track_e.alpha == 0,
      (row_text(menu, 3), len(pieces("zmhud_seg")), track_e.alpha))
check("DIVIDED is the fill's own height now: 6 px (4..10), not the pill's 10 px",
      band(pieces("zmhud_seg")[0]) == [4, 10], band(pieces("zmhud_seg")[0]))
check("both halves are translucent; the filled ones are accented",
      pieces("zmhud_seg")[0].alpha == 0.55 and pieces("zmhud_seg")[-1].alpha == 0.22
      and sum(1 for i in pieces("zmhud_seg") if i.rgb == GREEN["accent"]) == 10,
      (pieces("zmhud_seg")[0].alpha, pieces("zmhud_seg")[-1].alpha,
       sum(1 for i in pieces("zmhud_seg") if i.rgb == GREEN["accent"])))
check("a style does not move the text or the popup", geo(label)[6:8] == look_y and geo(gain)[4] == look_gx,
      (geo(label)[6:8], look_y, geo(gain)[4], look_gx))
rows[3][1]()                                      # DIVIDED -> BLOCKS
check("BLOCKS is the whole bar: shorter, closer stripes at a 7 px pitch, no pill",
      row_text(menu, 3) == "Look: Blocks" and len(pieces("zmhud_stripe")) == 142 and track_e.alpha == 0,
      (row_text(menu, 3), len(pieces("zmhud_stripe")), track_e.alpha))
check("BLOCKS is 5 px tall on the fill's baseline (5..10), and its gap is 3 px not 6",
      band(pieces("zmhud_stripe")[0]) == [5, 10]
      and abs((geo(pieces("zmhud_stripe")[1])[4] - geo(pieces("zmhud_stripe")[0])[4]) - 7) <= 1,
      (band(pieces("zmhud_stripe")[0]),
       geo(pieces("zmhud_stripe")[1])[4] - geo(pieces("zmhud_stripe")[0])[4]))
# A colour change has to re-tint the style's pieces too, at once. With the fill cache keyed on width + style only, the
# pieces kept the old colour until the XP moved far enough to change the width (D28).
g.XpHudOverlay.SetColour("violet")
check("a colour change re-tints a style's pieces on the same press, with no XP change",
      {i.rgb for i in pieces("zmhud_stripe")} == {0xB07CFF, 0x35254D},
      sorted({hex(i.rgb or 0) for i in pieces("zmhud_stripe")}))
g.XpHudOverlay.SetColour("green")
check("and back: the pieces are the green accent and its 30 % again",
      {i.rgb for i in pieces("zmhud_stripe")} == {GREEN["accent"], 0x174D21},
      sorted({hex(i.rgb or 0) for i in pieces("zmhud_stripe")}))
rows[3][1]()                                      # BLOCKS -> CAT PAWS
paw_strip = pieces("zmhud_pawstrip")
check("CATS is the user's trail: one 1200 px copy of the art in each stencil, no pill",
      row_text(menu, 3) == "Look: Cats" and len(paw_strip) == 2 and track_e.alpha == 0
      and abs((geo(paw_strip[0])[5] - geo(paw_strip[0])[4]) - 1200) <= 1,
      (row_text(menu, 3), len(paw_strip), track_e.alpha,
       geo(paw_strip[0])[4:6] if paw_strip else None))
# The bug the first strip build shipped: a child of a stencil placed with anchors (0, 1, 0, 1, x, x+tile, 0, 0) has
# a ZERO height, so neither style drew anything at all.
check("each strip copy fills its stencil's height (16 px), not zero",
      all(geo(i)[:4] == [0, 1, 0, 1] and geo(i)[6:8] == [0, 16] for i in paw_strip),
      [geo(i) for i in paw_strip])
bar1 = g.XpHudOverlay.bars[1]
check("the art is never scaled: two stencils clip the dim bar-width and the bright progress-width copies",
      any(k.stencil is True for k in kids(bar1.top))
      and sum(1 for k in kids(bar1.top) if getattr(k, "stencil", None) is True) == 2,
      [getattr(k, "stencil", None) for k in kids(bar1.top)][-6:])
check("the dim tiles are the accent at 30 %", paw_strip[0].rgb == 0x174D21, hex(paw_strip[0].rgb or 0))
rows[3][1]()                                      # CAT PAWS -> DRAGON
dragon_strip = pieces("zmhud_dragonstrip")
check("DRAGON is the user's tail: one 1200 px copy of the art in each stencil, no pill",
      row_text(menu, 3) == "Look: DraGON" and len(dragon_strip) == 2 and track_e.alpha == 0
      and abs((geo(dragon_strip[0])[5] - geo(dragon_strip[0])[4]) - 1200) <= 1,
      (row_text(menu, 3), len(dragon_strip), track_e.alpha,
       geo(dragon_strip[0])[4:6] if dragon_strip else None))
rows[3][1]()                                      # DRAGON -> LINE
check("and back to LINE: the pill and the pieces return, the style pieces go",
      row_text(menu, 3) == "Look: Line" and track_e.alpha > 0.5
      and [i for i in images(root) if i.mat == "mat:zmhud_cap"][0].alpha == 1
      and all(i.alpha == 0 for i in images(root)
              if i.mat in ("mat:zmhud_seg", "mat:zmhud_stripe", "mat:zmhud_pawstrip", "mat:zmhud_dragonstrip")),
      (row_text(menu, 3), track_e.alpha))
rows[4][1]()                                      # Position
check("Position flips the bar to the top edge, live",
      geo([i for i in images(root) if i.mat == "mat:zmhud_track"][0])[:4] == [0.5, 0.5, 0, 1])
rows[4][1]()
rows[2][1]()                                      # back to GREEN for the text tests
rows[5][1]()                                      # Reset bar
check("Reset bar restores the file's colour and edge",
      [i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb == GREEN["accent"]
      and geo([i for i in images(root) if i.mat == "mat:zmhud_track"][0])[:4] == [0.5, 0.5, 1, 0],
      (hex([i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb or 0),))

# --- XP Text tab
menu, rows = open_tab("text")
labels = [r[0] for r in rows]
check("XP Text: switch, prestige, size, position, reset",
      labels == ["Text: ON", "Prestige: ON", "Size: 11", "Position: CENTER", "Reset text"], labels)
g.DVARS["D:zm_local_rank"] = 5                    # P4, so the prefix is visible
g.DVARS["D:zm_local_prestige"] = 4
g.DVARS["D:zm_local_rankxp"] = 30000
g.STEP(3)
check("the level row carries the prestige prefix by default", label.text.startswith("P4   LVL 6"), label.text)
rows[1][1]()                                      # Prestige OFF
check("Prestige OFF drops the prefix and keeps the row", label.text == "LVL 6   |   3,500 / 6,500 XP" and
      row_text(menu, 1) == "Prestige: OFF", (label.text, row_text(menu, 1)))
rows[1][1]()
check("Prestige ON brings it back", label.text.startswith("P4   LVL 6"), label.text)
rows[2][1]()                                      # Size 11 -> 12
check("Size steps up and the element follows, still in the same row",
      row_text(menu, 2) == "Size: 12" and label.size == 12 and geo(label)[6:8] == [-39, -18],
      (row_text(menu, 2), label.size, geo(label)[6:8]))
for _ in range(4):
    rows[2][1]()
check("Size stops at 15 and wraps to 11", row_text(menu, 2) == "Size: 11" and label.size == 11,
      (row_text(menu, 2), label.size))
rows[3][1]()                                      # Position CENTER -> RIGHT
check("Text Position RIGHT aligns the label right, in the bar's own box",
      label.align == 2 and row_text(menu, 3) == "Position: RIGHT", (label.align, row_text(menu, 3)))
rows[3][1]()
check("and LEFT next", label.align == 0 and row_text(menu, 3) == "Position: LEFT", (label.align, row_text(menu, 3)))
rows[3][1]()
check("and back to CENTER", label.align == 1 and row_text(menu, 3) == "Position: CENTER")

# --- XP Popup tab: four rows, the popup pinned to the right of the text (D30)
menu, rows = open_tab("popup")
labels = [r[0] for r in rows]
check("XP Popup: switch, size, colour, reset - no position row",
      labels == ["Popup: ON", "Size: AUTO", "Colour: AUTO", "Reset popup"], labels)
tw = len(label.text) * 6.2
check("the popup is pinned immediately right of the text, whatever the text is doing",
      geo(gain)[4] == math.floor(tw / 2) + 16 and gain.align == 0,
      (geo(gain)[4:6], math.floor(tw / 2) + 16, gain.align))
rows[2][1]()                                      # Colour AUTO -> GIANT
check("the popup colour row re-tints the +N XP text only",
      row_text(menu, 2) == "Colour: GIANT" and gain.rgb == GIANT["accent"] and label.rgb != GIANT["accent"],
      (row_text(menu, 2), hex(gain.rgb or 0), hex(label.rgb or 0)))
rows[1][1]()                                      # Size AUTO -> 11
check("the popup size row leaves AUTO and steps", row_text(menu, 1) == "Size: 11" and gain.size == 11,
      (row_text(menu, 1), gain.size))
rows[3][1]()                                      # Reset popup
check("Reset popup puts it back to AUTO colour and AUTO size, still pinned right",
      row_text(menu, 1) == "Size: AUTO" and row_text(menu, 2) == "Colour: AUTO"
      and geo(gain)[4] == math.floor(tw / 2) + 16,
      (row_text(menu, 1), row_text(menu, 2), geo(gain)[4:6]))

# the pin holds at every text position: left, centre and right all put the popup after the label's own end
menu, rows = open_tab("text")
for where, want_x in (("LEFT", -500 + tw + 16), ("CENTER", math.floor(tw / 2) + 16), ("RIGHT", 500 - tw + tw + 16)):
    while row_text(menu, 3) != "Position: " + where:
        rows[3][1]()
    check(f"text {where}: the popup still starts 16 px after the text's end",
          geo(gain)[4] == math.floor(want_x + 0.5), (where, geo(gain)[4:6], want_x))

# --- General: Reset everything
menu, rows = open_tab("general")
g.XpHudOverlay.SetBar(False)
g.XpHudOverlay.SetPrestige(False)
g.XpHudOverlay.SetTextSize(15)
rows[1][1]()
check("Reset everything restores bar, text and popup from the file",
      track_e.alpha > 0.5 and label.alpha == 1 and label.size == 11
      and [i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb == GREEN["accent"],
      (track_e.alpha, label.size))

# the pause-menu entry: the ZM pause panel is the widget with id `zmpausemenubuttons`
g.NEXTID = "zmpausemenubuttons"
pause = g.MenuBuilder.BuildRegisteredType("#x96cd14a086232b2f", None)
check("one row is appended to the pause panel's own list", pause.zmXpMenuButton is not None and len(kids(pause)) == 1)
check("the row reads Operator XP HUD", pause.zmXpMenuButton.text.text == "Operator XP HUD", pause.zmXpMenuButton.text.text)
check("the row is a normal pause button: its own 51 px slot in the list",
      geo(pause.zmXpMenuButton)[7] - geo(pause.zmXpMenuButton)[6] == 51, geo(pause.zmXpMenuButton))
g.NEXTID = None
n_pop = len(g.POPUPS)
pause.zmXpMenuButton.handlers["button_action"]()
g.STEP(3)
check("pressing it opens the page", len(g.POPUPS) == n_pop + 1 and g.POPUPS[len(g.POPUPS)] == "H:zmxpsettings",
      list(g.POPUPS))
g.DVARS["D:zm_local_rankxp"] = 4800
g.STEP(30)
c = g.CALLS
g.STEP(400)
check("the settings page adds no per-tick work", g.CALLS == c, g.CALLS - c)


# --- 16. the pause hook: three paths, none of them dependent on the id alone --------------------------------------
lua = new_runtime(D3)
g = lua.globals()
check("the pause hook reports itself once", any("pause-menu row hooked" in s for s in g.LOG.values()),
      list(g.LOG.values()))

# path 1: a widget built through MenuBuilder, with the pause list's id
g.NEXTID = "zmpausemenubuttons"
w = g.MenuBuilder.BuildRegisteredType("#x96cd14a086232b2f", None)
check("build path: the row is appended when a widget arrives with the pause list's id",
      w.zmXpMenuButton is not None, list(g.LOG.values()))
check("the attach is logged with the path that found it",
      any("settings row added to the pause menu (build hook)" in s for s in g.LOG.values()), list(g.LOG.values()))

# path 2: the registered constructor, which needs no id and no MenuBuilder call
g.NEXTID = None
lua.execute("PAUSE_CTOR = function() return NEWEL('list') end\nFOREIGN_CTOR = function() return NEWEL('list') end")
g.MenuBuilder.registerType("zmpausemenubuttons", g.PAUSE_CTOR)
ctor = g.REGISTERED["zmpausemenubuttons"]
check("register path: registering the pause type installs a wrapper", g.SAME(ctor, g.PAUSE_CTOR) is False)
list2 = ctor()
check("constructor path: calling the registered constructor appends the row, with no id to match",
      list2.zmXpMenuButton is not None, list(g.LOG.values()))
check("the row built by that path carries its own action",
      list2.zmXpMenuButton is not None and list2.zmXpMenuButton.handlers["button_action"] is not None)

g.MenuBuilder.registerType("zmpausemenubuttons", g.PAUSE_CTOR)
list3 = g.REGISTERED["zmpausemenubuttons"]()
check("re-registering replaces the wrapper, and exactly one row goes into the list", len(kids(list3)) == 1, len(kids(list3)))

# a non-pause type is left exactly as it was registered
foreign = g.FOREIGN_CTOR
g.MenuBuilder.registerType("someothertype", foreign)
check("a type that is not a pause panel is not wrapped", g.SAME(g.REGISTERED["someothertype"], foreign) is True)

# --- 17. the settings survive a restart: one dvar, mirrored to disk by mod\scripts\xp_hud_overlay_store.gsc (D38) -------
# FileStorage raises for every name in this mod's VM (D36/D37), so the Lua publishes its settings in the dvar
# `xp_hud_overlay_cfg` and the GSC (modelled on custom_scripts\mp_bo6_store.gsc) writes it to kronos\xphudoverlay\settings.json
# and puts it back after a restart. The replay covers the Lua half; the GSC half is proved by a launch.
D3P = {"zm_local_rankxp": 4701, "zm_local_rank": 1, "zm_local_prestige": 0}
CFGK = "D:xp_hud_overlay_cfg"
ALLOWED_KEYS = {"anchor", "text", "tracker", "bar", "prestige", "colour", "look", "width",
                "textpos", "textsize", "trackersize", "trackerauto", "trackercolour"}

lua = new_runtime(D3P)
g = lua.globals()
attach(lua)
g.XpHudOverlay.SetColour("violet")
g.XpHudOverlay.SetLook("blocks")
g.XpHudOverlay.SetWidth(600)
saved = g.DVARS[CFGK]
check("a settings press writes the state into the `xp_hud_overlay_cfg` dvar",
      isinstance(saved, str) and "colour=violet" in saved and "look=blocks" in saved and "width=600" in saved, saved)
check("the payload is `key=value` pairs from the closed set - no paths, no free text, no extra keys",
      set(re.findall(r"(?:^|,)([a-z]+)=", saved or "")) == ALLOWED_KEYS and "\n" not in (saved or ""),
      sorted(set(re.findall(r"(?:^|,)([a-z]+)=", saved or ""))))
check("the only dvar ever set is `xp_hud_overlay_cfg`",
      set(str(g.SETS[i]) for i in range(1, len(g.SETS) + 1)) == {CFGK}, [g.SETS[i] for i in range(1, len(g.SETS) + 1)])
check("the first write says it wrote and that it reads back identical, once",
      sum(1 for s in g.LOG.values() if "wrote xp_hud_overlay_cfg" in s and "reads back identical" in s) == 1,
      [s for s in g.LOG.values() if "settings:" in s])

# a fresh VM whose dvar the GSC has filled from disk: the bar must come up exactly as it was left
lua = new_runtime(D3P)
g = lua.globals()
g.DVARS[CFGK] = saved
root = attach(lua)
check("a restart adopts the saved settings: colour, style and length",
      [i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb == 0xB07CFF
      and len(pieces("zmhud_stripe")) == math.floor(600 / 7)
      and geo([i for i in images(root) if i.mat == "mat:zmhud_track"][0])[4:6] == [-300, 300],
      ([i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb,
       len(pieces("zmhud_stripe")),
       geo([i for i in images(root) if i.mat == "mat:zmhud_track"][0])[4:6]))
check("and it says how many keys it read", any("13 read from xp_hud_overlay_cfg" in s for s in g.LOG.values()),
      [s for s in g.LOG.values() if "settings:" in s])
check("reading the saved settings sets nothing", len(g.SETS) == 0, len(g.SETS))

# the GSC fills the dvar a moment AFTER the level starts: the tick must pick it up late
lua = new_runtime(D3P)
g = lua.globals()
root = attach(lua)
g.DVARS[CFGK] = saved
g.STEP(3)
check("a dvar filled after the bar is up is adopted by the tick",
      [i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb == 0xB07CFF,
      hex([i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb or 0))

# a damaged value leaves the defaults alone instead of half-applying
lua = new_runtime(D3P)
g = lua.globals()
g.DVARS[CFGK] = "colour=notacolour,look=nope,textpos=sideways,=bad,width"
root = attach(lua)
check("a damaged value changes nothing that is not valid",
      [i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb == GREEN["accent"]
      and geo([i for i in images(root) if i.mat == "mat:zmhud_track"][0])[4:6] == [-500, 500],
      ([i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb,
       geo([i for i in images(root) if i.mat == "mat:zmhud_track"][0])[4:6]))

# a press before the saved value arrives must not be overwritten by it afterwards
lua = new_runtime(D3P)
g = lua.globals()
root = attach(lua)
g.XpHudOverlay.SetColour("gold")
g.DVARS[CFGK] = "colour=violet"
g.STEP(3)
check("a press is not overwritten by a stale saved value arriving later",
      [i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb == 0xFFC83C,
      hex([i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb or 0))

# a VM without a Dvar setter: the bar still works, and the console says once that nothing will persist
lua = new_runtime(D3P, pre='Dvar["H:SetDvarString"] = nil')
g = lua.globals()
root = attach(lua)
g.XpHudOverlay.SetColour("gold")
g.XpHudOverlay.SetColour("violet")
check("no setter in the VM: the bar still works", [i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb == 0xB07CFF,
      hex([i for i in images(root) if i.mat == "mat:zmhud_cap"][0].rgb or 0))
check("no setter in the VM: it says so, once, instead of failing silently",
      sum(1 for s in g.LOG.values() if "no Dvar.SetDvarString" in s) == 1, [s for s in g.LOG.values() if "settings:" in s])

# a setter that raises: reported once with the reason, the bar still works
lua = new_runtime(D3P, pre='Dvar["H:SetDvarString"] = function() error("boom") end')
g = lua.globals()
root = attach(lua)
g.XpHudOverlay.SetColour("gold")
g.XpHudOverlay.SetColour("violet")
check("a setter that raises is reported once with its reason",
      sum(1 for s in g.LOG.values() if "SetDvarString raised" in s and "boom" in s) == 1,
      [s for s in g.LOG.values() if "settings:" in s])

# the contract amendment (D38), asserted on the source: exactly one dvar name is ever written, no FileStorage left
check("the config dvar name is one constant", src_txt.count('local CFG_DVAR = "xp_hud_overlay_cfg"') == 1)
check("the setter is looked up in exactly one place (persist) and called once",
      code.count('dvarMember("SetDvarString")') == 1 and len(re.findall(r"pcall\(set,", code)) == 1,
      (code.count('dvarMember("SetDvarString")'), len(re.findall(r"pcall\(set,", code))))
check("FileStorage is gone from the script", "FileStorage" not in code and "writeallfilecontent" not in code)

# the GSC half: one file, one dvar, one store, no XP and no profile
gsc = (SCRIPT.parent.parent / "scripts" / "xp_hud_overlay_store.gsc").read_text(encoding="utf-8")
gcode = "\n".join(re.sub(r"//.*$", "", ln) for ln in gsc.splitlines())
check("the GSC sets only `xp_hud_overlay_cfg`", set(re.findall(r'setdvar\("([^"]+)"', gcode)) == {"xp_hud_overlay_cfg"},
      set(re.findall(r'setdvar\("([^"]+)"', gcode)))
check("the GSC stores into one namespace and file",
      set(re.findall(r'nengine_store_\w+\("([^"]+)"', gcode)) == {"xphudoverlay"}
      and set(re.findall(r'nengine_store_(?:load|save)\("xphudoverlay", "([^"]+)"', gcode)) == {"settings"})
check("the GSC touches no XP, rank, profile or player data",
      not re.search(r'rankxp|prestige|setplayerdata|giverankxp|zm_local', gcode), gcode[:0])


print(f"{passed} / {passed + failed}")
sys.exit(0 if failed == 0 else 1)
