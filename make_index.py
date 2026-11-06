"""Builds the Kronos Workshop entry for this mod from the files in mod\\.

  release\\index_entry.json   the object to paste into the "items" list of kronos-data\\index.json
  release\\upload\\            the same files with flat names, ready to attach to the GitHub release

Sizes and SHA-256 hashes are read from the files, so rerun this after any change and paste the new entry.
Usage:  python -I make_index.py
"""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MOD = ROOT / "mod"
OUT = ROOT / "release"
UPLOAD = OUT / "upload"

# Where the files are hosted: a GitHub release on the mod's own repo. Change TAG when the release tag changes.
REPO = "ripsawuk/xp_hud_overlay"
TAG = "v1"
BASE = f"https://github.com/{REPO}/releases/download/{TAG}/"

ENTRY = {
    "id": "xp_hud_overlay",
    "type": "ui",
    "name": "XP HUD Overlay",
    "author": "ripsawuk",
    "image": BASE + "preview.png",
    "version": "1",
    "description": (
        "XP HUD Overlay v1.0. Provides a visible overlay on your HUD to show you live XP being earned in game. "
        "Various customisation options that can be changed in game from positioning, to colours, to bar types "
        "(cats??). Dont like the bar? Disable it. Use the text only. Dont like the text? Disable it, use the bar "
        "only. Adjust to your liking. Currently only captures operator levelling and XP."
    ),
}


def main():
    files = ["mod.json"]
    for sub in ("lua", "scripts", "images"):
        files += sorted(f"{sub}/{p.name}" for p in (MOD / sub).iterdir() if p.is_file())
    if UPLOAD.exists():
        shutil.rmtree(UPLOAD)
    UPLOAD.mkdir(parents=True)
    items = []
    seen = set()
    sha = {}
    for rel in files:
        src = MOD / rel
        flat = Path(rel).name
        assert flat not in seen, f"two files would share the release asset name {flat}"
        seen.add(flat)
        data = src.read_bytes()
        shutil.copyfile(src, UPLOAD / flat)
        sha[flat] = hashlib.sha256(data).hexdigest()
        items.append({
            "name": rel,
            "size": len(data),
            "hash": "",                                  # the wiki: left empty, the reviewer fills in the SHA-256
            "urls": [BASE + flat],
        })
    entry = dict(ENTRY, files=items)
    (OUT / "index_entry.json").write_text(json.dumps(entry, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(items)} files -> {OUT / 'index_entry.json'}")
    print(f"upload these {len(items)} files (+ preview.png) to https://github.com/{REPO}/releases/tag/{TAG}:")
    for it in items:
        print(f"  {Path(it['name']).name:32} {it['size']:>7} B  {sha[Path(it['name']).name][:16]}")


if __name__ == "__main__":
    main()
