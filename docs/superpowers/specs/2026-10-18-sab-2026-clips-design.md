# SAB 2026 page — supplementary clips and the mask diagram: design

Status: DRAFT 1, 2026-10-18. Decisions D1–D14 were taken by Janosch in the design dialogue
of 2026-10-18. Every fact under "Verified" was read off the code or the data on that day,
with the file named. Git is Janosch's in both repositories (as WHERE D6): nothing is
committed or pushed by an agent.

Predecessor: `2026-09-21-where-2026-clips-design.md`. The tool it describes under
`tools/clips/` is the base; this document states what the SAB clips add and change. The
website page itself (`src/content/research/sab-2026.*`) is built in another session; this
work delivers the clips, the manifest, the diagram, the colour and caption drafts it needs.

## Goal

Three clips and one drawing for the SAB 2026 page, as supplementary material behind the
poster's QR code. A visitor coming from the poster meets the same three conditions, the
same names and the same mask vocabulary, and sees what a still image cannot carry: the
four behaviours with the latent ring moving, the masking experiment with the deviation
the controller reads, and the controller at work on a field of robots.

| Clip | Page slot | Claim on the page |
|---|---|---|
| `gaits` | Section 1, Behaviour Encoding | The four commanded behaviours lie as concentric rings on PC1 and PC2 of the latent. |
| `push` | Section 3, Push Survival | Behaviour feedback can be replaced by its nominal cycle, domain feedback cannot. PPO alone has no such partition. |
| `intro` | Hero, above the abstract | The controller stands up from any pose and realises the trained command range. |
| mask diagram | Section 3, before `push` | What the controller reads under each mask. |

## Decisions taken

| # | Decision |
|---|----------|
| D1 | `gaits` and `intro` are published for the curriculum run. `gaits` is recorded on all three runs so the latent ring exists for PPO and + AUX if asked. `push` shows all three runs, one row each. |
| D2 | Condition names on video and page are the poster's: `PPO`, `+ AUX`, `+ Curriculum`. The WHERE name "RECON + BCE" is not used on the SAB page. |
| D3 | Condition colours on video: PPO `#7fd882`, + AUX `#c08be0`, + Curriculum `#5fc4c8`. The site's `.cur` span gets the same dark-mode value, replacing the `#4fb8bc` the page session wrote as a placeholder (confirmed 2026-10-18). The poster's own colours (`#1F9423`, `#7B3FA0`, `#0F7C80`) are too dark on the label plate and stay on the poster. |
| D4 | `push` columns, left to right: No Mask · 100 N, Behavior Mask · 100 N, Domain Mask · 0 N, Full Mask · 0 N. The domain mask is shown unpushed so that its fall is the mask's, not the push's. The spelling is the poster's and the SAB page's (`poster-landscape.tex` caption, `sab-2026.mdx`): American, "Behavior". |
| D5 | The three pushed rows share one cell: trot 1.2 m/s, heading −y, onset 3.24 s episode clock, 100 N. The 0 N columns start the substitution at the same instant. The onset was chosen on the recorded `push_mask` datasets (Verified): 3.24 s is the one onset at which all three rows reproduce the poster's pooled result under the poster's own fall rule. The filmed clips are checked after recording with the rule read on the clip's end: a robot has fallen when a trunk or hip contact is present in the last 0.5 s of the 4 s window. The poster's rule counts any contact after the onset; on the filmed curriculum No Mask clip that flags a 0.08 s trunk graze at 0.40 s from which the robot is up again at once (Janosch, 2026-10-18: it does not fall), while every real fall in the twelve clips is still down at the window's end. 100 N stays. |
| D6 | No trained-range band on the `push` timeline. |
| D7 | `gaits` tiles carry a latent panel: the live latent point on PC1 and PC2 of the run's own basis, the one the poster figure draws, with a fading trail and the four conditions' rings faint behind it, each from the tile's own recording over its steady window (chosen on the rendered clips over rings from the nominal table: the recorded rings sit on the live points exactly). |
| D8 | `gaits` labels state the commanded speed only; the stride-frequency line is dropped. |
| D9 | `push` tiles carry a deviation trace under each robot: the deviation of the latent from its nominal cycle, split into the behaviour components and the domain components, with the masked group's line flat from the onset, in units of the group's nominal cycle amplitude (chosen on the rendered clips over raw scaled latent units). Drawn as a plot with axes: y titled `latent deviation` on the first column of each row, without tick labels, one range per condition row; x in seconds from the onset; a legend row above each plot; no caption on the video. |
| D10 | `intro`: no robot randomisation, no observation or encoder noise, no push. Robots spawn at random orientations on a 1 m grid that reaches past every edge of the camera frame. A robot that leaves the frame is truncated and respawns at its origin at a new random orientation, so the field stays full. Every environment's clock starts at zero; the recording starts at the reset. |
| D11 | `intro` commands are drawn from the curriculum run's own accomplished command cells at checkpoint 7250, not from the full box: the box was not fully reached (see Verified). The whole accomplished range is sampled, backward cells included. Standstills are included. |
| D12 | The `intro` still is taken a second or two after the robots are up and spread; the exact offset is picked on the rendered clip. |
| D13 | One manifest and one clip folder per conference page: `public/videos/sab-2026/` and `src/data/sab-2026-clips.json`. The WHERE files are untouched. |
| D14 | The mask mechanism diagram is made in this repository as an SVG, not in the poster's vault. |

