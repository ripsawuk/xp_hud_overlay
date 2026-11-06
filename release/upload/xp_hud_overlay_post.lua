-- XP HUD Overlay - the operator level and XP bar for BO7 Zombies, Multiplayer and Endgame on Kronos.
--
--   P5   LVL 7   |   1,200 / 8,000 XP     +20 XP
--   =========================================================----
--
-- Display only: it reads the level Kronos already tracks and draws it. It awards no XP and writes no profile value.
-- Zombies reads the dvars zm_local_rankxp / zm_local_rank / zm_local_prestige; Multiplayer and Endgame read
-- PROGRESSION.GetPlayerXP / GetPlayerRank.
--
-- Settings: PAUSE > OPERATOR XP HUD (or XpHudOverlay.Menu()). They are kept in the dvar xp_hud_overlay_cfg, which
-- scripts\xp_hud_overlay_store.gsc mirrors to kronos\xphudoverlay\settings.json. Deleting that file restores DEFAULTS.
-- Run only one copy of this bar: two scripts drawing it is two bars.

local WIDTH = 1000                              -- the starting length; DEFAULTS.width and the page's slider change it

-- What a fresh install starts with. Every value here has a row in the in-game page, and the saved settings file wins
-- over it from the next launch on. A per-tab Reset puts its own group back to these.
local DEFAULTS = {
  anchor = "bottom",          -- "bottom" or "top" edge of the screen
  showText = true,            -- the level row and the light behind it
  showTracker = true,         -- the "+N XP" popup
  showBar = true,             -- the bar itself: pill or style
  showPrestige = true,        -- the "P3" / "PM" prefix on the level row
  textPos = "center",         -- the level row inside the bar: "left", "center", "right"
  textSize = 11,              -- engine font points
  trackerColour = "auto",     -- "auto" follows the bar, or a preset name
  trackerAuto = true,         -- the popup's own size follows the level row
  trackerSize = 13,           -- ... unless trackerAuto is false
  look = "line",              -- "line", "divided", "blocks", "paws", "dragon"
  colour = "green",           -- "auto", or a preset name
  width = 1000,               -- 1920x1080 units, 200..1200
}

-- ---------------------------------------------------------------------------------------------------------
-- Presets: accent = bar fill + "+N XP"; text = label; glow = soft light behind the label.
-- "giant" and "soe" are the colours of Kronos's two HUD themes.
local PRESETS = {
  giant = { accent = 0x2FB4FF, text = 0xE8F6FF, glow = 0x0096FF },
  soe = { accent = 0xFF9E1C, text = 0xFFEFD0, glow = 0xFF4F00 },
  blue = { accent = 0x2FB4FF, text = 0xD6F1FF, glow = 0x0096FF },
  cyan = { accent = 0x30FCF5, text = 0xE8FFFE, glow = 0x00C8C0 },
  ice = { accent = 0x9ED8FF, text = 0xFFFFFF, glow = 0x5AB4FF },
  gold = { accent = 0xFFC83C, text = 0xFFF3D0, glow = 0xFFA000 },
  red = { accent = 0xFF4A4A, text = 0xFFE3E3, glow = 0xFF1E1E },
  green = { accent = 0x4CFF6E, text = 0xE4FFE9, glow = 0x1EC84A },
  violet = { accent = 0xB07CFF, text = 0xF0E6FF, glow = 0x7A3CFF },
}
local AUTO_DEFAULT = "giant"      -- used when the HUD theme cannot be read

-- Geometry, in 1920x1080 units. Each NEAR/FAR pair is a distance from the chosen screen edge, so `anchor = "top"`
-- mirrors the whole widget. The bar is centred on the screen and the label is centred on the bar.
local WIDTH_MIN, WIDTH_MAX, WIDTH_STEP = 200, 1200, 50
local CAPW = 4
local BAR_NEAR, BAR_FAR = 4, 10                 -- the fill
local TRACK_NEAR, TRACK_FAR = 2, 12             -- the pill behind it, with a 2 px outline margin
local LABEL_NEAR, LABEL_FAR = 18, 39            -- the text row, starting 6 px above the pill
local TRACKER_NEAR, TRACKER_FAR = 18, 40        -- the "+N XP" popup, bottom-aligned with the text row
local GLOW_NEAR, GLOW_FAR = 8, 44               -- the soft light behind the label
local GLOW_GROW, GLOW_PAD = 1.4, 20             -- its half-width = text width / 2 * GLOW_GROW + GLOW_PAD
local TEXT_MIN, TEXT_MAX = 11, 15               -- the level text's size range, in engine points

-- Bar styles. Each draws only inside the fill band, so the text and the popup never move.
local LOOKS = {
  { "line", "Line" },
  { "divided", "Divided" },
  { "blocks", "Blocks" },
  { "paws", "Cats" },
  { "dragon", "DraGON" },
}
local LOOK_PITCH = { divided = 48, blocks = 7 }
local LOOK_GLYPH = { divided = 44, blocks = 4 }
-- each style's vertical band (same units as above); all of it stays below the text
local LOOK_NEAR = { divided = 4, blocks = 5, paws = 1, dragon = 1 }
local LOOK_FAR = { divided = 10, blocks = 10, paws = 17, dragon = 17 }
local LOOK_ALPHA = { divided = 0.55, blocks = 1 }
local LOOK_EMPTY_ALPHA = { divided = 0.22, blocks = 1 }
local LOOK_MAT = { divided = "zmhud_seg", blocks = "zmhud_stripe" }
-- paws and dragon are ONE wide strip each, drawn across the whole bar at the art's own width/height ratio
local LOOK_STRIP = { paws = "zmhud_pawstrip", dragon = "zmhud_dragonstrip" }
local LOOK_STRIP_ASPECT = { paws = 1200 / 16, dragon = 1200 / 16 }
local TRACKER_GAP = 16                          -- px between the end of the label and the popup
local TRACKER_W = 150                           -- the popup's own box
local TICK_MS = 250                             -- how often the XP dvars are read (4 times a second)

local VERSION = "v1.0"                          -- a changed file under the same number loads on a restart

local H, HD = rawget(_G, "xhash"), rawget(_G, "xhashdvar")
if type(H) ~= "function" or type(HD) ~= "function" then return end
local old = rawget(_G, "XpHudOverlay")
if old and old.version == VERSION then return end
if old then old.enabled = false end

-- One validated copy of a settings table: used once for the live state, and again by every Reset row.
local function makeConfig(d)
  return {
    anchor = d.anchor == "top" and "top" or "bottom",
    showText = d.showText ~= false,
    showTracker = d.showTracker ~= false,
    showBar = d.showBar ~= false,
    colour = (d.colour == "auto" or PRESETS[d.colour]) and d.colour or "auto",
    textSize = tonumber(d.textSize) or 11,
    trackerSize = tonumber(d.trackerSize) or 13,
    trackerAuto = d.trackerAuto ~= false,
    showPrestige = d.showPrestige ~= false,
    textPos = (d.textPos == "left" or d.textPos == "right") and d.textPos or "center",
    trackerColour = (d.trackerColour == "auto" or PRESETS[d.trackerColour]) and d.trackerColour or "auto",
    look = d.look or "line",
    width = math.floor(tonumber(d.width) or WIDTH),
  }
end
local CFG = makeConfig(DEFAULTS)
if CFG.width < WIDTH_MIN then CFG.width = WIDTH_MIN end
if CFG.width > WIDTH_MAX then CFG.width = WIDTH_MAX end
local S = { version = VERSION, enabled = true, bars = {}, pending = {}, later = {}, tick = 0, gen = 0 }
rawset(_G, "XpHudOverlay", S)

local NULLEL = setmetatable({}, { __index = function() return function() end end })
local function nullImage() return { el = NULLEL, alpha = 0, rgb = nil, png = false } end

local lastMsg
local function log(msg)
  if lastMsg == msg then return end
  lastMsg = msg
  local fn = rawget(_G, "DebugPrint") or rawget(_G, "print")
  if type(fn) == "function" then pcall(fn, "[XpHudOverlay] " .. tostring(msg)) end
end

-- ---------------------------------------------------------------------------------------------------------
-- Settings that survive a restart. The Lua VM has no file API, so the settings travel through ONE dvar, `xp_hud_overlay_cfg`, and mod\scripts\xp_hud_overlay_store.gsc mirrors that dvar to
-- kronos\xphudoverlay\settings.json. This is the only dvar the script ever sets; it carries no XP and no profile value.
-- The payload is `key=value` pairs from the closed set below joined with `,`, and every value is validated on read.
local CFG_DVAR = "xp_hud_overlay_cfg"
local storeLoaded, storeSaidBad, storeSaidOK = false, false, false

local function dvarMember(name)
  local d = rawget(_G, "Dvar")
  if type(d) ~= "table" then return nil end
  local f = H and d[H(name)]
  if type(f) ~= "function" then f = d[name] end
  return type(f) == "function" and f or nil
end

local function num(v, lo, hi, fallback)
  local n = tonumber(v)
  if n == nil then return fallback end
  if n < lo then n = lo elseif n > hi then n = hi end
  return math.floor(n)
end

local function align(v)
  return (v == "left" or v == "center" or v == "right") and v or nil
end

local function knownLook(v)
  for _, st in ipairs(LOOKS) do
    if st[1] == v then return v end
  end
  return nil
end

local function readCfgDvar()
  local g = dvarMember("GetDvarString")
  if g == nil then return nil end
  local ok, v = pcall(g, HD(CFG_DVAR))
  if ok and type(v) == "string" and #v > 0 then return v end
  return nil
end

-- Adopt the saved text once, the first time the dvar is non-empty (the GSC fills it from disk a moment after the
-- level starts). An unknown key, an unknown value or a truncated pair is skipped: a damaged value must leave the
-- defaults alone rather than half-apply.
local function applyStored()
  if storeLoaded then return end
  local text = readCfgDvar()
  if text == nil then return end                 -- nothing yet: the tick tries again
  storeLoaded = true
  local seen = 0
  for k, v in text:gmatch("([%a_]+)=([^,]*)") do
    local ok = true
    if k == "anchor" then
      if v == "top" or v == "bottom" then CFG.anchor = v else ok = false end
    elseif k == "text" then CFG.showText = (v == "1")
    elseif k == "tracker" then CFG.showTracker = (v == "1")
    elseif k == "bar" then CFG.showBar = (v == "1")
    elseif k == "prestige" then CFG.showPrestige = (v == "1")
    elseif k == "colour" then
      if v == "auto" or PRESETS[v] ~= nil then CFG.colour = v else ok = false end
    elseif k == "look" then
      local look = knownLook(v)
      if look ~= nil then CFG.look = look else ok = false end
    elseif k == "width" then CFG.width = num(v, WIDTH_MIN, WIDTH_MAX, CFG.width)
    elseif k == "textpos" then
      local a = align(v)
      if a ~= nil then CFG.textPos = a else ok = false end
    elseif k == "textsize" then CFG.textSize = num(v, TEXT_MIN, TEXT_MAX, CFG.textSize)
    elseif k == "trackersize" then CFG.trackerSize = num(v, TEXT_MIN, TEXT_MAX, CFG.trackerSize)
    elseif k == "trackerauto" then CFG.trackerAuto = (v == "1")
    elseif k == "trackercolour" then
      if v == "auto" or PRESETS[v] ~= nil then CFG.trackerColour = v else ok = false end
    else
      ok = false
    end
    if ok then seen = seen + 1 end
  end
  if CFG.width < WIDTH_MIN then CFG.width = WIDTH_MIN elseif CFG.width > WIDTH_MAX then CFG.width = WIDTH_MAX end
  log("settings: " .. seen .. " read from " .. CFG_DVAR)
  if type(S.afterStored) == "function" then pcall(S.afterStored) end
