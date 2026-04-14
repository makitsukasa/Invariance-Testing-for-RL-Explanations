"""統合実験エントリポイント。

使い方:
    python experiments/run.py --config experiments/configs/exp001_cartpole_noise.yaml
    python experiments/run.py --config experiments/configs/exp002_spurious_gridworld.yaml

新しい実験を追加するときは configs/exp00N_xxx.yaml を作成し、
env.base に環境名を指定してください。
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import yaml


def main():
    parser = argparse.ArgumentParser(description="実験ランナー")
    parser.add_argument("--config", required=True, help="YAML 設定ファイルのパス")
    parser.add_argument("--seed", type=int, default=None, help="シードを1つ指定して実行（並列化用）")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if args.seed is not None:
        cfg["evaluation"]["seeds"] = [args.seed]

    env_cfg = cfg.get("env", {})
    env_base = env_cfg.get("base", "")
    env_type = env_cfg.get("type", "")

    # MuJoCo/LunarLander 予備実験（lunar または hopper キーで判定）
    if cfg.get("lunar") or cfg.get("hopper"):
        from experiments.run_mujoco import run_experiment
        run_experiment(cfg)
    # 蒸留感度分析（distill_n_samples_list キーで判定）
    elif cfg.get("distill_n_samples_list"):
        from experiments.run_distill_sensitivity import run_experiment
        run_experiment(cfg)
    # comparison 実験（model_types キーで判定）
    elif cfg.get("comparison", {}).get("model_types"):
        from experiments.run_comparison import run_experiment
        run_experiment(cfg)
    elif "CartPole" in env_base or env_cfg.get("noise_dim") is not None:
        if env_cfg.get("shift_conditions") or env_cfg.get("gravity_conditions"):
            from experiments.run_gravity import run_experiment
        else:
            from experiments.run_cartpole import run_experiment
        run_experiment(cfg)
    elif "GridWorld" in env_base or "grid" in env_base.lower() or "grid" in env_type.lower():
        from experiments.run_gridworld import run_experiment
        run_experiment(cfg)
    else:
        print(
            f"Error: 未対応の env.base: '{env_base}'\n"
            "CartPole または GridWorld を指定してください。",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
