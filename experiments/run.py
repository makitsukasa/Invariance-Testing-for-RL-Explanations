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
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    env_base = cfg.get("env", {}).get("base", "")

    if "CartPole" in env_base:
        if cfg.get("env", {}).get("shift_conditions") or cfg.get("env", {}).get("gravity_conditions"):
            from experiments.run_gravity import run_experiment
        else:
            from experiments.run_cartpole import run_experiment
        run_experiment(cfg)
    elif "GridWorld" in env_base or "grid" in env_base.lower():
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
