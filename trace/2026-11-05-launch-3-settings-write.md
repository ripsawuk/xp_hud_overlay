# Launch 3 - the settings write is refused (v1.1 / 87,876 B, 2026-11-05)

One launch, one question: does a press on the settings page write `zm_xp_hud_config`, and does it come back?

**Answer: no. The store refused the write and nothing reached disk.**

## The console, as pasted

    [ZmXpHud] pause-menu row hooked (1 path(s))
    [ZmXpHud] v1.1 loaded: bottom, green
    [ZmXpHud] settings: no zm_xp_hud_config yet - the defaults stand
    [ZmXpHud] bar attached to the HUD root (Multiplayer / Endgame)
    [ZmXpHud] xp source: dvar
    [ZmXpHud] label width from the text element (getElementTextDims)
    [ZmXpHud] settings row added to the pause menu (register hook)
    [ZmXpHud] settings page opened (general)
    [ZmXpHud] settings page opened (bar)
    [ZmXpHud] colour: violet
    [ZmXpHud] settings: the zm_xp_hud_config write did not read back

Reading it line by line:

| Line | What it settles |
|---|---|
| `v1.1 loaded` | The game holds the 87,876 B build, not the renumbered one. The reinstall had not been run. |
| `settings: no zm_xp_hud_config yet` | `readallfilecontent` is in the VM and answered, with nothing. The global is not missing. |
| `pause-menu row hooked (1 path(s))` then `settings row added ... (register hook)` | X7's entry point still works (D8). |
| `settings page opened (general)`, `(bar)` | The tab strip and the page still work (D9/D14). |
| `colour: violet` | The press reached `SetColour`, which is the setters' wrapper, so `persist()` ran (D29's wrapper list). |
| `the zm_xp_hud_config write did not read back` | `pcall(storeWrite)` failed, or the read-back returned nothing. **The line does not say which** - the reason was thrown away. That is the defect this build fixes. |

## The disk, before and after

Baseline `trace\2026-11-05-profile-before-x8.txt` (76 files, SHA-256 each), taken before the launch. After the press
and the game closing:

    before: 76  now: 76
    === NEW files ===
    === GONE files ===

So no file was created for the store, under any name, in either profile directory. The only writes are the game's own
`*.csf` at 23:53. **The write did not reach disk** - it is not a read-back-only failure that a restart would have
redeemed.

## What this refutes, and what it leaves open

- Refuted: "the store takes the write and the read-back is just impatient". Nothing landed.
- Refuted: "FileStorage is not in the mod's VM". It answered the read.
- Open: **why** the write was refused. The three candidates, which the instrumented build distinguishes in one press:
  1. the call raised - wrong argument count or a name of the wrong type;
  2. the call returned but the store keys by **xhash** (`#x0416...`-style), so a plain string name is written where
     the read will not look (the observed call at `trace\p5y\console.txt:311` passes a xhash name, though that may be
     the probe's own);
  3. the store accepts the call and keeps nothing for a name the client never registered.

## The instrument (90449 B)

`verify.cmd` -> **296 / 296**. What changed, all inside the store block:

- **Four shapes, not two.** `(controller, name, text)`, `(controller, xhash, text)`, `(name, text)`, `(xhash, text)`.
  A read tries all four; a write takes the known shape or walks the rest.
- **The verdict is one tick late.** A store that flushes at the end of a frame cannot be read in the same one, and
  that is precisely the difference between "saved" and "saved nowhere".
- **The reason is kept.** `pcall`'s message is no longer discarded.
- **The line names the shape that worked**, so the next launch ends the guessing:
  `settings: saved to zm_xp_hud_config via controller+name (N bytes)`, or
  `settings: the zm_xp_hud_config write did not read back - controller+name read back nothing; controller+xhash raised: ...`

Three new replay assertions: the plain stub adopts `controller+name`; a stub that only answers a xhash name is found
and the log names that shape; a stub that keeps nothing produces one line listing every shape and never says `saved`.

## Next

Install this build, press one setting, and read one line. If it says `via ...`, that shape is now the one it uses and
the same line answers the restart question. If it names four failures, the store itself is the wrong tool and the next
step is a different one - not another guess at this one.
