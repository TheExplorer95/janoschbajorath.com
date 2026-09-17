Contemporary quadruped locomotion controllers trained with reinforcement learning rely, almost universally, on externally introduced locomotion priors — architectural ones such as central pattern generators, or reward functions that explicitly encode desired gait properties. My work removes these priors from both the policy architecture and the reward, and instead makes the training process itself responsive to the latent space that forms inside a modular encoder–controller architecture. The central hypothesis: the structured, periodic nature of stable quadruped locomotion can emerge as a consequence of optimisation, not as a precondition of it.

Three connected goals:

1. **Learning** — learn structured, generalisable latent representations of the robot's dynamics and its environment.
2. **Understanding** — understand how these representations modulate adaptive behaviour: gait, stability, transitions.
3. **Applying** — use what the latent space reveals to improve training — curricula, exploration, control architectures.

Platform: PPO, NVIDIA Isaac Sim / Isaac Lab, Unitree Go1/Go2.
