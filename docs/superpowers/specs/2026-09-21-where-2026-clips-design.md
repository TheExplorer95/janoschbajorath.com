# WHERE 2026 page — experiment clips: design

Status: DRAFT 2, 2026-09-21. Decisions D1–D6 were taken by Janosch in the design dialogue of
2026-09-21. DRAFT 2 folds an agent review of DRAFT 1 whose findings were re-checked against
the recordings. Of the two points it raised for Janosch, the jump clip's device is decided
(D7) and so is the phone question (D8).

## Goal

The WHERE 2026 page (`/research/where-2026`) shows the poster's experiments as video. The raw
recordings exist; this design covers how they become published clips, how the page presents
them, and the tool that renders them. A reader who has not seen the poster should be able to
tell, from a clip alone, what condition it shows and when the thing that matters happens.

## Decisions taken

| # | Decision |
|---|----------|
| D1 | Clips are self-hosted `<video>` files in the site, not YouTube embeds. The YouTube mode of `<Clip>` stays for later use. |
| D2 | Markers and labels are burned into the video pixels. The page's captions carry the explanation. |
| D3 | The rendering tool lives in this repository under `tools/clips/`. `gait_rl` stays a recorder; nothing about the site's look enters it. |
| D4 | One-encoder clips (capabilities, gaits, domain) show the RECON + BCE run, knowing that four of its forty capabilities robots never stand while all forty PPO robots do. Jump and push show both encoders. |
| D5 | The page layout is free to change where it serves the videos. This supersedes, in `2026-09-17-website-design.md`, the section name "Architecture", the order "figure, caption, clip", the `<Clip title note id? />` signature, the slot "capabilities (abstract)" and YouTube as the page's video mechanism; that document is updated with this work. |
| D6 | Git is Janosch's in both repositories: nothing is committed or pushed by the agent. A push to `main` deploys the site. |
| D7 | The jump clip draws a deviation trace of the joint targets above the footfall strip. DRAFT 1's claim that the strip would show the feet catching up over several strides was refuted by the recordings (see "Raw material"); the strip stays, captioned for what it shows. Re-recording the jump at another clock phase was not chosen. |
| D8 | No phone-specific work in this version (MVP). A clip scales to the screen like any other media; a phone reader who wants the burned-in detail zooms in or uses the player's fullscreen. No second render, no sideways-scrolling grid. The page's viewport must keep pinch-zoom enabled. |

## Raw material

Recorded by `gait_rl`'s `config/eval/video_*.py` on the two rev2 runs, under
`<gait_rl>/experiment/WHERE_rev2/`:

- RECON + BCE: `dynamics-contacts/26-09-15_01-18-50_dynamics-contacts`
- PPO: `rl-only/26-09-15_12-58-26_rl-only`

Per run and task id `<t>`: the clip `evaluations/videos/evaluation/<t>-step-0.mp4`
(1920 × 1080, 50 fps, one frame per control step, starting on the first step after the
warmup) and its recording `evaluations/<t>/evaluation_data_<timestamp>.parquet` with its
`.meta.json`, one row per control step and environment (`env_idx`), warmup rows included and
flagged `warmup`.

| Task id | Frames | Content |
|---|---|---|
| `video_stand`, `video_walk`, `video_trot`, `video_bound` | 499 | one robot, side view, commanded 0 / 0.35 / 1.2 / 2.1 m/s |
| `video_domain` | 499 | eight robots abreast at one trot command, trained domain randomisation and noise |
| `video_jump_advance-quarter` | 499 | trot, clock advanced a quarter cycle |
| `video_push_m0_blind`, `video_push_m100_{identity,leading,trailing}` | 599 | trot, rear view, 100 N towards −y for 0.2 s (0 N for `m0`), latent deviation masked (`leading` = components 1–8, `trailing` = 9–16) |
| `video_capabilities` | 749 | forty robots initialised in random orientations, each recovering to stance and tracking its own command |

Facts the design relies on, checked on the recordings of 2026-09-21:

