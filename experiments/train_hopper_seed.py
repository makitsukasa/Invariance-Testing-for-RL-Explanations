"""Hopper SAC 単一シード訓練スクリプト（並列実行用）。

使い方:
    python experiments/train_hopper_seed.py --seed 123 --n_steps 500000 --out_dir experiments/results/exp007_mujoco_v2
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import gymnasium as gym
from stable_baselines3 import SAC


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--n_steps", type=int, default=500000)
    parser.add_argument("--out_dir", type=str, default="experiments/results/exp007_mujoco_v2")
    args = parser.parse_args()

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / f"intuitive_hopper_seed{args.seed}"

    if model_path.with_suffix(".zip").exists():
        print(f"[Hopper seed={args.seed}] 既存モデルあり、スキップ", flush=True)
        return

    env = gym.make("Hopper-v5")
    model = SAC(
        "MlpPolicy", env,
        learning_rate=3e-4, batch_size=256,
        buffer_size=100000, learning_starts=5000,
        seed=args.seed, verbose=0,
    )
    model.learn(total_timesteps=args.n_steps)
    model.save(str(model_path))
    env.close()
    print(f"[Hopper seed={args.seed}] SAC 学習完了 ({args.n_steps} steps)", flush=True)


if __name__ == "__main__":
    main()
