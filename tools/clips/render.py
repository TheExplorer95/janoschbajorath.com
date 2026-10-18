"""Render the clips of one conference page.

    python tools/clips/render.py                              # all WHERE 2026 clips
    python tools/clips/render.py jump push                    # some; other entries are kept
    python tools/clips/render.py --page sab-2026 gaits push   # the SAB 2026 page
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

import compose

REPO = Path(__file__).resolve().parents[2]
PAGES = ("where-2026", "sab-2026")
"""Each page's entries live in the module of the same name with `-` as `_`, exposing
`CLIPS`, `RUNS`, `LEADING`, `ROOT` and `CHECKPOINT`."""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("names", nargs="*", help="clip entries of the page; all when none")
    parser.add_argument("--page", choices=PAGES, default=PAGES[0])
    parser.add_argument("--root", type=Path, default=None,
                        help="runs root; the page module's ROOT when omitted")
    args = parser.parse_args()
    entries = importlib.import_module(args.page.replace("-", "_"))
    clips = entries.CLIPS
    unknown = [name for name in args.names if name not in clips]
    if unknown:
        parser.error(f"unknown clip(s) {unknown}; known: {', '.join(clips)}")
    root = args.root if args.root is not None else entries.ROOT
    out_dir = REPO / "public" / "videos" / args.page
    manifest_path = REPO / "src" / "data" / f"{args.page}-clips.json"

    for name in args.names or list(clips):
        print(f"rendering {name} …")
        entry = compose.render_clip(clips[name], entries.RUNS, root, out_dir, args.page,
                                    entries.CHECKPOINT, entries.LEADING)
        print(f"  {entry['width']} x {entry['height']}, {entry['duration_s']} s, "
              f"{entry['bytes']} bytes")
        # Read the manifest again at each write, so renders running side by side keep
        # each other's entries.
        manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
        manifest[name] = entry
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