- A clip has one frame fewer than its recording has post-warmup rows (the writer drops the
  last). The bound of a cut is the clip's own frame count.
- Clip frame = recording row − warmup rows. The warmup is 32 rows for every task except
  `video_capabilities`, where it is 0; it is read per recording (`warmup` column). The
  mapping carries a known uncertainty of one control step (20 ms): the rendered camera may
  lag the recorded state by one step. Marker alignment is accepted to ±1 raw frame.
- The clock jump (`clock_jump_fired`) and the push onset (`push_fired`) both sit at row 176,
  clip frame 144 (2.88 s), in every event clip of both runs, `m0` included. The tool reads
  the row from each recording; it never assumes 144.
- The push is applied on the rows where `push_applied` is 1: ten rows, 176–185, in all eight
  push recordings (`push_force_y` = −100 N, 0 N for `m0`).
- `<foot>_foot_contact` (FL, FR, RL, RR) is measured contact, exactly 0 or 1.
  `<foot>_foot_desired_contact` is the clock's *smoothed* stance indicator in [0, 1]; desired
  stance is `> 0.5`, which reproduces the configured duty (0.75 / 0.50 / 0.35).
- `gait_frequency` is the stride frequency the clock advances at: 0 / 1.9 / 2.85 / 3.4 Hz for
  stand / walk / trot / bound. `gait_phase` is the clock phase.
- `<joint>_action_policy` (12 columns) are the policy-stage joint targets.
- Raw 4–7 s of the four gait clips is steady state.
- **The feet follow the clock at once.** Around the jump, measured touchdown trails desired
  touchdown by 0–2 control steps before the jump and by the same after it, in both runs. The
  jump fires at global phase 0, which coincides with a natural touchdown; its only footfall
  signature is one stance cut to a quarter cycle (4 control steps instead of 9). There is no
  multi-stride catch-up in the contacts.
- **The joint targets do show the transient.** The distance of the twelve policy-stage
  targets from their pre-jump mean cycle (per clock-phase bin) is, per stride from the jump,
  8.6 / 3.0 / 1.5 / 1.0 × its pre-jump level for RECON + BCE and 8.6 / 2.9 / 2.0 / 1.3 × for
  PPO — back to baseline within three to four strides, as the poster's H2 states.
- The first three frames of every raw clip are unusable: frame 0 has a stale camera, frames
  0–2 show the ground before its material has loaded.
- Push outcomes at the filmed cell: RECON + BCE stands with the whole deviation and with
  components 9–16, falls with components 1–8 (about 0.5 s after the onset); PPO stands only
  with the whole deviation; with the deviation withheld and no push both fall late, about 2 s
  after the onset. No `terminated` flag is set; a fall is read from pose.
- Capabilities: all 40 PPO robots stand by 15 s; 36 of 40 RECON + BCE robots do, four never
  stand. The caption says so.
- The RECON + BCE walk realises about 0.25 m/s against its 0.35 m/s command; labels state the
  *commanded* speed and say so.
- The ground is mid-grey (median pixel about 80 of 255, grid lines brighter), not dark.

## Part 1 — the published clips

### Shared grammar

- The first three raw frames are never shown.
- Output: 25 fps, H.264, plus a still `<name>.jpg`. Every clip loops with a hard seam; the
  gait cycles of different tiles cannot share a seamless window (1.9 / 2.85 / 3.4 Hz).
- Pacing: a 1× stretch shows every second raw frame; a slow-motion stretch runs at 0.5× and
  shows every raw frame exactly once, so it is smooth. No other speeds. (True slower motion
  needs a recorder that captures at the 200 Hz physics rate — out of scope.)
- Label block, top-left of each tile, on a semi-opaque dark plate (the ground is mid-grey and
  the grid lines are bright): a bold first line (gait · commanded speed, or the condition)
  and a lighter second line. Encoder names are drawn in the site's dark-scheme colours,
  PPO `#7fd882` and RECON + BCE `#c08be0`, the pair the page's `.ppo` / `.aux` words take in
  dark mode.
