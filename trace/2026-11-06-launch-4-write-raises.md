# Launch 4 - all four FileStorage write shapes raise (90,449 B / 3A43D079F237451D, 2026-11-06)

Installed (both hashes read back), launched, one Colour press:

    [ZmXpHud] v1.0 loaded: bottom, green
    [ZmXpHud] settings: no zm_xp_hud_config yet - the defaults stand
    [ZmXpHud] colour: violet
    [ZmXpHud] settings: the zm_xp_hud_config write did not read back -
      controller+name raised:  #x0e223f1757dd29ee:12473 : #x0c274e67aca1dee66 (const char *);
      controller+xhash raised: #x0e223f1757dd29ee:12473 : #x0c274e67aca1dee66 (XHash);
      name raised:             #x0e223f1757dd29ee:12468 : #x014aad79ba0554ff9;
      xhash raised:            #x0e223f1757dd29ee:12468 : #x014aad79ba0554ff9

Reading: the read member accepts (0, "zm_xp_hud_config"); the write member raises on every shape. The 3-arg error
names the type of the *name* argument (it changes const char* -> XHash with it), so the engine rejects a name it
does not know, not the argument count. The client's own HUD editor passes the plain string "hud_editor_config" with
Engine.GetFirstActiveController() as the first argument (hudeditorutils.dec.lua:110-114, :2206, :2875).
Two attempts at this criterion have now failed (launch 3: refused silently; launch 4: raised in all shapes).