## Verified (2026-10-18)

Runs, under `~/code/gait_rl/experiment/sab_rev/`, all evaluated at checkpoint 7250
(`config/eval/sab_rev/_common.py`):

| Condition | Run directory | Latent block read by the policy edge | Behaviour components |
|---|---|---|---|
| PPO | `rl-only/26-10-12_16-04-32_rl-only` | `latent` (deterministic encoder) | 5 |
| + AUX | `proprio-encoder_contacts/26-10-15_09-29-51_proprio-encoder_contacts` | `mean` (Gaussian encoder) | 7 |
| + Curriculum | `proprio-encoder_contacts_curriculum/26-10-12_21-26-43_proprio-encoder_contacts_curriculum` | `mean` | 2 |

The behaviour counts are `BEHAVIOUR_COMPONENTS` in `config/eval/sab_rev/_mask_design.py`.

Artifacts, present for all three runs: the basis
`<run>/analysis/latent_representation/shared/latent_basis.parquet` (with `.meta.json` and
`latent_basis_stats.parquet`) and the nominal table
`<run>/analysis/latent_representation/sources/nominal_fixed/latent_nominal.parquet`. These
are the two paths every `push_mask` recording's `.meta.json` names under `intervention`,
with `leading_components` = the behaviour count. The nominal table holds the 16 steady
conditions (stand and five speeds per band, `_rev2_common.STEADY_SPEEDS`); 0.35, 1.2 and
2.1 m/s are among them.

Masks (`gaitrl/pipeline/base/latent_reference.py`, `MaskKind`; `_mask_design.MASKS`): the
policy reads `h + M (z − h)`, `h` the nominal latent at the clock phase, `z` the encoder's
latent. Poster name ↔ mask id: No Mask ↔ `identity` (M = I); Behaviour Mask ↔ `trailing`
(deviation kept on the domain components, behaviour components held at `h`); Domain Mask ↔
`leading` (deviation kept on the behaviour components); Full Mask ↔ `blind` (M = 0).
`mask_matrices(basis, kinds, tangent=None)` returns the matrices `D⁻¹ P D`, `D =
diag(1 / scaling)`; `apply_mask(mask, latent, nominal)` applies them. The substitution is
switched on by the trunk wrench window's onset flag and stays on (`latent_substitution.py`,
`LatentEdgeSubstitution.step`; `recorder/function/domain.py`, `TRUNK_WRENCH_ONSET_COLUMN`).

What a recording under the substitution holds: the encoder's raw latent. The intervention
is applied in `GraphCoordinator` when the reading node's input is assembled
(`learning/model/coordinator/graph.py` line 226); the recorder's `node_block` reads the
emitted block off `PolicyState.latents` (`recorder/function/policy.py`), which the
intervention does not touch. The substituted value is therefore reconstructed offline with
the formula above, the way `pipeline/replay` does.

Recording columns (read off `push_mask/7250/*.parquet` of the curriculum and PPO runs and
`nominal_spawn_fixed/7250/*.parquet` of the AUX run):

- latent: `dynamics_encoder_mean_0..15` (Gaussian runs; `dynamics_encoder_log_std_*` beside
  it) or `dynamics_encoder_latent_0..15` (PPO);
- window: `robot_trunk_wrench_window_{open,onset,closed,remaining,fraction}`, the force in
  force `robot_trunk_wrench_in_force_force_{x,y,z}`;
