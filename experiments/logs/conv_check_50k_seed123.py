import sys
sys.path.insert(0, "experiments")
from pathlib import Path
from src.cartpole_intuitive import train_intuitive
from src.cartpole_env import NoisyCartPoleEnv
from stable_baselines3.common.evaluation import evaluate_policy

check_dir = Path("experiments/results/conv_check_50k")
check_dir.mkdir(parents=True, exist_ok=True)
seed = 123
print(f"Training seed={seed} for 50,000 steps...", flush=True)
model_path = check_dir / f"check_seed{seed}"
model = train_intuitive(0, 50_000, seed, model_path)
env = NoisyCartPoleEnv(noise_dim=0)
j, _ = evaluate_policy(model, env, n_eval_episodes=50, deterministic=True)
env.close()
print(f"RESULT seed={seed}: J={j:.1f}", flush=True)