- Type: Fira Sans, loaded from the site's own
  `node_modules/@fontsource/fira-sans/files/fira-sans-latin-{400,600}-normal.woff2`
  (Pillow reads them; the tool fails loud if it cannot).
- Every band and tile size is even; the encoder is opened so that it never rescales.

### The devices

- **Footfall strip** (gaits, jump). Four rows, FL / FR / RL / RR from the top, labelled, over
  a window of 1.5 s of *source* time centred on the playhead (a vertical line at the strip's
  middle), so it scrolls at half speed in slow motion and shows what comes next. Filled bars:
  measured contact. Thin outline: desired stance (`> 0.5`). The window draws recorded data
  beyond the cut where it exists. In the jump clip a red vertical line marks the event. What
  it shows there, truthfully: the outlines shift a quarter cycle, one stance is cut short,
  and the feet follow at once.
- **Deviation trace** (jump, D7). Under each tile, over the whole cut window
  in source time, with a moving playhead: the distance of the twelve policy-stage joint
  targets from their pre-event mean cycle, in units of its pre-event level. It spikes at the
  event and decays over three to four strides — the transient the poster's H2 is about,
  drawn from the clip's own recording.
- **Timeline** (jump, push). A track over the cut window, linear in source time, with a
  playhead, a tick at the event carrying a short label, and a "0.5×" tag while the clip runs
  in slow motion. In the push clip a static red band spans the rows where `push_applied` is
  1; the tick reads "substitution on", since the latent substitution starts at that step in
  all four columns while the fourth column is not pushed.

### The five clips

Times are relative to the raw clip ("raw") or to the event ("ev").

| Name | Page slot | Tiles | Cut and pacing | Devices |
|---|---|---|---|---|
| `capabilities` | hero, above the abstract | 1, full frame, RECON + BCE | raw 0.06–9.98 s (frames 3–499, an even count) at 1× | label |
| `gaits` | H1 Behaviour | 2 × 2: stand, walk, trot, bound; RECON + BCE | raw 4–7 s at 1×, then the same window at 0.5× | label with commanded speed and stride frequency (stand: 0 Hz); footfall strip per tile (stand: all four in contact); "0.5×" tag |
| `domain` | H2 Domain | 1, full frame, RECON + BCE | raw 0.52–8 s (frames 26–400, an even count) at 1× | label |
| `jump` | H2 Latent Feedback | 2 side by side, RECON + BCE left, PPO right | ev −1 s … +3 s; 0.5× from ev −0.2 s to ev +1.4 s (four trot strides) | label; deviation trace and footfall strip per tile; timeline with tick "clock +¼ cycle" |
| `push` | H1 Robustness | 2 rows (RECON + BCE, PPO) × 4 columns: whole deviation · components 9–16 · components 1–8 · none, 0 N | ev −0.6 s … +3 s; 0.5× from ev to ev +1.2 s | column headers (retained part, force); the encoder in the label plate of each row's first tile; timeline with push band and tick "substitution on" |

All tiles of one clip follow one frame schedule, each anchored on its own event frame.

### Geometry

| Clip | Source crop (raw px) | Tile | Bands | Output W × H |
|---|---|---|---|---|
| `capabilities`, `domain` | full 1920 × 1080 | 1920 × 1080 | — | 1920 × 1080 |
| `gaits` | 960 × 540, frame-centred (robot box x 668–1204, y 440–744 fits) | 960 × 540, 1:1 | strip 96 under each tile | 1920 × 1272 |
| `jump` | 1280 × 720, frame-centred | 960 × 540 | trace 120 and strip 96 under each tile; timeline 88 across | 1920 × 844 |
| `push` | 864 × 720, frame-centred (keeps the robot in all eight tiles, fallers included; 720 × 600 clips one) | 480 × 400 | column headers 64 on top; timeline 88 across | 1920 × 952 |

### Frame schedule rules