- `gait_phase`, `gait_frequency`, `gait_kind`, `gait_duty`; `<foot>_foot_contact`,
  `<foot>_foot_desired_contact`; `<foot>_<part>_joint_action_policy` (12);
  structural `env_idx`, `timestep`, `warmup`, `trial`, `command_index`, `episode_id`,
  `terminated`, `truncated`;
- the steady recorder (`_where_common.recorder_config`) records the same latent block,
  contacts, gait columns and policy actions, so the `gaits` devices read it as the WHERE
  clips did.

Transient protocol (`config/eval/_transient_design.py`, `sab_rev/_probe_design.py`):
control 50 Hz; warmup 32 steps, counted by the episode clock; 10 s recorded after it;
settle 1.0 s; onset instants (3.00, 3.12, 3.24, 3.36) s episode clock; hold 0.2 s;
headings (0, π/2, π, 3π/2) = +x, +y, −x, −y; magnitudes 0 and the ladder 15 … 200 N
(100 N is a level, `_push_design.PUSH_MAGNITUDES`). An onset at 3.24 s is raw clip frame
3.24 × 50 − 32 = 130, 2.60 s into the clip; 7.40 s follow. `transient_validation` and
`_video_common.video_validation` build the same `ValidationCfg` fields; only `video` and
`capture_video` differ.

Fall rule and the filmed cell (read off the newest `push_mask/7250/*.parquet` of each run
with the poster's rule from `plotting/allocation/mask_survival.py`, `FALLEN`: a fall is
`trunk_contact` or any `<leg>_hip_contact` true on a step after the onset; the mask
recorder writes no `base_orientation` or `projected_gravity`, only
`corrupted_projected_gravity_*`, so the contact rule is the one to use). At trot 1.2 m/s,
heading −y, seconds after the onset:

| Onset | PPO | + AUX | + Curriculum |
|---|---|---|---|
| 3.00 | intact stands, behaviour mask falls 0.72, domain mask (0 N) falls 3.82, full mask falls 1.36 | stands, stands, 2.28, 2.32 | **intact falls 0.28, behaviour mask falls 0.28**, 1.90, 1.82 |
| 3.12 | stands, 1.64, 2.92, 1.48 | stands, stands, 2.64, 2.56 | **0.48, 0.66**, 2.52, 2.04 |
| 3.24 | stands, 0.84, 3.28, 1.34 | stands, stands, 2.28, 2.58 | stands, stands, 2.22, 2.20 |
| 3.36 | stands, 0.74, 3.58, 1.54 | stands, stands, 2.40, 3.94 | **0.60, 0.60**, 1.90, 2.24 |

Only 3.24 s reproduces the pooled result in every row, hence D5. PPO's domain mask at 0 N
falls late, 2.9 to 3.8 s after the onset at every onset, hence the cut to ev +4.0 s (Part
2). The curriculum run's `push_mask/7250/` also holds an older k = 3 recording; "the run's
recording" means the newest file, as the poster script reads it.

Video capture (`src/gaitrl/pipeline/video/README.md`, `manager.py` line 1219): eval clips
land in `<run>/evaluations/videos/evaluation/<task_id>-<checkpoint tag>-step-0.mp4`, with
tag `7250` here; recordings in `<run>/evaluations/<task_id>/<tag>/evaluation_data_*.parquet`.
The WHERE-era paths without the tag (`tools/clips/sources.py`, `clip_path`,
`recording_path`) are stale for new recordings. Frames are 1920 × 1080 at one frame per
control step from the first step after the warmup (`_video_common.video_validation`).

Camera and ground (`config/eval/_video_common.py`): `SIDE_VIEW` (tracking, from the right),
`REAR_VIEW` (tracking, from behind), `CROWD_VIEW` (fixed in the world, eye (0, −7.5, 4.8),
look-at (0, 0.7, 0), about 10 m wide at the grid); the grid ground `VIDEO_TERRAIN_CONFIG`
on the datasets' 2000 × 2000 m plane (`_where_common.FLAT_TERRAIN`), so the existing
`at_environment_boundary` truncation (threshold 2 m, `_where_common.physical_truncations`)
never fires.