end

local function persist()
  local set = dvarMember("SetDvarString")
  if set == nil then
    if not storeSaidBad then
      storeSaidBad = true
      log("settings: no Dvar.SetDvarString in this VM - settings will not survive a restart")
    end
    return false
  end
  local text = "anchor=" .. CFG.anchor
    .. ",text=" .. (CFG.showText and 1 or 0)
    .. ",tracker=" .. (CFG.showTracker and 1 or 0)
    .. ",bar=" .. (CFG.showBar and 1 or 0)
    .. ",prestige=" .. (CFG.showPrestige and 1 or 0)
    .. ",colour=" .. CFG.colour
    .. ",look=" .. CFG.look
    .. ",width=" .. CFG.width
    .. ",textpos=" .. CFG.textPos
    .. ",textsize=" .. CFG.textSize
    .. ",trackersize=" .. CFG.trackerSize
    .. ",trackerauto=" .. (CFG.trackerAuto and 1 or 0)
    .. ",trackercolour=" .. CFG.trackerColour
  storeLoaded = true                              -- our own value is now the truth; do not adopt a stale one over it
  local ok, err = pcall(set, HD(CFG_DVAR), text)
  if not ok then
    if not storeSaidBad then
      storeSaidBad = true
      log("settings: SetDvarString raised: " .. tostring(err))
    end
    return false
  end
  if not storeSaidOK then
    storeSaidOK = true
    local function verdict(back)
      return back == text and "identical" or (back and (#back .. " B, different: " .. back:sub(1, 40)) or "nothing")
    end
    log("settings: wrote " .. CFG_DVAR .. " (" .. #text .. " bytes), reads back " .. verdict(readCfgDvar()))
    -- A dvar set may only land at the end of the frame: ask again a tick later.
    S.later[#S.later + 1] = { at = S.tick + 1, fn = function()
      log("settings: one tick later " .. CFG_DVAR .. " reads back " .. verdict(readCfgDvar()))
    end }
  end
  return true
end

-- ---------------------------------------------------------------------------------------------------------
-- Reading the HUD theme that Kronos has selected. Kronos itself does this through an OPTIONS member whose name is a
-- 64-bit hash, written in its Lua as a bytecode constant (so the name never appears in plain text). The same three
-- helpers are used here, once, wrapped in pcall: if anything at all goes wrong the colour falls back to AUTO_DEFAULT.
local function uleb(n)
  local t = {}
  repeat
    local b = n % 128
    n = math.floor(n / 128)
    if n > 0 then b = b + 128 end
    t[#t + 1] = string.char(b)
  until n == 0
  return table.concat(t)
end
local HXC = {}
local function Hx(hex, kind)
  kind = kind or 0
  local ck = hex .. ":" .. kind
  if HXC[ck] then return HXC[ck] end
  local h = hex:gsub("^0*", "")
  h = string.rep("0", 16 - #h) .. h
  local b8 = {}
  for i = 8, 1, -1 do b8[#b8 + 1] = string.char(tonumber(h:sub(i * 2 - 1, i * 2), 16)) end
  local kgc = string.char(4, kind) .. table.concat(b8)
  local bc = string.char(0x28, 0, 0, 0) .. string.char(0x4d, 0, 2, 0)
  local body = string.char(0, 0, 2, 0) .. uleb(1) .. uleb(0) .. uleb(2) .. bc .. kgc
  local chunk = string.char(27) .. "LJ" .. string.char(0x84) .. uleb(0x1a) .. uleb(#body) .. body .. string.char(0)
  local f = assert(load(chunk))
  HXC[ck] = f()
  return HXC[ck]
end
local THEME = { [990420] = "soe", [990421] = "giant" }     -- Kronos's two HUD themes, by id
local function themeID()
  local opt = rawget(_G, "OPTIONS")
  if type(opt) ~= "table" then return nil end
  local okK, key = pcall(Hx, "08b03778e36f133d")
  if not okK or key == nil then return nil end
  local fn = opt[key]
  if type(fn) ~= "function" then return nil end
  local okV, v = pcall(fn, 0, "appliedhudthemeid")
  if not okV then return nil end
  return tonumber(v)
end

-- Work out the four colours once (and again if SetColour is called). Nothing here runs while idle.
local function colours()
  local base
  if CFG.colour == "auto" then
    local id = themeID()
    base = PRESETS[THEME[id] or AUTO_DEFAULT] or PRESETS.giant
    if S.themeID ~= id then
      S.themeID = id
      log("colour: " .. (THEME[id] or AUTO_DEFAULT) .. " (hud theme id " .. tostring(id) .. ")")
    end
  else
    base = PRESETS[CFG.colour] or PRESETS[AUTO_DEFAULT]
  end
  return base
end

-- The "+N XP" popup's own colour: `auto` borrows the bar's accent, any preset name takes its accent.
local function popupColour()
  local p = CFG.trackerColour ~= "auto" and PRESETS[CFG.trackerColour] or colours()
  return p.accent
end

-- ---------------------------------------------------------------------------------------------------------
-- The ladder: level L (rank = L-1) spans [LV_XP[L], LV_XP[L+1]). Same table Kronos uses.
-- 55 is the last standard level, 1000 the last Prestige Master level (`LEVEL_MAX`, the client's own number:
-- `LUIFPSCounter.lua:4126`). Level 55 is not MAX on arrival: the client keeps earning through it and parks the XP
-- at 1,152,999 until the player prestiges (`kronos\custom_scripts\zm_local_xp.gsc`: `if prestige < 11 && xp >
-- 1152999`). Prestige Master 1000 is the ladder's last rank (999, `docs\tables\rank-table-sat.csv`) and has no
-- next level, so it is MAX as soon as it is reached.
local LV_XP = { 0, 4500, 9500, 15000, 20500, 26500, 33000, 40000, 47500, 55500, 64000, 73000, 82500, 92500, 103000,
  114000, 125500, 137500, 150000, 163000, 176500, 191000, 206000, 221500, 237500, 254500, 272000, 290000, 309000, 328500,
  348500, 369500, 391000, 413500, 437000, 461000, 486000, 512000, 538500, 566000, 594500, 624000, 654500, 686000, 718500,
  752000, 786500, 822000, 858500, 896500, 935500, 976000, 1018000, 1061500, 1106500, 1153000, 1200000 }
local PRESTIGE_MASTER, LEVEL_CAP, LEVEL_MAX = 11, 55, 1000
local function levelXP(level)
  if level < 1 then return 0 end
  if level <= #LV_XP then return LV_XP[level] end
  return LV_XP[#LV_XP] + (level - #LV_XP) * 48000
end
local function levelFromXP(xp)
  local level = 1
  while levelXP(level + 1) <= xp and level < LEVEL_MAX do level = level + 1 end
  return level
end
local function comma(n)
  local s = tostring(math.floor(n + 0.5))
  local sign, digits = s:match("^(-?)(%d+)$")
  if not digits then return s end
  digits = digits:reverse():gsub("(%d%d%d)", "%1,"):reverse():gsub("^,", "")
  return sign .. digits
end

-- The level row, with the `P3` / `PM` prefix only when it is switched on. Prestige master prints `PM`, not `P11`:
-- passing level 55 of prestige 10 is the same PRESTIGE_MASTER constant.
local function labelFor(m, hidePrestige)
  if hidePrestige then return m.body end
  if m.master then return "PM   " .. m.body end
  if m.prestige and m.prestige > 0 then return string.format("P%d   %s", m.prestige, m.body) end
  return m.body
end

-- xp/rank/prestige -> what the bar shows: the level, the progress inside the current level, and the fill fraction.
-- MAX means "nothing left to earn": at Prestige Master 1000 that is the moment the level is reached (it is the last
-- level), while level 55 is a band the player still has to finish before the next prestige. `capped` also
-- suppresses the `+N XP` popup, so a maxed row cannot move.
local function model(xp, rank, prestige)
  prestige = prestige or 0
  local master = prestige >= PRESTIGE_MASTER
  local top = master and LEVEL_MAX or LEVEL_CAP
  local level = rank and (rank + 1) or levelFromXP(xp)
  if level > top then level = top end
  local lo, hi = levelXP(level), levelXP(level + 1)
  local capped
  if master then
    capped = level >= LEVEL_MAX          -- PM 1000: no next level exists, so MAX on arrival
  else
    -- below Prestige Master the client holds the XP one short of the next rank (`zm_local_xp.gsc`), so 55's band
    -- is finished at `hi - 1`
    capped = level >= LEVEL_CAP and xp >= hi - 1
  end
  local frac = hi > lo and (xp - lo) / (hi - lo) or 0
  if frac < 0 then frac = 0 elseif frac > 1 then frac = 1 end
  if capped then frac = 1 end
  local body
  if capped then
    body = string.format("LVL %d   |   MAX", level)
  else
    body = string.format("LVL %d   |   %s / %s XP", level, comma(math.max(0, xp - lo)), comma(hi - lo))
  end
  local m = { level = level, lo = lo, hi = hi, frac = frac, body = body, capped = capped,
    prestige = prestige, master = master }
  m.label = labelFor(m, false)
  return m
end
S.model = model

-- ---------------------------------------------------------------------------------------------------------
-- The three dvars Kronos keeps the player level in. Read only.
local getInt, getStr, handles
local function resolveApi()
  local dvar = rawget(_G, "Dvar")
  if dvar == nil then return false end
  getInt = dvar[H("GetDvarInt")]
  getStr = dvar[H("GetDvarString")]
  handles = handles or { xp = HD("zm_local_rankxp"), rank = HD("zm_local_rank"), prestige = HD("zm_local_prestige") }
  return type(getInt) == "function" or type(getStr) == "function"
end
local function getvar(key)
  local h = handles[key]
  for _, fn in ipairs({ getInt or false, getStr or false }) do
    if fn then
      local ok, v = pcall(fn, h)
      if ok and v ~= nil and v ~= "" then
        local n = tonumber(v)
        if n then return n end
      end
    end
  end
end
local function readState()
  if not handles and not resolveApi() then return nil end
  return getvar("xp"), getvar("rank"), getvar("prestige")
end

-- Controller index for the game's own progression getters (0 is fine solo; otherwise the first active pad).
local ctrl
local function controller()
  if ctrl ~= nil then return ctrl end
  ctrl = 0
  local e = rawget(_G, "Engine")
  local f = e and e[H("GetFirstActiveController")]
  if type(f) == "function" then
    local ok, v = pcall(f)
    if ok and type(v) == "number" then ctrl = v end
  end
  return ctrl
end

-- The game's own getters. Kronos rewrites these to read your local progression, so they answer in every mode.
local function progressFromUI()
  local P = rawget(_G, "PROGRESSION")
  if type(P) ~= "table" then return nil end
  local fxp, frank = P[H("GetPlayerXP")], P[H("GetPlayerRank")]
  if type(fxp) ~= "function" or type(frank) ~= "function" then return nil end
  local okx, xp = pcall(fxp, controller())
  local okr, rank = pcall(frank, controller())
  xp, rank = okx and tonumber(xp) or nil, okr and tonumber(rank) or nil
  if xp == nil or rank == nil then return nil end
  return xp, rank
end

-- xp, rank, prestige, source. Zombies dvars first (they are what Kronos writes there), then the getters.
local function readProgress()
  local xp, rank, prestige = readState()
  if xp ~= nil then return xp, rank, prestige, "dvar" end
  local uxp, urank = progressFromUI()
  if uxp ~= nil then return uxp, urank, nil, "progression" end
  return nil
end

-- In the frontend (main menu, lobby, loading videos)? The game answers this itself; if it cannot, the map name below
-- is the fallback.
local frontendFn
local function inFrontend()
  if frontendFn == nil then
    local e = rawget(_G, "Engine")
    local f = e and e[H("InFrontend")]
    frontendFn = (type(f) == "function") and f or false
  end
  if frontendFn == false then return false end
  local ok, v = pcall(frontendFn)
  return ok and v == true
end

-- Is a map actually loaded? Kronos reads the same dvar to tell Zombies from Multiplayer. Unknown -> assume yes, so an
-- unreadable dvar never hides the bar.
local mapHandles
local function inMap()
  local dvar = rawget(_G, "Dvar")
  if dvar == nil then return true end
  local getter = dvar[H("GetDvarString")]
  if type(getter) ~= "function" then return true end
  if mapHandles == nil then
    mapHandles = {}
    local okN, h1 = pcall(HD, "mapname")
    if okN and h1 ~= nil then mapHandles[1] = h1 end
    local okH, h2 = pcall(Hx, "b2d6f347952c7d99")     -- the form Kronos itself uses for this dvar
    if okH and h2 ~= nil then mapHandles[2] = h2 end
  end
  for i = 1, 2 do
    local h = mapHandles[i]
    if h ~= nil then
      local ok, v = pcall(getter, h)
      v = ok and tostring(v) or ""
      if v:find("^mp_") or v:find("^zm_") then return true end
      if v ~= "" and v ~= "nil" then return false end
    end
  end
  return true
end

-- ---------------------------------------------------------------------------------------------------------
-- Placement. Every element is positioned the same way: horizontally from the centre, vertically by a distance from
-- the chosen screen edge, so DEFAULTS.anchor = "top" mirrors the whole layout without touching anything else.
local function place(e, l, r, near, far)
  if CFG.anchor == "top" then
    e:SetAnchorsAndPosition(0.5, 0.5, 0, 1, l, r, near, far)
  else
    e:SetAnchorsAndPosition(0.5, 0.5, 1, 0, l, r, -far, -near)
  end
end

-- Every engine call goes through a cached setter: if the value is the one already set, nothing is sent.
local function setRGB(o, rgb)
  if o == nil or o.rgb == rgb then return end
  o.rgb = rgb
  o.el:SetRGB(rgb, 0)
end
local function setAlpha(o, a, ms)
  if o == nil or o.alpha == a then return end
  o.alpha = a
  o.el:SetAlpha(a, ms or 0)
end

-- The label, the tracker and the soft light always exist, so the in-game settings page can switch them on and off
-- without tearing a bar down: hiding is three cached SetAlpha calls, not a rebuild. The track and the fill are
-- owned by setVisible (is the bar on screen at all) and by setFill (how much XP is in it).
local GLOW_ALPHA = 0.30
local function lookVisible(bar)
  local shown = not S.hidden
  local text = CFG.showText and shown
  local gain = CFG.showTracker and shown
  -- the plain pill is the accented base colour, not black - the same read as every other style's empty part
  setAlpha(bar.track, (CFG.showBar and shown and CFG.look == "line") and 1 or 0)
  setAlpha(bar.label.group, text and 1 or 0)
  setAlpha(bar.glow, text and GLOW_ALPHA or 0)
  setAlpha(bar.gain.group, (gain and bar.gainShown) and 1 or 0)
end

local MATS = {}
local function mat(name)
  local m = MATS[name]
  if m == nil then
    local ok, v = pcall(function() return RegisterMaterial(CLUA.PushXHashAsset(name)) end)
    m = (ok and v) or false
    MATS[name] = m
  end
  return m or nil
end
local WHITE_MAT
local function whiteMat()
  if WHITE_MAT == nil then
    local ok, v = pcall(RegisterMaterial, "white")
    WHITE_MAT = (ok and v) or false
  end
  return WHITE_MAT or nil
end
local function addBlend()
  local b = rawget(_G, "BLEND_MODE")
  return type(b) == "table" and b.addWithAlpha or nil
end

-- optional = true: a missing PNG draws nothing (a missing track must not become a white rectangle).
local function image(parent, name, rgb, alpha, l, r, near, far, optional, blend)
  local m = mat(name)
  local png = m ~= nil
  if not m and optional then return nullImage() end
  local e = LUI.UIImage.new()
  place(e, l, r, near, far)
  if not m then m = whiteMat() end
  if m then e:setImage(m, 0) end
  local o = { el = e, rgb = nil, alpha = nil, png = png }
  if rgb then e:SetRGB(rgb, 0); o.rgb = rgb end
  e:SetAlpha(alpha, 0); o.alpha = alpha
  if blend then e:SetBlendMode(blend) end
  parent:addElement(e)
  return o
end

-- ---------------------------------------------------------------------------------------------------------
-- The text and the popup sit 6 px above the pill; with the bar hidden there is nothing to clear, so they drop onto
-- where the pill was instead of floating with an empty row underneath.
local function textDrop()
  return CFG.showBar and 0 or 10
end

-- One text element with the engine's own built-in drop shadow.
local function styledRow(parent, l, r, near, far, align, size)
  local t = LUI.UIStyledText.new()
  place(t, l, r, near, far)
  local fonts = rawget(_G, "FONT_HANDLE")
  local font = type(fonts) == "table" and (fonts.PrimaryBold or fonts.PrimaryRegular) or nil
  if font then pcall(t.SetFont, t, font) end
  local pt = rawget(_G, "_PT")
  if type(pt) ~= "number" then pt = 1 end
  pcall(t.SetFontSize, t, size * pt)
  pcall(t.SetMinFontSize, t, size * pt)
  pcall(t.SetWordWrap, t, false)
  pcall(t.SetAlignment, t, align)
  pcall(t.SetShadowAngle, t, 225, 0)
  pcall(t.SetShadowDistance, t, 0.04, 0)
  pcall(t.SetShadowSize, t, 0.08, 0)
  pcall(t.SetShadowOpacity, t, 0.9, 0)
  parent:addElement(t)
  local row = { group = { el = t, alpha = nil }, str = nil, rgb = nil, width = 0, fallback = true, size = size, align = align or 0 }
  -- The box is bottom-aligned so the text sits on a fixed line above the pill and grows upward with its size.
  pcall(function()
    local al = rawget(_G, "LUI")
    local alignTab = type(al) == "table" and rawget(al, "Alignment") or nil
    t:SetVerticalAlignment(type(alignTab) == "table" and alignTab.Bottom or 2)
  end)
  -- This client does not re-lay a styled row out on SetFontSize/SetAlignment alone: the glyphs only change when the
  -- text is set again. Every size/align change therefore re-sets the same string.
  local function refreshText()
    local s = row.str or ""
    row.str = nil
    row.set(s, row.rgb)
  end
  function row.setColor(c)
    if row.rgb == c then return end
    row.rgb = c
    t:SetRGB(c, 0)
  end
  function row.setSize(s)
    if row.size == s then return end
    row.size = s
    local p = rawget(_G, "_PT")
    if type(p) ~= "number" then p = 1 end
    pcall(t.SetFontSize, t, s * p)
    pcall(t.SetMinFontSize, t, s * p)
    if row.str then row.width = #row.str * s * 0.4 end
    refreshText()
  end
  function row.setAlign(a)
    if row.align == a then return end
    row.align = a
    pcall(t.SetAlignment, t, a)
    refreshText()
  end
  function row.set(str, c)
    row.setColor(c)
    if row.str == str then return end
    row.str = str
    t:setText(str)
    for _, n in ipairs({ "CompleteDecodeAnimation", "FinishDecodeAnimation", "CompleteTextDecode" }) do
      local f = t[n]
      if type(f) == "function" and pcall(f, t) then break end
    end
    row.width = #str * (row.size or size) * 0.4
  end
  return row
end

-- ---------------------------------------------------------------------------------------------------------
-- One bar: soft light, track, fill (rounded cap + body + rounded tip), label, "+N XP" tracker.
local function build(top)
  local bar = { top = top, fillW = -1, cur = nil, glowHalf = nil, gainShown = false, gainUntil = 0, gainTotal = 0,
    pool = {}, poolN = 0, look = nil }
  local ok, err = pcall(function()
    local C = colours()
    local L, R = -CFG.width / 2, CFG.width / 2
    local fill = { L, L + 1, BAR_NEAR, BAR_FAR }
    bar.glow = image(top, "zmhud_glow", C.glow, 0, -120, 120, GLOW_NEAR, GLOW_FAR, true, addBlend())
    bar.track = image(top, "zmhud_track", nil, 0, L, R, TRACK_NEAR, TRACK_FAR, true)
    bar.cap = image(top, "zmhud_cap", C.accent, 0, fill[1], fill[2], fill[3], fill[4])
    bar.body = image(top, "zmhud_body", C.accent, 0, fill[1], fill[2], fill[3], fill[4])
    bar.tip = image(top, "zmhud_tip", C.accent, 0, fill[1], fill[2], fill[3], fill[4])
    bar.png = bar.track.png and bar.cap.png and bar.body.png and bar.tip.png
    -- The strip styles ("Cats", "DraGON"): one copy of the strip inside each of two stencils - the dim copy spans
    -- the bar, the bright copy spans the progress. A stencil crops the art at its own edge, so the strip is drawn at
    -- its authored size and cut, never squeezed. Built before the rows, so the text always draws on top.
    bar.clip = LUI.UIElement.new()
    bar.clip:setUseStencil(true)
    top:addElement(bar.clip)
    bar.clipFill = LUI.UIElement.new()
    bar.clipFill:setUseStencil(true)
    top:addElement(bar.clipFill)
    bar.stripDim = image(bar.clip, "zmhud_pawstrip", nil, 0, 0, 1, 0, 1, true)
    bar.stripBright = image(bar.clipFill, "zmhud_pawstrip", nil, 0, 0, 1, 0, 1, true)
    bar.stripDim.mat = nil
    bar.stripBright.mat = nil
    -- align: 0 = left, 1 = centre, 2 = right. The label is centred in the bar's own box.
    local la = CFG.textPos == "left" and 0 or (CFG.textPos == "right") and 2 or 1
    local drop = textDrop()
    bar.label = styledRow(top, L, R, LABEL_NEAR - drop, LABEL_FAR - drop, la, CFG.textSize)
    local gs = CFG.trackerAuto and CFG.textSize or CFG.trackerSize
    bar.gain = styledRow(top, 0, TRACKER_W, TRACKER_NEAR - drop, TRACKER_FAR - drop, 0, gs)
    setAlpha(bar.gain.group, 0)
    lookVisible(bar)
  end)
  if not ok then
    log("could not build the bar: " .. tostring(err))
    return nil
  end
  return bar
end

-- The soft light is as wide as the label needs, and only re-fitted when the label's width changes. It is centred on
-- the LABEL (which starts at the bar's left end), not on the middle of the bar.
local function fitGlow(bar)
  if not CFG.showText or bar.glow == nil or bar.label == nil then return end
  local tw = bar.label.width or 0
  if tw <= 0 then return end
  local width = math.max(1, CFG.width)
  local half = math.floor(tw / 2 * GLOW_GROW + GLOW_PAD + 0.5)
  -- the light follows the TEXT, wherever the XP Text tab put it, and may bleed past the bar's ends: clamping it
  -- inside the pill would cut it off at LEFT/RIGHT
  local cx
  if CFG.textPos == "left" then cx = -width / 2 + tw / 2
  elseif CFG.textPos == "right" then cx = width / 2 - tw / 2
  else cx = 0 end
  cx = math.floor(cx + 0.5)
  -- The row's drop is part of the key: with the bar off the text sits 10 px lower and the light has to follow it.
  local drop = textDrop()
  if half == bar.glowHalf and cx == bar.glowCX and drop == bar.glowDrop then return end
  bar.glowHalf, bar.glowCX, bar.glowDrop = half, cx, drop
  place(bar.glow.el, cx - half, cx + half, GLOW_NEAR - drop, GLOW_FAR - drop)
end

-- 30 % of a colour: the "not earned yet" read every style shares (and the plain pill's base colour).
local function dimAccent(rgb)
  -- plain arithmetic: the client speaks Lua 5.1, which has no bitwise operators
  local r = math.floor((math.floor(rgb / 65536) % 256) * 0.30 + 0.5)
  local g = math.floor((math.floor(rgb / 256) % 256) * 0.30 + 0.5)
  local b = math.floor((rgb % 256) * 0.30 + 0.5)
  return r * 65536 + g * 256 + b
end

local function applyColours(bar)
  local C = colours()
  setRGB(bar.track, dimAccent(C.accent))
  setRGB(bar.cap, C.accent)
  setRGB(bar.body, C.accent)
  setRGB(bar.tip, C.accent)
  setRGB(bar.glow, C.glow)
  if bar.cur then
    bar.label.set(labelFor(bar.cur, not CFG.showPrestige), C.text)
  end
  if bar.gain.str then
    bar.gain.setColor(popupColour())
  end
end

-- One pooled image for a style's fill. Created on first use, re-materialled when the style changes, hidden by alpha
-- when the fill does not need it. Everything here is inside the fill band, so a style cannot move the text.
local function poolImage(bar, i, material, l, r, near, far, rgb, alpha)
  local o = bar.pool[i]
  if o == nil then
    local ok, e = pcall(function() return LUI.UIImage.new() end)
    if not ok or e == nil then return end
    place(e, l, r, near, far)
    pcall(function() bar.top:addElement(e) end)
    o = { el = e, alpha = nil, rgb = nil, mat = nil }
    bar.pool[i] = o
  end
  if material ~= nil and o.mat ~= material then
    o.mat = material
    pcall(function() o.el:setImage(material, 0) end)
  end
  place(o.el, l, r, near, far)
  setRGB(o, rgb)
  setAlpha(o, alpha or 1)
end

local function setFill(bar, frac)
  local w = math.floor(CFG.width * frac + 0.5)
  local C = colours()
  -- The tint is part of the key: a colour change repaints the pieces, a width-only change would not.
  if w == bar.fillW and bar.look == CFG.look and bar.tint == C.accent then return end
  bar.fillW, bar.look, bar.tint = w, CFG.look, C.accent
  local l = -CFG.width / 2
  local style = CFG.look
  local on = CFG.showBar and not S.hidden
  local line = (style == "line")
  local stripStyle = (on and LOOK_STRIP[style]) or nil
  if stripStyle == nil then
    setAlpha(bar.stripDim, 0)
    setAlpha(bar.stripBright, 0)
  end
  -- the pill is the plain style's body; a styled bar replaces it
  setAlpha(bar.track, (on and line) and 1 or 0)
  if not on or w < 3 or not line then
    setAlpha(bar.cap, 0); setAlpha(bar.body, 0); setAlpha(bar.tip, 0)
  else
    local tip = math.min(CAPW, math.floor(w / 2))
    local cap = math.min(CAPW, w - tip)
    local body = w - tip - cap
    place(bar.cap.el, l, l + cap, BAR_NEAR, BAR_FAR)
    place(bar.tip.el, l + w - tip, l + w, BAR_NEAR, BAR_FAR)
    setAlpha(bar.cap, 1)
    setAlpha(bar.tip, 1)
    if body > 0 then
      place(bar.body.el, l + cap, l + cap + body, BAR_NEAR, BAR_FAR)
      setAlpha(bar.body, 1)
    else
      setAlpha(bar.body, 0)
    end
  end
  local n = 0
  if stripStyle ~= nil then
    -- The strip is the bar: one copy in each stencil - the dim one fills the bar, the bright one is cropped at the
    -- progress. Nothing is scaled.
    local sn, sf = LOOK_NEAR[style] or BAR_NEAR, LOOK_FAR[style] or BAR_FAR
    local band = sf - sn
    local aspect = LOOK_STRIP_ASPECT[style] or (CFG.width / math.max(1, band))
    local tile = math.max(1, math.floor(band * aspect + 0.5))
    local material = mat(stripStyle)
    for _, o in ipairs({ bar.stripDim, bar.stripBright }) do
      if material ~= nil and o.mat ~= material then
        o.mat = material
        pcall(function() o.el:setImage(material, 0) end)
      end
      -- a child of a stencil is placed in the stencil's own units: 0..tile across, 0..band down
      pcall(function() o.el:SetAnchorsAndPosition(0, 1, 0, 1, 0, tile, 0, band) end)
    end
    setRGB(bar.stripDim, dimAccent(C.accent))
    setRGB(bar.stripBright, C.accent)
    setAlpha(bar.stripDim, 1)
    setAlpha(bar.stripBright, (on and w >= 2) and 1 or 0)
    place(bar.clip, l, l + CFG.width, sn, sf)
    place(bar.clipFill, l, l + math.max(1, w), sn, sf)
    -- the pool belongs to the other styles: nothing of it may show through the art
    for k = 1, bar.poolN or 0 do
      if bar.pool[k] ~= nil then setAlpha(bar.pool[k], 0) end
    end
    bar.poolN = 0
    return
  end
  if on and style ~= "line" then
    local pitch = LOOK_PITCH[style] or 24
    local gw = LOOK_GLYPH[style] or (pitch - 4)
    local alpha = LOOK_ALPHA[style] or 1
    local alphaEmpty = LOOK_EMPTY_ALPHA[style] or alpha
    local near = LOOK_NEAR[style] or BAR_NEAR
    local far = LOOK_FAR[style] or BAR_FAR
    local material = mat(LOOK_MAT[style])
    local count = math.floor(CFG.width / pitch)
    local filled = math.min(count, math.floor(w / pitch + 0.5))
    for i = 1, count do
      local x = l + (i - 1) * pitch + math.floor((pitch - gw) / 2)
      local on_ = i <= filled
      poolImage(bar, i, material, x, x + gw, near, far,
        on_ and C.accent or dimAccent(C.accent), on_ and alpha or alphaEmpty)
    end
    n = count
  end
  for i = n + 1, bar.poolN or 0 do
    if bar.pool[i] ~= nil then setAlpha(bar.pool[i], 0) end
  end
  bar.poolN = n
end

-- The label's own width, in 1920x1080 units: the text element answers with `getElementTextDims` (what the game's own
-- `LAYOUT.GetTextWidth` calls); `label width from <source>` says which source answered, once.
local function labelWidth(bar)
  if bar.label == nil then return nil end
  local el = bar.label.group and bar.label.group.el
  if el ~= nil then
    local ok, w = pcall(function() return el:getElementTextDims() end)
    if ok and type(w) == "number" and w > 8 and w < CFG.width then
      S.widthFrom = "the text element (getElementTextDims)"
      return w
    end
  end
  local str = bar.label.str
  if type(str) == "string" and #str > 0 then
    S.widthFrom = "the estimate (#str x size x 0.4)"
    return #str * (bar.label.size or CFG.textSize) * 0.4
  end
  S.widthFrom = "nothing - the popup stays at its fixed column"
  return nil
end

-- The `+N XP` popup is pinned to the right of the level text, always: its box starts TRACKER_GAP after the label's own
-- measured end and its text is left-aligned inside it, so the gap is the gap and nothing else. The only case without a
-- "right of the text" is the text being off - then the popup parks at the bar's left end.
local function placeTracker(bar)
  if not CFG.showTracker or bar.gain == nil then return end
  local half = CFG.width / 2
  local x, w = -half, 0
  if CFG.showText then
    w = labelWidth(bar) or 0
    if S.widthFrom ~= nil and S.widthFrom ~= S.widthSaid then
      S.widthSaid = S.widthFrom
      log("label width from " .. S.widthFrom)
    end
    local ls
    if CFG.textPos == "left" then ls = -half
    elseif CFG.textPos == "right" then ls = half - w
    else ls = -w / 2 end
    x = ls + w + TRACKER_GAP
  end
  -- Pinned to the right of the text at all times: with the text at the bar's right end the popup runs past the bar's
  -- edge rather than jumping to the other side of the label. The only bound is the screen (1920 units, so +/-960).
  if x + TRACKER_W > 960 then x = 960 - TRACKER_W end
  if x < -960 then x = -960 end
  x = math.floor(x + 0.5)
  bar.gain.setAlign(0)
  if x == bar.gainX then return end
  bar.gainX = x
  place(bar.gain.group.el, x, x + TRACKER_W, TRACKER_NEAR - textDrop(), TRACKER_FAR - textDrop())
end

-- Re-place a bar that is already built: every element is positioned from CFG.anchor, so SetAnchor can mirror the
-- whole widget without tearing it down and building a second one.
local function reanchor(bar)
  place(bar.track.el, -CFG.width / 2, CFG.width / 2, TRACK_NEAR, TRACK_FAR)
  if bar.glowHalf then
    -- the light follows the text row, drop included
    place(bar.glow.el, bar.glowCX - bar.glowHalf, bar.glowCX + bar.glowHalf,
      GLOW_NEAR - textDrop(), GLOW_FAR - textDrop())
  end
  place(bar.label.group.el, -CFG.width / 2, CFG.width / 2, LABEL_NEAR - textDrop(), LABEL_FAR - textDrop())
  local x = bar.gainX or 0
  place(bar.gain.group.el, x, x + TRACKER_W, TRACKER_NEAR - textDrop(), TRACKER_FAR - textDrop())
  bar.fillW = -1
  setFill(bar, bar.cur and bar.cur.frac or 0)
end

-- Re-apply everything a settings row can change, to a bar that is already on screen. No element is created: the
-- rows exist from the first build, so a toggle is colours, alphas and positions only.
local function repaint(bar)
  local la = CFG.textPos == "left" and 0 or (CFG.textPos == "right") and 2 or 1
  if bar.label ~= nil and bar.label.setSize ~= nil then
    bar.label.setSize(CFG.textSize)
    bar.label.setAlign(la)
  end
  local gs = CFG.trackerAuto and CFG.textSize or CFG.trackerSize
  if bar.gain ~= nil and bar.gain.setSize ~= nil then
    bar.gain.setSize(gs)
  end
  applyColours(bar)
  fitGlow(bar)
  placeTracker(bar)
  lookVisible(bar)
  if bar.cur then setFill(bar, bar.cur.frac) end
end

-- ---------------------------------------------------------------------------------------------------------
-- XP -> bars. Runs only when a dvar value actually changed.
local cur = { xp = nil, rank = nil, prestige = nil, m = nil }
local function applyAll(xp, rank, prestige)
  local m = model(xp, rank, prestige)
  local gained = (cur.xp and xp > cur.xp) and (xp - cur.xp) or 0
  local C = colours()
  cur.xp, cur.rank, cur.prestige, cur.m = xp, rank, prestige, m
  for _, bar in ipairs(S.bars) do
    bar.cur = m
    bar.label.set(labelFor(m, not CFG.showPrestige), C.text)
    fitGlow(bar)
    placeTracker(bar)
    setAlpha(bar.track, 1)
    setFill(bar, m.frac)
    if gained > 0 and CFG.showTracker and not m.capped then
      bar.gainTotal = (bar.gainShown and bar.gainTotal or 0) + gained
      local txt = "+" .. comma(bar.gainTotal) .. " XP"
      bar.gain.set(txt, popupColour())
      setAlpha(bar.gain.group, 1)
      bar.gainShown = true
      bar.gainUntil = S.tick + 6              -- 6 reads of the timer = about 1.5 seconds
    end
    lookVisible(bar)
  end
end

local hidden = false
local function setVisible(show)
  if hidden == not show then return end
  hidden = not show
  S.hidden = hidden
  for _, bar in ipairs(S.bars) do
    setAlpha(bar.track, show and 1 or 0)
    if show then
      lookVisible(bar)                        -- restores the text/tracker per the current settings
    else
      setAlpha(bar.cap, 0); setAlpha(bar.body, 0); setAlpha(bar.tip, 0)
      setAlpha(bar.stripDim, 0); setAlpha(bar.stripBright, 0)
      setAlpha(bar.glow, 0)
      -- a style's own fill pieces are not part of the pill: hiding the bar has to take them with it
      for i = 1, bar.poolN or 0 do
        if bar.pool[i] ~= nil then setAlpha(bar.pool[i], 0) end
      end
      bar.poolN = 0
      -- the popup is not part of the row: hiding the bar mid-award must take it with it
      setAlpha(bar.gain.group, 0)
      setAlpha(bar.label.group, 0)
      bar.gainShown = false
      bar.fillW = -1
    end
  end
end

local function poll()
  -- The GSC fills the settings dvar from disk a moment after the level starts: one dvar read per tick until it answers.
  if not storeLoaded then pcall(applyStored) end
  local xp, rank, prestige, source = readProgress()
  if source and source ~= S.source then
    S.source = source
    log("xp source: " .. source)
  end
  -- Visibility is decided once, here: readable XP, and (for a bar on the HUD root) a map actually loaded.
  local show = xp ~= nil
  if show and inFrontend() then show = false end
  if show and S.rootBar and not inMap() then show = false end
  if not show then
    if xp == nil and not S.warned then
      S.warned = true
      log("no player XP is readable in this game state - the bar stays hidden")
    end
    setVisible(false)
    return
  end
  if hidden then
    setVisible(true)
    cur.xp = nil                                 -- repaint fully, without a "+N XP" for the change
  end
  if xp ~= cur.xp or rank ~= cur.rank or prestige ~= cur.prestige then
    applyAll(xp, rank, prestige)
  end
  for _, bar in ipairs(S.bars) do
    if bar.gainShown and S.tick >= bar.gainUntil then
      bar.gainShown = false
      bar.gain.group.el:SetAlpha(0, 500); bar.gain.group.alpha = 0
    end
  end
end

-- Attach: a freshly built widget has no parent for a moment, so the timer keeps trying, walks to the top of the HUD
-- tree and builds there once per tree.
local TYPES = {
  PERKS = "fb7c1d32eeb344a0", ROUND = "e7da34cbc8066689", LOADOUT = "05671cb57eb82497",
  SQUAD = "f34f8750c67ba329", COMPASS = "56cd14a086232b2f", QUEST = "5985ec6e703283a7",
}
local function typeName(t)
  local s = tostring(t):lower()
  for name, hx in pairs(TYPES) do
    if s:find(hx, 1, true) then return name end
  end
end
local function topOf(w)
  local p, guard = w, 0
  while guard < 40 do
    local ok, up = pcall(function() return p:getParent() end)
    if not ok or not up then break end
    p, guard = up, guard + 1
  end
  return p, guard
end
local function attached(top)
  for _, bar in ipairs(S.bars) do
    if bar.top == top then return true end
  end
  return false
end
local function tryAttach(entry)
  local top, depth = topOf(entry.widget)
  entry.tries = entry.tries + 1
  if depth == 0 then return false end           -- still orphaned: try again on the next tick
  if attached(top) then return true end
  local bar = build(top)
  if not bar then return true end
  S.bars[#S.bars + 1] = bar
  log(string.format("bar attached at the %s (%s)", CFG.anchor, bar.png and "images" or "without images"))
  if cur.m then
    bar.cur = cur.m
    repaint(bar)
  end
  poll()
  return true
end

-- Outside Zombies the HUD widget names are unknown, so the bar is added to the HUD root itself, once, as long as no
-- Zombies HUD widget was seen (that path has its own, better parent).
local function tryRoot()
  if S.rootDone or S.sawHud then return true end
  if inFrontend() then return false end
  if readProgress() == nil then return false end
  local okR, root = pcall(function() return LUI.GetRoot() end)
  if not okR or not root then return false end
  if attached(root) then S.rootDone = true; return true end
  local bar = build(root)
  if not bar then S.rootDone = true; return true end
  bar.root = true
  S.bars[#S.bars + 1] = bar
  S.rootDone, S.rootBar = true, true
  log("bar attached to the HUD root (Multiplayer / Endgame)")
  if cur.m then
    bar.cur = cur.m
    repaint(bar)
  end
  poll()
  return true
end

local ensureTimer
local addPauseEntry, openMenu, syncArrow        -- the settings entry, page and length row, defined below
local function onBuilt(t, widget)
  local name = typeName(t)
  if name then S.sawHud = true end
  ensureTimer()
  if name and widget and #S.pending < 6 then
    S.pending[#S.pending + 1] = { widget = widget, name = name, tries = 0 }
  end
  addPauseEntry(widget)
end

-- Optional runtime helpers: called by the in-game settings page, and available to another script.
-- A repaint that says why it failed, once, so a broken live update shows in the console instead of only on screen.
local function repaintBar(bar)
  local ok, err = pcall(repaint, bar)
  if not ok and S.repaintErr ~= tostring(err) then
    S.repaintErr = tostring(err)
    log("repaint error: " .. tostring(err))
  end
end

S.SetColour = function(name)
  if name ~= "auto" and not PRESETS[name] then return false, "unknown colour" end
  CFG.colour = name
  S.themeID = nil
  for _, bar in ipairs(S.bars) do repaintBar(bar) end
  -- the page's own accent follows the bar, so the tab strip on an open page is not a colour behind
  if type(S.refreshAccent) == "function" then pcall(S.refreshAccent, colours()) end
  log("colour: " .. name)
  return true
end
S.SetAnchor = function(where)
  if where ~= "top" and where ~= "bottom" then return false, "anchor must be top or bottom" end
  CFG.anchor = where
  for _, bar in ipairs(S.bars) do pcall(reanchor, bar) end
  log("anchor: " .. where)
  return true
end
S.SetText = function(on)
  CFG.showText = on ~= false and on ~= nil
  for _, bar in ipairs(S.bars) do repaintBar(bar) end
  log("text: " .. (CFG.showText and "on" or "off"))
  return CFG.showText
end
S.SetTracker = function(on)
  CFG.showTracker = on ~= false and on ~= nil
  for _, bar in ipairs(S.bars) do repaintBar(bar) end
  log("xp popup: " .. (CFG.showTracker and "on" or "off"))
  return CFG.showTracker
end
-- The bar itself (pill + fill). Off leaves the text where it is, so "just the level" and "just +N XP" are both
-- combinations of these three switches rather than more drawing code.
S.SetBar = function(on)
  CFG.showBar = on ~= false and on ~= nil
  for _, bar in ipairs(S.bars) do
    -- the text and the popup change line with the bar (textDrop), so this is a re-place, not just an alpha change
    pcall(reanchor, bar)
    pcall(repaint, bar)
  end
  log("bar: " .. (CFG.showBar and "on" or "off"))
  return CFG.showBar
end
S.SetPrestige = function(on)
  CFG.showPrestige = on ~= false and on ~= nil
  for _, bar in ipairs(S.bars) do repaintBar(bar) end
  log("prestige prefix: " .. (CFG.showPrestige and "on" or "off"))
  return CFG.showPrestige
end
S.SetTextSize = function(px)
  local n = tonumber(px)
  if n == nil then return false, "size must be a number" end
  if n < TEXT_MIN then n = TEXT_MIN end
  if n > TEXT_MAX then n = TEXT_MAX end
  CFG.textSize = math.floor(n)
  for _, bar in ipairs(S.bars) do repaintBar(bar) end
  -- the engine reports the row's new width a frame after the re-set, so place the popup again once it has
  S.later[#S.later + 1] = { at = S.tick + 1, fn = function()
    for _, bar in ipairs(S.bars) do repaintBar(bar) end
  end }
  log("text size: " .. CFG.textSize)
  return CFG.textSize
end
local function setAlign(where)
  if where ~= "left" and where ~= "center" and where ~= "right" then return false, "left, center or right" end
  return true
end
S.SetTextPos = function(where)
  local okPos = setAlign(where)
  if not okPos then return false, "left, center or right" end
  CFG.textPos = where
  for _, bar in ipairs(S.bars) do repaintBar(bar) end
  -- the engine reports the row's new width a frame after the re-set, so place the popup again once it has
  S.later[#S.later + 1] = { at = S.tick + 1, fn = function()
    for _, bar in ipairs(S.bars) do repaintBar(bar) end
  end }
  log("text position: " .. where)
  return CFG.textPos
end
S.SetTrackerColour = function(name)
  if name ~= "auto" and not PRESETS[name] then return false, "auto or a preset name" end
  CFG.trackerColour = name
  for _, bar in ipairs(S.bars) do repaintBar(bar) end
  log("xp popup colour: " .. name)
  return CFG.trackerColour
end
-- nil/"auto" follows the XP Text size; a number sets the popup's own points.
S.SetTrackerSize = function(px)
  if px == nil or px == "auto" then
    CFG.trackerAuto = true
  else
    local n = tonumber(px)
    if n == nil then return false, "auto or a number" end
    if n < TEXT_MIN then n = TEXT_MIN end
    if n > TEXT_MAX then n = TEXT_MAX end
    CFG.trackerAuto, CFG.trackerSize = false, math.floor(n)
  end
  for _, bar in ipairs(S.bars) do repaintBar(bar) end
  log("xp popup size: " .. (CFG.trackerAuto and "auto" or tostring(CFG.trackerSize)))
  return CFG.trackerAuto and "auto" or CFG.trackerSize
end
S.SetLook = function(name)
  local found = nil
  for _, st in ipairs(LOOKS) do
    if st[1] == name then found = st[1] end
  end
  if found == nil then return false, "unknown bar style" end
  CFG.look = found
  for _, bar in ipairs(S.bars) do
    bar.fillW = -1
    -- a throw is logged once instead of being swallowed
    local ok, err = pcall(setFill, bar, bar.cur and bar.cur.frac or 0)
    if not ok then log("style error: " .. tostring(err)) end
  end
  log("bar look: " .. found)
  return found
end
-- The length grows to the right from a fixed left end, so this re-places the pill and the fill and nothing else:
-- the label, the popup and the soft light are placed from the left end and do not move.
S.SetWidth = function(px)
  local w = tonumber(px)
  if w == nil then return false, "width must be a number" end
  if w < WIDTH_MIN then w = WIDTH_MIN end
  if w > WIDTH_MAX then w = WIDTH_MAX end
  CFG.width = math.floor(w)
  for _, bar in ipairs(S.bars) do pcall(reanchor, bar); pcall(repaint, bar) end
  log("bar length: " .. CFG.width)
  return CFG.width
end
S.presets = PRESETS

-- The starting values, so a Reset row means DEFAULTS, not "whatever they were when the page opened".
local function defaults()
  return makeConfig(DEFAULTS)
end

local function clampWidth()
  if CFG.width < WIDTH_MIN then CFG.width = WIDTH_MIN end
  if CFG.width > WIDTH_MAX then CFG.width = WIDTH_MAX end
end
local function repaintAll()
  for _, bar in ipairs(S.bars) do
    bar.fillW = -1
    pcall(reanchor, bar)
    pcall(repaint, bar)
  end
end
-- Per-tab resets: each tab puts its own part back to DEFAULTS, so a reset never surprises you by touching a switch
-- on another tab.
S.ResetBar = function()
  local d = defaults()
  CFG.showBar, CFG.colour, CFG.width, CFG.anchor, CFG.look = d.showBar, d.colour, d.width, d.anchor, d.look
  clampWidth()
  syncArrow()
  S.themeID = nil
  if type(S.refreshAccent) == "function" then pcall(S.refreshAccent, colours()) end
  repaintAll()
  log("bar restored to the defaults")
  return true
end
S.ResetText = function()
  local d = defaults()
  CFG.showText, CFG.showPrestige, CFG.textSize, CFG.textPos = d.showText, d.showPrestige, d.textSize, d.textPos
  repaintAll()
  log("text restored to the defaults")
  return true
end
S.ResetPopup = function()
  local d = defaults()
  CFG.showTracker, CFG.trackerColour = d.showTracker, d.trackerColour
  CFG.trackerAuto, CFG.trackerSize = d.trackerAuto, d.trackerSize
  repaintAll()
  log("xp popup restored to the defaults")
  return true
end
S.Reset = function()
  local d = defaults()
  CFG.anchor, CFG.showText, CFG.showTracker, CFG.colour = d.anchor, d.showText, d.showTracker, d.colour
  CFG.showBar, CFG.showPrestige, CFG.textPos = d.showBar, d.showPrestige, d.textPos
  CFG.textSize, CFG.trackerColour, CFG.look = d.textSize, d.trackerColour, d.look
  CFG.trackerAuto, CFG.trackerSize = d.trackerAuto, d.trackerSize
  CFG.width = d.width
  clampWidth()
  syncArrow()
  S.themeID = nil
  if type(S.refreshAccent) == "function" then pcall(S.refreshAccent, colours()) end
  repaintAll()
  log("everything restored to the defaults")
  return true
end

-- One save per change, in one place: every setter and every reset returns through here, so a setter added later
-- cannot forget to save. A rejected call (it returned false) writes nothing. `pack`/`unpack(t, 1, n)` keep a setter's
-- exact return count, so a `nil` second return does not appear where a setter returned only one value.
local function pack(...) return { n = select("#", ...), ... } end
-- Lua 5.1 has `unpack`; newer runtimes have it under `table`. `or` short-circuits, so 5.1 never looks below.
local unpackValues = rawget(_G, "unpack") or table.unpack
for _, name in ipairs({ "SetColour", "SetAnchor", "SetText", "SetTracker", "SetBar", "SetPrestige",
    "SetTextSize", "SetTextPos", "SetTrackerColour", "SetTrackerSize", "SetLook", "SetWidth",
    "ResetBar", "ResetText", "ResetPopup", "Reset" }) do
  local fn = S[name]
  S[name] = function(...)
    local out = pack(fn(...))
    if out[1] ~= false then pcall(persist) end
    return unpackValues(out, 1, out.n)
  end
end
S.afterStored = repaintAll      -- a store read late (the dvar filled after load) repaints the bars it changed

-- ---------------------------------------------------------------------------------------------------------
-- The in-game settings page. Opened from a row this mod adds to the in-match pause panel
-- (`zmpausemenubuttons`, the client's own ZM pause list), and from `XpHudOverlay.Menu()`.
--
-- It is built from the two widgets that panel itself builds in a match - `LUI.UIVerticalList` and
-- `MenuBuilder.BuildRegisteredType("genericbutton", ...)` - so it needs nothing the match VM does not already have,
-- which is the whole reason for not using the frontend's fly-in list. Each row's action repaints the bar behind the
-- page: no rebuild, so "live" is the same three SetAlpha calls the bar uses everywhere else.
local TABS = {
  { "general", "General" },
  { "bar", "XP Bar" },
  { "text", "XP Text" },
  { "popup", "XP Popup" },
}
local COLOUR_CYCLE = { "auto", "giant", "soe", "blue", "cyan", "ice", "gold", "red", "green", "violet" }
local MENU = { id = nil, tab = "general", open = false, accent = { texts = {}, boxes = {} } }

local function later(ticks, fn)
  S.later[#S.later + 1] = { at = S.tick + (ticks or 1), fn = fn }
end

local function flowManager()
  local lui = rawget(_G, "LUI")
  local fm = type(lui) == "table" and lui.FlowManager or nil
  if type(fm) ~= "table" or type(fm.RequestPopupMenu) ~= "function" then return nil end
  return fm
end

local function closeMenu()
  local fm = flowManager()
  if fm == nil or MENU.id == nil then return false end
  local ok, err = pcall(fm.RequestLeaveMenuByName, MENU.id, true)
  if not ok then log("could not close the settings page: " .. tostring(err)) end
  MENU.open = false
  return ok
end

-- Is the page actually on the stack? The engine closes it on its own back button, which never tells us.
local function menuInStack()
  local fm = flowManager()
  if fm == nil or MENU.id == nil then return false end
  if type(fm.IsInStack) ~= "function" then return MENU.open end
  local ok, v = pcall(fm.IsInStack, MENU.id)
  return ok and v == true
end

local function nextColour(cur)
  for i = 1, #COLOUR_CYCLE do
    if COLOUR_CYCLE[i] == cur then return COLOUR_CYCLE[i % #COLOUR_CYCLE + 1] end
  end
  return COLOUR_CYCLE[1]
end

local ALIGN_CYCLE = { "left", "center", "right" }
local function nextAlign(cur)
  for i = 1, #ALIGN_CYCLE do
    if ALIGN_CYCLE[i] == cur then return ALIGN_CYCLE[i % #ALIGN_CYCLE + 1] end
  end
  return "center"
end

local function lookName(id)
  for _, st in ipairs(LOOKS) do
    if st[1] == id then return st[2] end
  end
  return "Line"
end
local function nextLook(cur)
  for i = 1, #LOOKS do
    if LOOKS[i][1] == cur then return LOOKS[i % #LOOKS + 1][1] end
  end
  return LOOKS[1][1]
end

-- The small popup, in 1920x1080 units, top-left origin: 620 x 348, centred. The page is deliberately not
-- full-screen - it sits beside the pause panel instead of over the whole view.
local PANEL_L, PANEL_T, PANEL_R, PANEL_B = 650, 372, 1270, 720
local TAB_L, TAB_TOP, TAB_H, TAB_W, TAB_GAP = 670, 418, 24, 132, 8
local ROW_L, ROW_R, ROW_TOP, ROW_H, ROW_GAP = 670, 1250, 460, 38, 2

-- One row: label is a function so a row can be refreshed in place after its action ran.
local function menuRows()
  local rows = {}
  if MENU.tab == "bar" then
    rows[#rows + 1] = { arrow = true, title = "Bar length", value = "length" }
    rows[#rows + 1] = { label = function() return "Bar: " .. (CFG.showBar and "ON" or "OFF") end,
      action = function() S.SetBar(not CFG.showBar) end }
    rows[#rows + 1] = { label = function() return "Colour: " .. string.upper(CFG.colour) end,
      action = function() S.SetColour(nextColour(CFG.colour)) end }
    rows[#rows + 1] = { label = function() return "Look: " .. lookName(CFG.look) end,
      action = function() S.SetLook(nextLook(CFG.look)) end }
    rows[#rows + 1] = { label = function() return "Position: " .. string.upper(CFG.anchor) end,
      action = function() S.SetAnchor(CFG.anchor == "top" and "bottom" or "top") end }
    rows[#rows + 1] = { label = function() return "Reset bar" end, action = function() S.ResetBar() end }
  elseif MENU.tab == "text" then
    rows[#rows + 1] = { label = function() return "Text: " .. (CFG.showText and "ON" or "OFF") end,
      action = function() S.SetText(not CFG.showText) end }
    rows[#rows + 1] = { label = function() return "Prestige: " .. (CFG.showPrestige and "ON" or "OFF") end,
      action = function() S.SetPrestige(not CFG.showPrestige) end }
    rows[#rows + 1] = { label = function() return "Size: " .. CFG.textSize end,
      action = function() S.SetTextSize(CFG.textSize >= TEXT_MAX and TEXT_MIN or CFG.textSize + 1) end }
    rows[#rows + 1] = { label = function() return "Position: " .. string.upper(CFG.textPos) end,
      action = function() S.SetTextPos(nextAlign(CFG.textPos)) end }
    rows[#rows + 1] = { label = function() return "Reset text" end, action = function() S.ResetText() end }
  elseif MENU.tab == "popup" then
    rows[#rows + 1] = { label = function() return "Popup: " .. (CFG.showTracker and "ON" or "OFF") end,
      action = function() S.SetTracker(not CFG.showTracker) end }
    rows[#rows + 1] = { label = function() return "Size: " .. (CFG.trackerAuto and "AUTO" or tostring(CFG.trackerSize)) end,
      action = function()
        -- AUTO -> 11..15 -> AUTO
        if CFG.trackerAuto then
          S.SetTrackerSize(TEXT_MIN)
        elseif CFG.trackerSize >= TEXT_MAX then
          S.SetTrackerSize("auto")
        else
          S.SetTrackerSize(CFG.trackerSize + 1)
        end
      end }
    rows[#rows + 1] = { label = function() return "Colour: " .. string.upper(CFG.trackerColour) end,
      action = function() S.SetTrackerColour(nextColour(CFG.trackerColour)) end }
    rows[#rows + 1] = { label = function() return "Reset popup" end, action = function() S.ResetPopup() end }
  else
    rows[#rows + 1] = { label = function() return "Operator XP HUD   " .. VERSION end }
    rows[#rows + 1] = { label = function() return "Reset everything" end, action = function() S.Reset() end }
    rows[#rows + 1] = { label = function() return "Close" end, action = function() closeMenu() end }
  end
  return rows
end

-- The length row. `GenericArrowButton` + `LUI.AddUIArrowTextButtonLogic` is the client's own left/right option row
-- (`ui\widgets\arrowbuttonlogic.dec.lua:237-246`, and `genericbuttonlistflyin.dec.lua:28-40` builds it the same
-- way). If either is not in this VM the row falls back to a button that steps the length and wraps.
local function nextWidth(cur)
  local w = cur + WIDTH_STEP
  if w > WIDTH_MAX then w = WIDTH_MIN end
  return w
end

local function arrowRow(row, ctrl)
  local ok, ab = pcall(MenuBuilder.BuildRegisteredType, "GenericArrowButton", { controllerIndex = ctrl })
  if not ok or ab == nil then return nil end
  pcall(function() ab.id = "zxpLength" end)
  pcall(function() ab:SetAnchorsAndPosition(0, 0, 0, 1, 0, 0, 0, ROW_H) end)
  pcall(function() ab.genericoptionbuttonbase.title:setText(row.title or "", 0) end)
  local labels, index = {}, 1
  for w = WIDTH_MIN, WIDTH_MAX, WIDTH_STEP do
    labels[#labels + 1] = tostring(w)
    if w == CFG.width then index = #labels end
  end
  local okL = pcall(function()
    LUI.AddUIArrowTextButtonLogic(ab, ctrl, {
      labels = labels,
      defaultValue = index,
      action = function(value) S.SetWidth(WIDTH_MIN + (value - 1) * WIDTH_STEP) end,
    })
  end)
  if not okL then return nil end
  MENU.arrow = ab                                   -- so a reset can move the arrow back to the file's length
  return ab
end

-- Put the length row's own value back in step with CFG.width after a reset changed it behind the arrow's back.
syncArrow = function()
  if MENU.arrow == nil or type(MENU.arrow.SetCurrentValue) ~= "function" then return end
  local index = math.floor((CFG.width - WIDTH_MIN) / WIDTH_STEP) + 1
  pcall(MENU.arrow.SetCurrentValue, MENU.arrow, index)
end

local function pageText(menu, str, size, l, r, top, bottom, align, rgb)
  local t = LUI.UIStyledText.new()
  t:SetAnchorsAndPosition(0, 1, 0, 1, l, r, top, bottom)
  local fonts = rawget(_G, "FONT_HANDLE")
  local font = type(fonts) == "table" and (fonts.PrimaryBold or fonts.PrimaryRegular) or nil
  if font then pcall(t.SetFont, t, font) end
  local pt = rawget(_G, "_PT")
  if type(pt) ~= "number" then pt = 1 end
  pcall(t.SetFontSize, t, size * pt)
  pcall(t.SetWordWrap, t, false)
  pcall(t.SetAlignment, t, align or 0)
  if rgb then pcall(t.SetRGB, t, rgb, 0) end
  pcall(function() t:setText(str, 0) end)
  menu:addElement(t)
  return t
end

-- A flat coloured rectangle: the panel's own backer and the 3 px accent bar under the active tab.
local function pageBox(menu, l, r, top, bottom, rgb, alpha)
  local ok, e = pcall(function() return LUI.UIImage.new() end)
  if not ok or e == nil then return nil end
  e:SetAnchorsAndPosition(0, 1, 0, 1, l, r, top, bottom)
  local wm = whiteMat()
  if wm then pcall(function() e:setImage(wm, 0) end) end
  if rgb then pcall(function() e:SetRGB(rgb, 0) end) end
  pcall(function() e:SetAlpha(alpha or 1, 0) end)
  menu:addElement(e)
  return e
end

-- L1 / R1 (the shoulder callbacks) and a click on the strip move between the tabs; on keyboard the same actions fire
-- through the bind. `switchTabTo` is the click's entry: it only re-opens when the tab actually changes.
local function switchTabTo(key)
  if MENU.tab == key then return end
  MENU.tab = key
  if menuInStack() then
    closeMenu()
    later(1, function() pcall(openMenu) end)
  end
end

local function switchTab(dir)
  local i = 1
  for k, t in ipairs(TABS) do if t[1] == MENU.tab then i = k end end
  i = (i - 1 + dir) % #TABS + 1
  switchTabTo(TABS[i][1])
end

-- The page itself. FlowManager builds it for the type registered in openMenu.
local function buildPage(id)
  return function()
    local cls = LUI.UIVerticalNavigatorMenu
    local menu = (type(cls) == "table" and type(cls.new) == "function") and cls.new() or LUI.UIElement.new()
    menu.id = id
    if cls == nil then log("settings page: no UIVerticalNavigatorMenu, rows will not navigate") end
    local ctrl = controller()
    local C = colours()
    -- the window: a dark backer with one accent rule along its top edge
    MENU.accent = { texts = {}, boxes = {} }
    local rule = pageBox(menu, PANEL_L, PANEL_R, PANEL_T, PANEL_T + 3, C.accent, 0.9)
    if rule then MENU.accent.boxes[#MENU.accent.boxes + 1] = rule end
    pageBox(menu, PANEL_L, PANEL_R, PANEL_T, PANEL_B, 0x000000, 0.62)
    pageText(menu, "OPERATOR XP HUD", 20, PANEL_L + 20, PANEL_R - 20, PANEL_T + 12, PANEL_T + 40, 0, 0xFFFFFF)
    pageText(menu, "L1 / R1", 12, PANEL_L + 20, PANEL_R - 20, TAB_TOP, TAB_TOP + TAB_H, 2, 0x9A9A9A)
    -- the tab strip: the active tab in the accent colour with a rule under it, the other one grey. Each tab also has
    -- an invisible mouse-only button over it, so a click switches tabs as well as L1/R1.
    for i = 1, #TABS do
      local l = TAB_L + (i - 1) * (TAB_W + TAB_GAP)
      local active = TABS[i][1] == MENU.tab
      local tab = pageText(menu, string.upper(TABS[i][2]), 16, l, l + TAB_W, TAB_TOP, TAB_TOP + TAB_H, 0,
        active and C.accent or 0x9A9A9A)
      if active then
        MENU.accent.texts[#MENU.accent.texts + 1] = tab
        local under = pageBox(menu, l, l + TAB_W, TAB_TOP + TAB_H + 2, TAB_TOP + TAB_H + 5, C.accent, 0.9)
        if under then MENU.accent.boxes[#MENU.accent.boxes + 1] = under end
      end
      local key = TABS[i][1]
      pcall(function()
        local hit = LUI.UIButton.new()
        hit:SetAnchorsAndPosition(0, 1, 0, 1, l, l + TAB_W, TAB_TOP, TAB_TOP + TAB_H)
        pcall(function() hit:SetFocusable(false) end)      -- mouse only: the list keeps the pad's focus
        hit:addEventHandler("button_action", function() switchTabTo(key) end)
        hit:registerEventHandler("mousedownleft", function() switchTabTo(key) end)
        menu:addElement(hit)
      end)
    end
    local okL, list = pcall(function() return LUI.UIVerticalList.new() end)
    if not okL or list == nil then
      log("settings page: LUI.UIVerticalList is not in this VM")
      return menu
    end
    list:SetSpacing(ROW_GAP)
    list:SetAnchorsAndPosition(0, 1, 0, 1, ROW_L, ROW_R, ROW_TOP, PANEL_B - 20)
    menu:addElement(list)
    menu.VerticalList = list                       -- what ACTIONS.GainFocus looks for
    local rows = menuRows()
    local buttons = {}
    for i = 1, #rows do
      local row = rows[i]
      local btn
      if row.arrow then btn = arrowRow(row, ctrl) end
      if btn == nil and row.arrow then
        -- no arrow widget in this VM: the same setting as a row that steps and wraps
        row = { label = function() return "Bar length: " .. CFG.width end,
          action = function() S.SetWidth(nextWidth(CFG.width)) end }
        rows[i] = row
      end
      if btn == nil then
        local ok, made = pcall(MenuBuilder.BuildRegisteredType, "genericbutton", { controllerIndex = ctrl })
        if ok and made then
          btn = made
          pcall(function() btn.id = "zxp" .. i end)
          pcall(function() btn:SetAnchorsAndPosition(0, 0, 0, 1, 0, 0, 0, ROW_H) end)
          pcall(function() btn.text:setText(row.label(), 0) end)
          if row.action then
            pcall(function()
              btn:addEventHandler("button_action", function()
                local okA, err = pcall(row.action)
                if not okA then log("settings row failed: " .. tostring(err)) end
                for k = 1, #buttons do
                  if not buttons[k].arrow then
                    pcall(function() buttons[k].btn.text:setText(buttons[k].row.label(), 0) end)
                  end
                end
              end)
            end)
          end
        end
      end
      if btn ~= nil then
        pcall(function() list:addElement(btn) end)
        buttons[#buttons + 1] = { btn = btn, row = row, arrow = row.arrow }
      end
    end
    if #buttons == 0 then log("settings page: no row could be built (is genericbutton registered?)") end
    pcall(function() list:processEvent({ name = "gain_focus", controller = ctrl }) end)
    if menu.VerticalList ~= nil then
      pcall(function()
        -- Returning true swallows the event: without it Esc also reaches the pause menu underneath and the game
        -- resumes while our page is still closing.
        menu:AddGamepadEventCallback("button_shoulderl", function() switchTab(-1); return true end)
        menu:AddGamepadEventCallback("button_shoulderr", function() switchTab(1); return true end)
        menu:AddGamepadEventCallback("button_secondary", function() closeMenu(); return true end)
      end)
    end
    return menu
  end
end

-- SetColour calls this with the new palette, so an open page's accent follows the bar instead of lagging a colour.
S.refreshAccent = function(C)
  for _, e in ipairs(MENU.accent.texts) do pcall(function() e:SetRGB(C.accent, 0) end) end
  for _, e in ipairs(MENU.accent.boxes) do pcall(function() e:SetRGB(C.accent, 0) end) end
end

openMenu = function(tab)
  if tab ~= nil then
    for _, t in ipairs(TABS) do if t[1] == tab then MENU.tab = tab end end
  end
  local fm = flowManager()
  if fm == nil then
    log("settings page: LUI.FlowManager is not in this VM")
    return false, "no FlowManager"
  end
  local builder = rawget(_G, "MenuBuilder")
  if type(builder) ~= "table" or type(builder.registerType) ~= "function" then
    log("settings page: MenuBuilder.registerType is not in this VM")
    return false, "no MenuBuilder"
  end
  local okId, id = pcall(H, "zmxpsettings")
  if not okId or id == nil then
    log("settings page: xhash refused the page id")
    return false, "no id"
  end
  MENU.id = id
  local okR, errR = pcall(builder.registerType, id, buildPage(id))
  if not okR then log("settings page: registerType failed: " .. tostring(errR)) return false, tostring(errR) end
  if menuInStack() then
    -- the engine leaves a menu asynchronously, so a tab switch closes and re-opens: never two pages at once
    closeMenu()
    later(2, function() pcall(openMenu) end)
    return true
  end
  local ok, err = pcall(fm.RequestPopupMenu, nil, id, true, controller(), false, {})
  if not ok then log("settings page did not open: " .. tostring(err)) return false, tostring(err) end
  MENU.open = true
  log("settings page opened (" .. MENU.tab .. ")")
  return true
end
S.Menu = openMenu
S.CloseMenu = closeMenu

-- The pause-menu row. Three ways in, so it appears whichever path this client takes:
--   1. `onBuilt` sees every widget `MenuBuilder.BuildRegisteredType` returns - but only if the client builds the
--      pause panel through that function and only if it is this VM's copy of it;
--   2. the *registered constructor* of the pause panel is wrapped, which does not depend on the id or on the build
--      path - only on the type being registered in this VM;
--   3. `MenuBuilder.registerType` is wrapped, for the case where the panel's file is loaded after this script.
-- Everything is idempotent (`list.zmXpMenuButton` per list, `MINE` per wrapper), so the three cannot stack.
local PAUSE_TYPES = { "zmpausemenubuttons", "mppausemenubuttons" }
local PAUSE_KEYS = {}
for _, n in ipairs(PAUSE_TYPES) do
  PAUSE_KEYS[n] = true
  pcall(function() PAUSE_KEYS[tostring(H(n))] = true end)
end
local function isPauseType(name)
  if type(name) == "string" then return PAUSE_KEYS[name] == true or PAUSE_KEYS[name:lower()] == true end
  return PAUSE_KEYS[tostring(name)] == true
end

local function appendPauseRow(list, why)
  if list == nil or S.addingRow then return false end
  local okDone, done = pcall(function() return list.zmXpMenuButton end)
  if okDone and done ~= nil then return true end
  S.addingRow = true                       -- the row's own `genericbutton` build must not look like a pause panel
  local ok, btn = pcall(MenuBuilder.BuildRegisteredType, "genericbutton", { controllerIndex = controller() })
  S.addingRow = false
  if not ok or btn == nil then
    log("could not add the pause-menu row (genericbutton is not in this VM)")
    return false
  end
  pcall(function() btn.id = "zmXpMenuButton" end)
  pcall(function() btn:SetAnchorsAndPosition(0, 0, 0, 1, 0, 0, 0, 51) end)
  pcall(function() btn.text:SetLeft(52, 0) end)
  pcall(function() btn.text:setText("Operator XP HUD", 0) end)
  pcall(function() btn:addEventHandler("button_action", function() openMenu() end) end)
  local okA = pcall(function() list:addElement(btn) end)
  if not okA then
    log("could not attach the pause-menu row")
    return false
  end
  pcall(function() list.zmXpMenuButton = btn end)
  log("settings row added to the pause menu (" .. tostring(why) .. ")")
  return true
end

addPauseEntry = function(widget)
  if widget == nil then return end
  local okId, id = pcall(function() return widget.id end)
  if not okId or id ~= "zmpausemenubuttons" then return end
  appendPauseRow(widget, "build hook")
end

-- Wrap one pause type that is already registered. `MINE[ctor]` marks the wrappers this mod made, so a re-registered
-- original is wrapped again (the panel may load its file more than once) while our own wrapper never wraps itself.
-- A Lua function cannot carry a field, so the markers live in tables keyed by the function itself.
local WRAPPED, MINE = {}, {}
local function wrapPauseType(name)
  local MB = rawget(_G, "MenuBuilder")
  if type(MB) ~= "table" or type(MB.GetConstructorForType) ~= "function" then return false end
  local okK, key = pcall(H, name)
  if not okK or key == nil then return false end
  local okG, ctor = pcall(MB.GetConstructorForType, key)
  if not okG or type(ctor) ~= "function" or MINE[ctor] then return false end
  local mine = function(...)
    local list = ctor(...)
    pcall(appendPauseRow, list, "constructor hook")
    return list
  end
  WRAPPED[ctor], WRAPPED[mine], MINE[mine] = true, true, true
  local okR = pcall(MB.registerType, key, mine)
  return okR
end

local function installRegisterHook()
  local MB = rawget(_G, "MenuBuilder")
  if type(MB) ~= "table" or type(MB.registerType) ~= "function" then return false end
  if S.registerHooked then return true end
  local native = MB.registerType
  local mine = function(name, ctor, ...)
    if isPauseType(name) and type(ctor) == "function" and not MINE[ctor] then
      local orig = ctor
      ctor = function(...)
        local list = orig(...)
        pcall(appendPauseRow, list, "register hook")
        return list
      end
      WRAPPED[orig], WRAPPED[ctor], MINE[ctor] = true, true, true
    end
    return native(name, ctor, ...)
  end
  S.registerHooked = true
  MB.registerType = mine
  return true
end

do
  local hooked = 0
  if installRegisterHook() then hooked = 1 end
  for _, name in ipairs(PAUSE_TYPES) do
    if wrapPauseType(name) then hooked = hooked + 1 end
  end
  if hooked > 0 then
    log("pause-menu row hooked (" .. hooked .. " path(s))")
  else
    log("this VM has no MenuBuilder to hook - the page is still available as XpHudOverlay.Menu()")
  end
end

local builder = rawget(_G, "MenuBuilder")
if builder and type(builder.BuildRegisteredType) == "function" then
  local native = builder.BuildRegisteredType
  local mine = function(t, data, ...)
    local m = native(t, data, ...)
    if S.enabled then pcall(onBuilt, t, m) end
    return m
  end
  builder.BuildRegisteredType = mine
else
  log("MenuBuilder.BuildRegisteredType is missing - the bar cannot attach")
end

-- The repeating job: an invisible element under the UI root that re-arms itself with Wait, as Kronos runs its own
-- timers. Reading the dvars four times a second is the only work done while nothing changes.
local timerEl
ensureTimer = function()
  if timerEl then
    local ok, parent = pcall(function() return timerEl:getParent() end)
    if ok and parent then return end
  end
  local okR, root = pcall(function() return LUI.GetRoot() end)
  if not okR or not root then return end
  local okE, el = pcall(function() return LUI.UIElement.new() end)
  if not okE or not el then return end
  root:addElement(el)
  timerEl = el
  S.gen = S.gen + 1
  local myGen = S.gen
  local function tick()
    if not S.enabled or myGen ~= S.gen then return end
    S.tick = S.tick + 1
    -- Work the settings page asked for one or two ticks later (the engine leaves a menu asynchronously).
    if #S.later > 0 then
      local keep = {}
      for _, a in ipairs(S.later) do
        if S.tick >= a.at then pcall(a.fn) else keep[#keep + 1] = a end
      end
      S.later = keep
    end
    if #S.pending > 0 then
      local keep = {}
      for _, e in ipairs(S.pending) do
        local ok, done = pcall(tryAttach, e)
        if not (ok and done) and e.tries < 60 then keep[#keep + 1] = e end
      end
      S.pending = keep
    end
    -- While the bar is off screen (frontend, menus) the values are read a quarter as often.
    if #S.bars > 0 and (not S.hidden or S.tick % 4 == 0) then
      local okP, errP = pcall(poll)
      if not okP and S.pollErr ~= tostring(errP) then
        S.pollErr = tostring(errP)
        log("poll error: " .. tostring(errP))
      end
    end
    if not S.rootDone and not S.sawHud then
      S.rootChecks = (S.rootChecks or 0) + 1
      if S.rootChecks >= 4 then S.rootChecks = 0; pcall(tryRoot) end
    end
    el:Wait(TICK_MS).onComplete = tick
  end
  el:Wait(TICK_MS).onComplete = tick
end

-- Start the timer now if the UI root already exists (it may not this early); onBuilt also starts it on the first widget.
pcall(ensureTimer)

-- The saved settings, if there are any: read once here, and again from the tick until the GSC has filled the dvar
-- (that happens when a level starts, so in the menus the bar is hidden and these are still the built-in defaults).
pcall(applyStored)

log(VERSION .. " loaded; nothing is drawn until a match starts (settings so far: " .. CFG.anchor .. ", " .. CFG.colour .. ")"
  .. (CFG.showText and "" or ", text hidden")
  .. (CFG.showTracker and "" or ", tracker hidden"))
