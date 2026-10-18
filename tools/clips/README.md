# Clip renderer

Turns the raw experiment recordings of `gait_rl` into the annotated clips of the
conference pages. Designs: `docs/superpowers/specs/2026-09-21-where-2026-clips-design.md`
(WHERE 2026) and `docs/superpowers/specs/2026-10-18-sab-2026-clips-design.md` (SAB 2026).

    conda run -n isaac --no-capture-output python tools/clips/render.py [--page PAGE] [name ...]
    conda run -n isaac --no-capture-output python -m pytest tools/clips/tests -q

Needs Pillow, imageio, imageio-ffmpeg, numpy, pyarrow and `gaitrl` (the `isaac` conda env)
and `npm install` (Fira Sans is read from `node_modules`). Reads raw clips and recordings
in place under the page's runs root (`--root` to override).

`--page` picks the page, its entries module and its files; `where-2026` is the default.

| Page | Entries | Runs root | Checkpoint | Output |
|---|---|---|---|---|
| `where-2026` | `where_2026.py` | `~/code/gait_rl/experiment/WHERE_rev2` | none (`<task>-step-0.mp4`, `evaluations/<task>/`) | `public/videos/where-2026/`, `src/data/where-2026-clips.json` |
| `sab-2026` | `sab_2026.py` | `~/code/gait_rl/experiment/sab_rev` | `7250` (`<task>-7250-step-0.mp4`, `evaluations/<task>/7250/`) | `public/videos/sab-2026/`, `src/data/sab-2026-clips.json` |

Each entries module exposes `CLIPS` (keyed by clip name), `RUNS` (condition key to run
directory), `LEADING` (condition key to the run's behaviour-component count, the poster's
`k`), `ROOT` and `CHECKPOINT`. Only the named entries of a manifest are rewritten; the
rest are kept.

Wording, cuts and pacing live in the entries modules. A cut is refused at construction when
a time is off the 50 fps lattice or a normal-speed stretch would skip the event frame.

## Devices

Besides the WHERE label plate, column headers, footfall strip, joint-target trace and
timeline, a tile can carry two latent devices, both reading the run's own basis and
nominal table through `latent.py` (`gaitrl`'s readers, refused unless they were produced
from the recording's run, checkpoint, precision and latent block):

- **Latent panel** (`Geometry.side_w`): a square beside the robot showing the live latent
  on PC1 and PC2 of the run's basis, with the last 0.6 s as a fading trail in the tile's
  gait colour and the four gaits' rings faint behind it: each gait tile's own cut window,
  projected, so the rings sit on the live points exactly. The axis limits are one square
  over all rings of the clip, shared by every tile.
- **Deviation trace** (`Clip.trace = "latent"`): under the robot, the deviation of the
  latent from its nominal cycle split into the behaviour part (condition colour) and the
  domain part (white); from the event the lines show what the controller reads under the
  tile's `mask`, the withheld group dotted behind its flat line. Each group is divided by
  its nominal cycle amplitude, so 1 reads as "a deviation as large as the gait cycle". The
  plot has axes: y from 0 to one ceiling per condition row over its tiles' cut windows
  (rounded up to a decimal; no tick labels; the title `latent deviation` on the first
  column of each row), x in seconds from the event (the recording's control period),
  ticked at whole seconds; a legend row above each plot names the three line styles.
