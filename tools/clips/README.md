# Clip renderer

Turns the raw experiment recordings of `gait_rl` into the annotated clips of the
WHERE 2026 page. Design: `docs/superpowers/specs/2026-09-21-where-2026-clips-design.md`.

    conda run -n isaac --no-capture-output python tools/clips/render.py [name ...]
    conda run -n isaac --no-capture-output python -m pytest tools/clips/tests -q

Needs Pillow, imageio, imageio-ffmpeg, numpy, pyarrow (the `isaac` conda env) and
`npm install` (Fira Sans is read from `node_modules`). Reads raw clips and recordings in
place under `~/code/gait_rl/experiment/WHERE_rev2` (`--root` to override). Writes
`public/videos/where-2026/<name>.mp4|jpg` and `src/data/where-2026-clips.json`.

Wording, cuts and pacing live in `where_2026.py`. A cut is refused at construction when a
time is off the 50 fps lattice or a normal-speed stretch would skip the event frame.