Resets and spawn: in evaluation, every environment that terminates or truncates is reset
on the next step (`runner.py` lines 1051, 1036; `environment/locomotion/unitree_go1/base.py`
line 1019 ff., which resets simulation, robot, command modulator, sampler and processor
for `done_ids`). The spawn producer draws every spawn quantity again for the reset
environments (`spawn/randomisation/producer.py`, `run` at RESET and EPISODE), so a random
orientation is redrawn on every respawn. `EpisodeClockStart.ZERO` in
`physical_truncations` starts every clock at zero. The robot's world position is
`state.robot.base_position` `[env_n, 3]`, world frame (`simulation/robot/state.py`).

Curriculum frontier of the + Curriculum run at 7250
(`checkpoints/curriculum_7250.pt`, dimension `behaviour`): the lattice spans forward
−1.4 … 2.5 m/s in 0.1 m/s cells (14 below, 25 above), sideways ±0.9 m/s in 0.1 m/s cells,
yaw ±2.0 rad/s in 0.2 rad/s cells, 40 × 19 × 21 = 15 960 cells. States
(`simulation/curriculum/config.py`, `UnitState`): 12 841 ACCOMPLISHED, 229 OPENED, 875
ADJACENT, 2 015 UNREACHED. Index 0 is the point `[0, 0]`, index +i the interval
`[(i − 1) · step, i · step]`, −i its mirror (`command/curriculum/config.py`,
`LatticeChannelCfg`). The uniform runs trained under a cohort sampler instead
(`env_config.json`, `command.sampling_policy`): standstill 0.1, low (forward ±0.7, sideways
±0.4, yaw ±1.0), mid (forward −1.4 … −0.7 and 0.7 … 1.7, sideways ±0.9, yaw ±1.4), high
(forward 1.7 … 2.5).

Renderer (`tools/clips/`): `spec.Tile(run, task, title, subtitle, encoder, header)`,
`spec.Geometry(crop, tile, rows, cols, header_h, trace_h, strip_h, timeline_h)`,
`spec.Clip(name, tiles, geometry, anchor, event_column, segments, tick_label, push_band,
still_s, env_idx)`; `draw.ENCODERS = {"ppo": ("PPO", …), "aux": ("RECON + BCE", …)}`;
`draw.trace(image, box, values, rows, playhead_row, event_row)` draws one line;
`sources.load_recording` requires the WHERE columns and reads `push_applied` as optional;
`compose.render_clip` hard-codes `/videos/where-2026/`; `render.py` hard-codes the WHERE
runs root, output folder and manifest; `Clip.astro` imports the WHERE manifest. The
`isaac` conda environment imports `gaitrl` (`gaitrl.pipeline.base.latent_reference`
resolves to `~/code/gait_rl/src/…`). The site stylesheet already has `.cur { color:
#0f7c80 }` with no dark-mode rule.

## Part 1 — recordings (`~/code/gait_rl`)

All new files under `config/eval/sab_rev/`. They load `../_video_common.py` for the
viewers, ground, spawn grid and `video_validation`, and this folder's `_common.py` for the
roster. Capture is switched on by `--capture_video` on the command line, as the WHERE
configs document. Runs are evaluated at their latest checkpoint, 7250.

### 1a `video_gaits.py`

Four tasks `video_stand`, `video_walk`, `video_trot`, `video_bound` from
`_video.steady_video_task` at 0 / 0.35 / 1.2 / 2.1 m/s (`_video.STAND_SPEED` and the
band middles), `SIDE_VIEW`, default spawn, `NOMINAL_RANDOMISATION`; roster `runs()` (all
three); `video_validation(tasks, num_trials=1, runs, episode_length_s=10.0,
warmup_steps_n=32)`. Identical to the WHERE file but for the roster. Output: twelve clips
and twelve recordings.

### 1b `_video_mask_common.py` and `video_mask_{rl-only,proprio-encoder_contacts,proprio-encoder_contacts_curriculum}.py`

