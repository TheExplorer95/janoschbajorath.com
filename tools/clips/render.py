"""Render the WHERE 2026 clips.

    python tools/clips/render.py              # all
    python tools/clips/render.py jump push    # some; other manifest entries are kept
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import compose
from where_2026 import CLIPS, RUNS

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "public" / "videos" / "where-2026"
MANIFEST = REPO / "src" / "data" / "where-2026-clips.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="*", help=f"any of: {', '.join(CLIPS)}")
    parser.add_argument("--root", type=Path,
                        default=Path.home() / "code/gait_rl/experiment/WHERE_rev2")
    args = parser.parse_args()
    unknown = [name for name in args.names if name not in CLIPS]
    if unknown:
        parser.error(f"unknown clip(s) {unknown}; known: {', '.join(CLIPS)}")

    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.is_file() else {}
    for name in args.names or list(CLIPS):
        print(f"rendering {name} …")
        manifest[name] = compose.render_clip(CLIPS[name], RUNS, args.root, OUT_DIR)
        print(f"  {manifest[name]['width']} x {manifest[name]['height']}, "
              f"{manifest[name]['duration_s']} s, {manifest[name]['bytes']} bytes")
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