Times convert to raw-frame offsets with `round(t × 50)` and must be exact. A window is
half-open, `[start, end)`. A 1× segment has even length and starts an even number of frames
from the anchor, so offset 0 — the event frame — is always a shown frame; a clip cut in
raw time is anchored on its window's first frame. These rules are
validated when a clip entry is constructed, not discovered while rendering.

### Encoding

libx264, CRF 23, preset slow, `yuv420p`, `+faststart`, no audio, a keyframe every 50 frames;
the encoder is opened with `macro_block_size=1` (its default silently rescales 1080 to 1088).
Each clip at most 5 MB; above that the CRF is raised, to at most 26, and the result reported.
Trial encodes of the bare grids give 2.8 MB (`gaits`) and 1.6 MB (`push`) at CRF 23. The
still is a JPEG at quality 85, same size as the video, taken at a per-clip offset stated in
the clip entry — for the hero, a frame with the robots up, since under reduced motion the
still is all a visitor sees.

## Part 2 — the page

Order of `src/content/research/where-2026.mdx`:

1. **Hero clip** (`capabilities`) as the first thing in the body, full column width. The
   frontmatter `status` line is removed (the template renders it between the buttons and the
   body; `status` is optional in the schema).
2. **Abstract** — unchanged (the poster's Vision + Problem).
3. **Contributions** — unchanged.
4. **Setup** (replaces "Architecture"): the architecture figure and caption as now; a
   parameters block in three groups — robot and control, representation and policy, training
   and evaluation — with values read once from the runs' saved `env_config.json` /
   `rl_config.json` and written into the page as static text; a gait table from the saved
   schedule (walk below 0.7 m/s, 1.5–2.3 Hz, duty 0.75 · trot 0.7–1.7 m/s, 2.3–3.4 Hz, duty
   0.50 · bound above 1.7 m/s, 3.4 Hz, duty 0.35 · stand, duty 1); a fold-out (`<details>`)
   for the long tail (randomisation ranges, PPO settings); a short "reading the clips" note
   (footfall strip, deviation trace, event tick, "0.5×" tag, encoder colours, labels state
   commanded speed).
5. **One `##` per coupling, one `###` per hypothesis**, each in the same rhythm: one-line
   claim, clip, figure, caption. The clip precedes the figure. H1 Adaptation has no clip.
6. **Conclusion**, **References** — unchanged.

Text. The poster's wording stays the source of truth for the abstract, the figure captions
and the section texts. New text — the one-line claims, the parameters block, the reading
note and all five clip captions — is drafted for Janosch's edit. Two existing clip notes
are wrong under this design and are rewritten: the jump note's "about 3.5 s into the rollout"
and "realigns its stride with the clock" (the published cut has the jump at 1.0 s, and the
feet follow at once), and the push note's order of conditions (now whole · 9–16 · 1–8 ·
none).

Component: `<Clip name? id? title wide?>caption</Clip>`. `name` renders the self-hosted
video, reading its `src`, still, width and height from the manifest (below), so the layout
does not shift while it loads; `id` renders the YouTube embed; neither renders the existing
placeholder. The caption is the slot, as in `<Figure>`, so it can carry `.ppo` / `.aux` spans
and math; `note` stays as a plain-text fallback.

Widths. `.clip`'s `max-width: 44rem` is lifted: a clip spans the full wide column
(`--measure-wide`, 60rem). A breakout clip (`.clip--breakout`, the push grid; the name
avoids the existing `.wide`) is centred on the column and takes
`width: min(80rem, 100vw − 2.5rem)` without causing horizontal page scroll.