One task per column of the `push` clip, per run. The task is `_mask_common.mask_window_task`
for the run (its nominal and basis paths, block and behaviour count exactly as the run's
`push_mask_*.py` states them, so the filmed substitution is the recorded dataset's), then
`.replace(…)` to one cell, the way `_video_common.push_video_task` pinned the WHERE task:

| Field | Value |
|---|---|
| `id` | `video_mask_identity_m100`, `video_mask_trailing_m100`, `video_mask_leading_m0`, `video_mask_blind_m0` |
| `viewer`, `terrain` | `REAR_VIEW`, `VIDEO_TERRAIN_CONFIG` |
| `env_n` | 1 |
| `command` | `_steady.command_config(GridModulatorCfg(grid=[command_tuple(1.2, 0, 0)]))` |
| `randomisation.robot` | `_design.robot_randomisation("trunk_wrench", _design.push_window_quantity((magnitude,), (3π/2,), (3.24,), settle_s=1.0, hold_s=0.2))` |
| `randomisation` others | terrain, observation, encoder `NO_RANDOMISATION`; spawn as the mask task states it |
| `design` | `push_window_design((magnitude,), (3π/2,), (3.24,))` entries plus the intervention mask entry with the one mask |
| `intervention.mask` | `EnumeratedLabelsCfg(values=[mask])` |

`magnitude` is 100.0 for the first two tasks and 0.0 for the other two. Validation:
`video_validation(tasks, num_trials=1, runs=[run], episode_length_s=10.0,
warmup_steps_n=32)`, one file per run because the intervention paths are the run's.
Output: twelve clips, twelve recordings, `env_idx` 0 in each.

### 1c `video_intro.py`

From `config/eval/video_capabilities.py`, with these changes.

- **Run:** the curriculum run only (`proprio_encoder_contacts_curriculum_run()`).
- **Randomisation:** `robot` the run's reference values (`RandomisationMode.NO_RANDOMISATION`
  for every quantity, no trunk wrench), `terrain` none, `observation` and `encoder`
  `NO_RANDOMISATION`, `spawn` the WHERE `_RANDOM_ORIENTATION_SPAWN` (uniform orientation,
  trained joint jitter).
- **Field:** `video_spawn(num_rows, num_cols)` at `VIDEO_SPAWN_SPACING_M` raised to 1 m for
  this task (a new module constant `INTRO_SPAWN_SPACING_M`; the 0.5 m value stays for the
  other clips), 16 rows × 24 columns = 384 robots. A first pass at 1.5 m lost the far
  corners of the field behind the label plate and the near corners off the sides; a second
  at 10 × 8 held the whole field inside the frame, and Janosch asked for the field to reach
  past the frame instead.
- **Camera:** eye (0, −12.5, 8), look-at (0, −3, 0): the pitch of the 10 × 8 pass, shifted
  so that the frame's ground footprint from a pinhole model of the viewport (60° horizontal
  field of view: y = −7.5 … 7.2, x = ±5.2 at the bottom row to ±11.7 at the top row) is
  centred on the field, which reaches past every edge of it.
- **Respawn:** a new truncation `outside_world_rectangle` in
  `src/gaitrl/simulation/done/function/spatial.py`, registered like its neighbours,
  signature `(state, interface, x_range: tuple[float, float], y_range: tuple[float, float],
  **kwargs)`, true where `state.robot.base_position[:, 0]` or `[:, 1]` lies outside the
  stated ranges. Added to the task's `DoneCfg` beside `physical_truncations()`'s entries
  as `DoneParamCfg(name="outside_world_rectangle", active=True, type=DoneType.TRUNCATION,
  function_param={...})` with the spawn rectangle plus half a spacing of margin. A test in
  `tests/simulation/done/` beside the existing ones.
- **Commands:** one command per environment, held for the clip, from a seeded draw over the
  curriculum's accomplished cells. A helper `_intro_commands.py` in the folder loads
  `checkpoints/curriculum_7250.pt` of the run, takes the `behaviour` dimension's
  `unit_state` and `units` (the `LatticeCfg`), maps every ACCOMPLISHED cell to its interval
  box by the rule above, and draws: a tenth of the environments exact standstills
  `(0, 0, 0)`; the rest in equal shares from the cells whose forward interval lies in the
  walk band (|v| below 0.7 m/s, standstill cell excluded), the trot band (|v| 0.7 … 1.7) and
  the bound band (|v| above 1.7), each a uniform point inside a uniformly chosen cell of
  that band. Bands are by |v|, so the accomplished backward cells (down to −1.4 m/s) are in
  the walk and trot shares; every accomplished cell is eligible.
  Seed 7, a module constant. The helper writes the drawn list once to
  `video_intro_commands.json` beside the config, and the config reads that file, so the
  draw is reviewable and the eval config does not load a checkpoint. The lattice's flat
  cell order is taken from `simulation/curriculum/lattice.py`, not assumed.
