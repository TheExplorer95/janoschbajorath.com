# SAB 2026 clip captions, drafts

Register as the WHERE page: bold title, en dash, one claim per sentence, condition spans
`.ppo` / `.aux` / `.cur`, American spelling as the SAB page uses it.

## gaits

```mdx
<Clip page="sab-2026" name="gaits" title="The commanded behaviors">
**The commanded behaviors** – Stand and the middle of the walk, trot and bound speed bands under nominal dynamics, with the <span class="cur">curriculum</span>, first at full speed, then at half speed. Beside each robot, the latent on the first two principal components of the run's basis: the live point with its trail, and the four conditions' recorded cycles as rings. Speed is the radius; the stand condition is the center.
</Clip>
```

## push

```mdx
<Clip page="sab-2026" name="push" title="A lateral push under latent masking" wide>
**A lateral push under latent masking** – At trot, seen from behind, <span class="ppo">PPO</span>, <span class="aux">AUX</span> and the <span class="cur">curriculum</span>, one row each. From the red tick on, the latent the controller reads is the command's nominal cycle plus the deviation on all components (No Mask), on the domain components only (Behavior Mask), on the behavior components only (Domain Mask) or on none (Full Mask). The red band is the 0.2 s push of 100 N, applied in the first two columns only. Under each robot, the deviation of the latent from its nominal cycle over time, split into the behavior components (in the condition's color) and the domain components (white), in units of the group's own cycle amplitude; a masked group's line is flat from the tick, the course it would have taken dotted.
</Clip>
```

## intro

```mdx
<Clip page="sab-2026" name="intro" title="Locomotion Diversity">
**Locomotion Diversity** – A field of 384 robots under nominal dynamics, each starting from a random orientation with its own command, drawn from the command range the <span class="cur">curriculum</span> run reached, standstills included. The field reaches past the frame; a robot that walks out of it re-enters at its origin with a new orientation.
</Clip>
```

The count is the one in `video_intro_commands.json`; change the caption if the field changes.
