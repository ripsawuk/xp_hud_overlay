# trace - evidence

One file per observation, named with the date and what was observed. What belongs here, and what does not:

| Belongs | Does not |
|---|---|
| Console pastes containing `[ZMHud]` lines | A description of what a launch "should" print |
| Hashes read back from `mods\zm_xp_hud\` after an install | A hash copied from `PROGRESS.md` |
| Screenshots of the bar, at native resolution | A mock (`make_mock.py` output is a picture of the constants, not the game) |
| A `verify.cmd` transcript that fails | Only the passes |

The rule is the project's own: a claim is a `file:line`, a command and its output, or labelled `UNVERIFIED`.
"Installed" is not evidence; the hash read back from the game folder is.