- **Done, clock, length:** `physical_truncations()` plus the rectangle term;
  `EpisodeClockStart.ZERO` as inherited; `episode_length_s` 12.0, `warmup_steps_n` 0.
- **Output:** one clip, one recording with `episode_id` counting the respawns.

Which gait a negative or sideways command resolves to is the run's own schedule's business
(`gait_resolving_speed` is recorded); the draw does not assume it.

### Recording order and cost

Twelve gait clips, twelve mask clips, one intro clip, each a short IsaacSim evaluation; the
WHERE set of comparable size recorded in about an hour. Order: gaits (needed first for the
ring), intro (camera iteration), mask clips last.

## Part 2 — clips (`tools/clips/`)

### Changes to the shared tool

- `sab_2026.py`: the three clip entries, the only file wording and timing touch, with
  `RUNS` mapping `ppo`, `aux`, `cur` to the run directories above and `CHECKPOINT = "7250"`.
- `render.py`: a `--page` argument (`where-2026`, `sab-2026`) selecting the entries module,
  runs root (`~/code/gait_rl/experiment/sab_rev`), output folder and manifest; the manifest
  `src` paths follow the page. `compose.render_clip` takes the page slug instead of the
  hard-coded folder.
- `sources.py`: `clip_path` and `recording_path` take the checkpoint tag
  (`<task>-<tag>-step-0.mp4`, `evaluations/<task>/<tag>/`); the WHERE entries pass no tag
  and keep their paths. `load_recording` learns the SAB window columns: event column
  `robot_trunk_wrench_window_onset`, push band from `robot_trunk_wrench_window_open`
  (`push_applied` remains for WHERE). It also returns the latent block columns
  (`dynamics_encoder_<block>_0..15`, the block named per tile) and the command columns
  the nominal table is keyed by (`COMMAND_COLUMNS` in `latent_reference`).
- `draw.py`: `ENCODERS` becomes `CONDITIONS = {"ppo": ("PPO", (127, 216, 130)), "aux":
  ("+ AUX", (192, 139, 224)), "cur": ("+ Curriculum", (95, 196, 200))}`; the `Tile.encoder`
  field keeps its name and takes the three keys. New primitives `latent_panel` and
  `deviation_trace` (below).
- `spec.Geometry` gains `side_w` (width of a square side panel per tile, 0 = none) and
  `Clip` gains `variant` (free string appended to the output name) so one entry renders its
  two versions.
- `latent.py` (new): reads the basis and the nominal table through
  `gaitrl.pipeline.base.latent_reference.read_latent_basis` and `read_nominal_table`, with
  `expect` built from the recording's `.meta.json` (`run`, `checkpoint`, `precision`,
  `latent_blocks`), so the tool refuses a basis that is not the recording's. Projection on
  the basis: `project_rows` of `gaitrl.pipeline.analysis.projection` with the `center` row
  of the basis file; the nominal at a row: `table.lookup(command_ids, phase)` with
  `command_ids` from `table.command_ids(commands, tolerance=1e-4)` and `phase` from
  `gait_phase`. The masked read: `apply_mask(mask_matrices(basis, [kind], None), z, h)`.
  Decision: the tool imports these readers from `gaitrl` rather than re-implementing them,
  so the ring and the traces are built from the same tables and formulas as the evaluation.
  This reverses nothing in WHERE D3 (nothing of the site enters `gait_rl`).

### The three clips

Times relative to the raw clip ("raw") or to the event ("ev"). The shared grammar of the
WHERE design holds: first three raw frames never shown, 25 fps output, 1× shows every second
raw frame, 0.5× every frame, label plate top-left, Fira Sans, even sizes, CRF 23 within 5 MB (raised in steps of 3 up to 32 until the clip fits; refused beyond).

| Name | Tiles | Cut and pacing | Devices |
|---|---|---|---|
| `gaits` | 2 × 2: stand, walk, trot, bound; `cur` | raw 4–7 s at 1×, then the same at 0.5× | label `Stand · 0 m/s commanded` etc., no subtitle; footfall strip under the robot; latent panel beside it |
| `push` | 3 rows (`ppo`, `aux`, `cur`) × 4 columns (D4) | ev −0.6 … +4.0 s; 0.5× from ev to ev +1.2 s | column headers; condition name on each row's first tile; deviation trace under every tile; timeline with push band and tick `substitution on` |
| `intro` | 1, full frame; `cur` | raw 0.06 s to the end of the clip at 1× | title `Locomotion Diversity`, no subtitle, condition name |

