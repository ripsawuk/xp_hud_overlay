// xp_hud_overlay: keeps the HUD settings across game restarts. The Lua side cannot write a file, so it publishes its
// settings in ONE dvar and this script mirrors that dvar to kronos\xphudoverlay\settings.json with the client's own
// store builtins. It touches no XP, no profile value and no other dvar.
autoexec xp_hud_overlay_store_init()
{
    level thread xp_hud_overlay_store_sync();
}

xp_hud_overlay_store_sync()
{
    nengine_store_load("xphudoverlay", "settings");
    level.xp_hud_overlay_stored = nengine_store_get("xphudoverlay", "cfg");
    if (!isdefined(level.xp_hud_overlay_stored))
    {
        level.xp_hud_overlay_stored = "";
    }
    if (getdvar("xp_hud_overlay_cfg", "") == "")
    {
        // A dvar that does not exist yet ignores a set from Lua, so create it here: the saved text, or "none"
        // (the Lua reads "none" as "nothing saved yet").
        if (level.xp_hud_overlay_stored != "")
        {
            setdvar("xp_hud_overlay_cfg", level.xp_hud_overlay_stored);
        }
        else
        {
            setdvar("xp_hud_overlay_cfg", "none");
        }
    }
    level.xp_hud_overlay_saved = getdvar("xp_hud_overlay_cfg", "");
    for (;;)
    {
        wait 0.5;
        if (getdvar("xp_hud_overlay_cfg", "") != level.xp_hud_overlay_saved)
        {
            level.xp_hud_overlay_saved = getdvar("xp_hud_overlay_cfg", "");
            nengine_store_set("xphudoverlay", "cfg", level.xp_hud_overlay_saved);
            nengine_store_save("xphudoverlay", "settings");
        }
    }
}