Player: `<video muted loop playsinline preload="metadata" controls poster width height>`.
One short script (the site's first) plays a clip while at least half of it is on screen and
pauses it when it leaves, so several never run at once; a clip the reader paused by hand is
not restarted. Under `prefers-reduced-motion: reduce` nothing autoplays; the still and the
controls remain.

Phones (D8): nothing special. Every clip, the breakout grid included, keeps
`max-width: 100%` and shrinks with the screen; the reader zooms or goes fullscreen. The
layout's viewport meta (`width=device-width, initial-scale=1`) does not disable zoom and
stays that way.

## Part 3 — the tool

`tools/clips/`, run with a Python that has Pillow, imageio, imageio-ffmpeg, numpy, pyarrow
and pytest (the `isaac` conda env does; its bundled ffmpeg is used — there is no system
ffmpeg):

```
python tools/clips/render.py            # all clips
python tools/clips/render.py jump push  # some; the manifest keeps the other entries
```

Output: `public/videos/where-2026/<name>.mp4` and `<name>.jpg`, and the manifest
`src/data/where-2026-clips.json` — per clip its files, width, height and duration, and its
provenance (run, task id, recording file, event frame) with paths relative to the runs root.
The manifest is imported by `<Clip>`; it is not served as a file. Raw clips are read in place
under the runs root (default `~/code/gait_rl/experiment/WHERE_rev2`, overridable) and never
copied into this repository.

| Module | Job | Depends on |
|---|---|---|
| `where_2026.py` | The five clips as declarative entries: tiles (run, task, label lines, crop box), grid shape, bands, cut window (raw or event-relative), pacing segments, devices, still offset. The only file a wording or timing change touches. | `spec.py` |
| `spec.py` | The dataclasses those entries are made of. Construction validates the frame-schedule rules and that every size is even. | — |
| `sources.py` | Locate a task's raw clip and recording; read (for one `env_idx`) warmup length, event row, measured contact, desired stance (`> 0.5`), `push_applied` rows, `gait_frequency`, `gait_phase`, policy-stage joint targets. Guards the pairing: the clip's frame count must equal post-warmup rows − 1, and the clip's modification time must lie within ten minutes of the recording's stamp. A recording is required only by a clip whose devices need one. | pyarrow, imageio |
| `signals.py` | The deviation trace: pre-event mean cycle per phase bin (36 bins, rows from 0.56 s after the warmup to the event), distance of the targets from it, normalised by its pre-event mean. Pure. | numpy |
| `schedule.py` | Cut window + pacing → the ordered raw-frame offsets to show at 25 fps, with the slow-motion flag per output frame. Pure. | — |
| `draw.py` | Overlays: label plate, headers, footfall strip, deviation trace, timeline with tick / band / playhead, "0.5×" tag. Pure given its inputs. | Pillow |
| `compose.py` | Per output frame: fetch each tile's raw frame, crop, scale, place, overlay; stream to the encoder; write the still and the manifest entry. | imageio-ffmpeg |
| `render.py` | CLI. | the above |

Error handling: every failure names the clip and the tile, and happens before any frame is
rendered — a missing raw clip; a missing recording or column where a device needs one; a
clip/recording pair that fails the pairing guard; an event outside the clip; a cut that
reaches before frame 3 or past the clip's last frame.

## Verification

- Unit tests (`tools/clips/tests/`, pytest) for the parts that can be silently wrong, with
  expectations stated as literals, never recomputed with the code under test: the frame
  schedule (1× shows every second frame, 0.5× every frame, half-open bounds, offset 0 shown,
  the validation refusing an odd 1× segment); the event lookup (row − warmup, both warmup
  lengths); the desired-stance threshold; the strip's time window; the deviation trace on a
  synthetic periodic signal with one disturbed cycle. No test asserts alignment tighter than
  the stated ±1 raw frame.
- Each rendered clip is checked by extracting frames: the first frame is clean, labels sit
  on the right tiles, tiles are in sync, the tick and the push band sit at the recorded
  event (±1 raw frame), the output size is the geometry table's.
- File sizes against the 5 MB bound.
- `astro build` passes; the built page contains the five `<video>` elements.
- The rendered clips and a contact sheet go to Janosch. The look of the page in a browser
  and the breakout are his to judge; the agent has no browser.

## Out of scope

- A recorder that captures at the physics rate (true slow motion), and a render warm-up that
  would remove the three odd first frames at the source.
- Re-recording any raw clip. If a published clip shows a raw clip to be unsuitable, that is
  raised, not worked around.
- A narrated or long-form cut for YouTube.
- Any other page of the site.

## Open points

None.