`push` column headers: `No Mask · 100 N`, `Behavior Mask · 100 N`, `Domain Mask · 0 N`,
`Full Mask · 0 N`. The cut runs to ev +4.0 s so that PPO's domain-mask fall, 3.3 s after
the onset at this cell, is inside it; at 25 fps the clip is 5.8 s long. Tasks per column: `video_mask_identity_m100`, `video_mask_trailing_m100`,
`video_mask_leading_m0`, `video_mask_blind_m0`. The event column is
`robot_trunk_wrench_window_onset` in all twelve recordings; it fires in the 0 N recordings
too (the window opens at 0 N).

### Geometry

| Clip | Source crop | Tile | Bands | Output |
|---|---|---|---|---|
| `gaits` | 960 × 540, frame-centred | 640 × 360 | strip 96 under the tile; side panel 456 × 456 (the cell height) | 2 × (640 + 456) = 2192 wide, 2 × 456 = 912 high |
| `push` | 864 × 720, frame-centred | 480 × 400 | header 64; trace 120 under every tile; timeline 88 | 1920 × (64 + 3 × 520 + 88) = 1920 × 1712 |
| `intro` | full 1920 × 1080 | 1920 × 1080 | — | 1920 × 1080 |

The `push` grid is taller than wide and sits in the page's breakout width; the tile size is
the WHERE one, so a visitor compares the two pages' robots at one scale.

### Latent panel (`gaits`)

A square panel right of the robot tile, dark band colour, axes PC1 (horizontal) and PC2
(vertical) of the run's basis with the explained variance in the axis labels, read from
`latent_basis_stats.parquet`, matching the poster figure's labels. Fixed axis limits per
clip, the same in all four tiles, from the four rings' extent plus a margin. Drawn per frame:

1. The four rings, faint, in the poster's gait colours (stand grey, walk blue, trot orange,
   bound pink, the legend of the poster's figure): each from its tile's own recording over
   the steady window (raw 4–7 s), projected, drawn as the recorded polyline. The stand
   condition is a point.
2. The tile's own trail: the projected latent of the last 0.6 s of source time (30 rows)
   fading to transparent, in the tile's gait colour.
3. The live point at the playhead row, filled, with a thin white ring.

The projection uses the recording's latent columns and the basis of the same run, so the
PPO and + AUX renders, if ever made, draw their own bases.

### Deviation trace (`push`)

Under each tile, over the whole cut window in source time, with a moving playhead and the
event line, like the WHERE jump trace. Two lines in the tile's band:

- **behaviour**, the norm of the deviation's part on the behaviour components;
- **domain**, the norm of its part on the domain components.

In the scaled coordinates the basis is orthonormal in (`d / scaling`), with
`d = z − h(φ)`, `z` the recorded latent, `h` from the nominal table at the recorded command
and phase. The parts are `P_lead d_s` and `P_trail d_s` with the basis's leading count =
the run's behaviour count. Before the onset both lines are the raw deviation. From the
onset, a line shows what the controller reads: under `identity` both stay; under
`trailing` the behaviour line is zero (drawn flat at the baseline in the muted colour) and
the domain line stays; under `leading` the reverse; under `blind` both are flat. The
withheld group's raw value is drawn dotted behind its flat line, so the viewer sees what
was removed. Colours: behaviour in the condition's colour, domain in white.

Scale: each group's norm divided by that group's nominal cycle amplitude, the RMS over the
phase bins of `P_group (h(φ_b) − mean_b h) / scaling`, a per-run, per-group constant, so 1
reads as "a deviation as large as the gait cycle itself". The y-axis is one fixed range
per condition row, 0 to the largest value over the row's four cut windows rounded up to a
decimal, so the four masks of a condition share a scale and each condition has its own
(the domain amplitude of the encoder runs is near zero, so their normalised values run
far above PPO's; one shared range flattened PPO's rows). No tick labels: the values are
not the point, the course is.

Layout of the band (D9): a plot with a left and a bottom axis. The y-axis title `latent
deviation` stands on the first column of each row only; no y tick labels.
The x-axis is time in seconds from the onset (the recording's control period converts
rows), ticked at every whole second of the window, titled `time (s)`. Above each plot a
legend row names the three styles: `behaviour` (condition colour), `domain` (white),
`removed by mask` (dotted, muted). No caption or unit text on the video; the unit is the
caption's.

### Stills

`gaits`: raw 5 s. `push`: ev +0.6 s. `intro`: an offset after the robots are up and spread,
set on the rendered clip (D12); start from raw 4 s.

## Part 3 — page assets (for the page session)

- `src/components/Clip.astro`: a `page` prop (`"where-2026"` default, `"sab-2026"`) selecting
  the manifest it reads; a missing name still fails loud with the manifest's name.
- `src/styles/global.css`: `.cur { color: #0f7c80 }` gets
  `@media (prefers-color-scheme: dark) { .cur { color: #5fc4c8; } }`, so the word in a caption
  matches the word in the video.
- The diagram file (Part 4).
- Caption drafts, in Janosch's register, one per clip, for the page session to place; each
  states the condition, what the devices show and, for `push`, the mask vocabulary. The
  `intro` caption says the field is unrandomised and that robots re-enter when they leave
  the frame.

## Part 4 — the mask mechanism diagram

`public/figures/sab-2026/mask-mechanism.svg`, hand-written SVG, text as text, colours as
variables at the top of the file, ink that reads on the light and the dark scheme (the
WHERE figures are the precedent). Content, left to right:

1. The encoder's latent `z_t` as sixteen components in a column, the first `k` marked
   behaviour (the condition's colour) and the rest domain (white or ink), with `k` = 5 / 7 /
   2 stated per condition in a small legend.
2. The nominal cycle `h(φ)` as the same column, and the deviation `z_t − h(φ)` as the
   difference, drawn as arrows between the two columns.
3. Four small panels, one per mask in the clip's column order, each showing which part of
   the deviation reaches the controller (kept, full colour) and which is replaced by the
   nominal course (greyed, with the `h` symbol): No Mask keeps both; Behaviour Mask keeps the
   domain part; Domain Mask keeps the behaviour part; Full Mask keeps none.
4. One line of formula under the panels: `read = h(φ) + M · (z_t − h(φ))`.

Size for the page column (about 60 rem wide), aspect about 3 : 1. No numbers beyond `k`.

## Verification

- `tools/clips/tests/`: the new primitives and the latent module get tests with literal
  expectations: the projection of a known row on a known basis; the nominal lookup at a bin
  centre; the four masks on a known deviation (identity keeps, blind zeroes, trailing and
  leading zero the right group); the group amplitudes on a synthetic ring; the checkpoint-tag
  path rule; the window-column event lookup (one onset, 0 N included).
- `gait_rl`: a test for `outside_world_rectangle` on a synthetic state; the mask video
  configs load and validate (`load_config_module`), and their task's intervention paths equal
  the run's `push_mask` recording's `.meta.json` `intervention` entry.
- After recording, before rendering `push`: for each run, the four filmed outcomes against
  the poster's pooled result, read from the recordings with the poster's fall rule
  (`trunk_contact` or any `<leg>_hip_contact` after the onset): intact stands; behaviour
  mask stands for + AUX and + Curriculum and falls for PPO; domain mask and full mask fall
  unpushed, all inside the cut. The filmed episode is a fresh rollout, not the dataset's
  row, so it may differ from the table under Verified; a cell that does not reproduce the
  result is reported with the table's alternatives and is not worked around.
- `intro`, on a test render with the robots at their spawn origins: the camera footprint, the
  rectangle, the fill of the frame over the whole clip, every behaviour visible, respawns
  landing inside the frame.
- Each rendered clip by extracted frames: labels on the right tiles, tiles in sync, the tick
  and band at the recorded onset (±1 raw frame), the latent point on the ring in the steady
  window, the masked trace flat from the onset, output sizes as the geometry table. File
  sizes within the bound.
- `astro build` passes with the `page` prop and the two manifests.

## Out of scope

- The SAB page's structure and text (another session), and the poster figures on it.
- Re-recording WHERE clips or changing the WHERE page.
- A recorder that captures at the physics rate; a render warm-up removing the first three
  frames at the source.
- PPO and + AUX renders of `gaits` (recorded, not rendered).

## Open points

None. The builder check of 2026-10-18 raised the push cell and fall rule (settled in D5
and Verified), the cut length (Part 2), the spelling (D4), the colour (D3) and the backward
commands (D11), all closed.

On-sight checks, not decisions: the camera and rectangle of `intro`, the `intro` still
offset, and which variant of `gaits` and `push` the page shows.
