"""LunarLander ablation experiment — exp007.

Zone bonus × c_mode ablation を走らせ、以下の採用基準を事前固定して検証する:

  Stage1 PASS  : AA >= 0.9  AND  J_oracle > 200
  Ablation PASS: J_oracle(c_correlated) > J_oracle(no_c) > 50
  Stage2 PASS  : c_collapse only for c_correlated  (no_c・c_random は collapse しない)
  Intervention : selected == "c (spurious)"  (c_correlated のみ)

Usage:
    python experiments/run_lunar_ablation.py --config experiments/configs/exp007_ablation_lunar.yaml
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from stable_baselines3 import PPO

from experiments.src.spurious_lunar_env import SpuriousLunarLander
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.evaluate import action_agreement, evaluate_rollout

N_ACTIONS = 4

# ---------------------------------------------------------------------------
# Per-seed pipeline
# ---------------------------------------------------------------------------

def _train_oracle(seed: int, env_kwargs: dict, oracle_cfg: dict) -> PPO:
    env = SpuriousLunarLander(**env_kwargs)
    model = PPO(
        "MlpPolicy", env, seed=seed, verbose=0,
        gamma=oracle_cfg["gamma"],
        gae_lambda=oracle_cfg["gae_lambda"],
        ent_coef=oracle_cfg["ent_coef"],
        n_steps=oracle_cfg["n_steps_per_rollout"],
        batch_size=oracle_cfg["batch_size"],
        n_epochs=oracle_cfg["n_epochs"],
    )
    model.learn(total_timesteps=oracle_cfg["n_steps"])
    env.close()
    return model


def _collect_transitions(
    model: PPO,
    env_kwargs: dict,
    seed: int,
    n_samples: int,
) -> tuple[np.ndarray, np.ndarray]:
    env = SpuriousLunarLander(**env_kwargs)
    obs_list, act_list = [], []
    rng = np.random.default_rng(seed)
    obs, _ = env.reset(seed=int(rng.integers(1_000_000)))
    while len(obs_list) < n_samples:
        action, _ = model.predict(obs, deterministic=True)
        obs_list.append(obs.copy())
        act_list.append(int(action))
        obs, _, terminated, truncated, _ = env.step(int(action))
        if terminated or truncated:
            obs, _ = env.reset(seed=int(rng.integers(1_000_000)))
    env.close()
    return np.array(obs_list, dtype=np.float32), np.array(act_list, dtype=np.int64)


def _eval_intervention(
    surrogate: SoftMoET,
    env_kwargs: dict,
    feature_idx: int,
    feat_lo: float,
    feat_hi: float,
    n_episodes: int,
    seed: int,
) -> float:
    env = SpuriousLunarLander(**env_kwargs)
    rng = np.random.default_rng(seed + feature_idx * 997)
    total = 0.0
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        done = False
        while not done:
            obs_p = obs.copy()
            obs_p[feature_idx] = float(rng.uniform(feat_lo, feat_hi))
            action = int(surrogate.predict(obs_p[np.newaxis])[0])
            obs, reward, terminated, truncated, _ = env.step(action)
            total += reward
            done = terminated or truncated
    env.close()
    return total / n_episodes


def run_one_seed(
    seed: int,
    condition: dict,
    zone_bonus: float,
    weak_signal: str,
    cfg: dict,
) -> tuple[dict, list[str]]:
    import torch
    torch.set_num_threads(2)  # 4 workers × 2 threads = 8 threads on 16 logical cores

    cname = condition["name"]
    logs = [f"\n{'='*60}", f"Seed {seed} | cond={cname} | zone_bonus={zone_bonus}", "="*60]

    c_mode    = condition["c_mode"]
    spurious_p = condition.get("spurious_p", 0.0)
    n_episodes = cfg["evaluation"]["n_eval_episodes"]
    n_distill  = cfg["surrogate"]["n_distill_samples"]
    n_eval     = cfg["evaluation"]["n_eval_samples"]

    # Common env kwargs (training distribution)
    train_kwargs = dict(
        c_mode=c_mode, spurious_p=spurious_p,
        weak_signal=weak_signal, zone_bonus=zone_bonus,
        vx_nudge_scale=cfg["env"].get("vx_nudge_scale", 0.25),
        z_weak_noise_std=cfg["env"].get("z_weak_noise_std", 1.0),
    )

    logs.append("  [1/4] Oracle training (PPO)...")
    model = _train_oracle(seed, train_kwargs, cfg["oracle"])

    logs.append("  [2/4] Data collection...")
    obs_distill, act_distill = _collect_transitions(model, train_kwargs, seed,          n_distill)
    obs_eval,   _            = _collect_transitions(model, train_kwargs, seed + 10_000, n_eval)

    # Infer obs dim from data
    n_obs       = obs_distill.shape[1]
    spurious_idx = n_obs - 1  # c is always last

    # Feature names from a temporary env
    _tmp_env = SpuriousLunarLander(**train_kwargs)
    feature_names = _tmp_env.feature_names
    _tmp_env.close()

    logs.append("  [3/4] Surrogate training (MoET)...")
    moet = SoftMoET(n_obs, N_ACTIONS, cfg["surrogate"]["n_experts"], cfg["surrogate"]["max_depth"])
    moet = distill(moet, obs_distill, act_distill, epochs=cfg["surrogate"]["distill_epochs"])

    oracle_actions, _ = model.predict(obs_eval, deterministic=True)
    aa_train    = action_agreement(obs_eval, oracle_actions, moet)
    stage1_pass = aa_train >= cfg["adoption_criteria"]["aa_min"]

    train_env      = SpuriousLunarLander(**train_kwargs)
    j_oracle_train = evaluate_rollout(model, train_env, n_episodes, seed + 20_000)
    j_s_train      = evaluate_rollout(moet,  train_env, n_episodes, seed + 20_000)
    train_env.close()
    logs.append(f"    Stage 1: AA={aa_train:.3f} ({'PASS' if stage1_pass else 'FAIL'}), "
                f"J_oracle={j_oracle_train:.1f}, J_S_train={j_s_train:.1f}")

    # Stage 2: c-reversed (only meaningful for correlated c)
    rev_kwargs = {**train_kwargs, "eval_mode": "reversed"}
    rev_env    = SpuriousLunarLander(**rev_kwargs)
    j_s_rev    = evaluate_rollout(moet, rev_env, n_episodes, seed + 30_000)
    rev_env.close()
    c_collapse = (j_s_train > 0) and (j_s_rev < cfg["adoption_criteria"]["j_s_rev_ratio_max"] * j_s_train)
    logs.append(f"    Stage 2 (c reversed): J_S={j_s_rev:.1f} -> "
                f"{'COLLAPSE' if c_collapse else 'no collapse'}")

    logs.append("  [4/4] Per-feature intervention test...")
    feat_ranges = [
        (float(obs_distill[:, i].min()), float(obs_distill[:, i].max()))
        for i in range(n_obs)
    ]
    j_s_feat: list[float] = []
    for fi in range(n_obs):
        lo, hi = feat_ranges[fi]
        j_f = _eval_intervention(moet, train_kwargs, fi, lo, hi, n_episodes, seed + 50_000)
        j_s_feat.append(j_f)
        logs.append(f"    {feature_names[fi]}: J_S_perturbed={j_f:.1f}")

    delta = [j_s_train - j_f for j_f in j_s_feat]
    top_idx = int(np.argmax(delta))
    intervention_correct = (top_idx == spurious_idx)
    delta_str = ", ".join(f"{feature_names[i]}={delta[i]:.2f}" for i in range(n_obs))
    logs.append(f"    Δ: {delta_str}")
    logs.append(f"    Auto-selected: {feature_names[top_idx]} -> "
                f"{'CORRECT' if intervention_correct else 'WRONG'}")

    result = {
        "condition": cname,
        "zone_bonus": zone_bonus,
        "seed": seed,
        "aa_train": aa_train,
        "stage1_pass": stage1_pass,
        "j_oracle_train": j_oracle_train,
        "j_s_train": j_s_train,
        "j_s_c_reversed": j_s_rev,
        "c_collapse": c_collapse,
        **{f"j_s_{feature_names[i]}_perturbed": j_s_feat[i] for i in range(n_obs)},
        **{f"delta_{feature_names[i]}": delta[i] for i in range(n_obs)},
        "intervention_selected": feature_names[top_idx],
        "intervention_correct": intervention_correct,
    }
    return result, logs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    output_dir = ROOT / cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    seeds       = cfg["evaluation"]["seeds"]
    n_workers   = cfg.get("n_workers", 4)
    weak_signal = cfg["env"]["weak_signal"]
    conditions  = cfg["ablation_conditions"]
    zone_bonuses = cfg["env"]["zone_bonus_sweep"]

    print(f"Experiment : {cfg.get('name', 'unknown')}")
    print(f"Seeds      : {seeds}")
    print(f"Workers    : {n_workers}")
    print(f"Conditions : {[c['name'] for c in conditions]}")
    print(f"Zone bonus : {zone_bonuses}")

    all_records: list[dict] = []
    all_logs: list[tuple[int, str, float, list[str]]] = []

    for zone_bonus in zone_bonuses:
        for condition in conditions:
            cname = condition["name"]
            print(f"\n--- zone_bonus={zone_bonus}, condition={cname} ---")

            with ProcessPoolExecutor(max_workers=n_workers) as ex:
                futures = {
                    ex.submit(run_one_seed, s, condition, zone_bonus, weak_signal, cfg): s
                    for s in seeds
                }
                for future in as_completed(futures):
                    seed = futures[future]
                    rec, logs = future.result()
                    all_records.append(rec)
                    all_logs.append((seed, cname, zone_bonus, logs))
                    delta_c = rec.get("delta_c (spurious)", float("nan"))
                    print(f"[DONE] seed={seed}: AA={rec['aa_train']:.3f}, "
                          f"J_oracle={rec['j_oracle_train']:.1f}, "
                          f"Δ_c={delta_c:.1f}, "
                          f"selected={rec['intervention_selected']}, "
                          f"correct={rec['intervention_correct']}, "
                          f"collapse={rec['c_collapse']}")

    for seed, cname, zb, logs in sorted(all_logs, key=lambda x: (x[2], x[1], x[0])):
        for line in logs:
            print(line)

    df = pd.DataFrame(all_records)
    df.to_csv(output_dir / "results.csv", index=False)

    _print_summary(df, cfg)
    _save_summary_txt(df, cfg, output_dir)
    _plot(df, output_dir, cfg)
    print(f"\nResults: {output_dir}")


def _print_summary(df: pd.DataFrame, cfg: dict) -> None:
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    crit = cfg["adoption_criteria"]

    for zb in sorted(df["zone_bonus"].unique()):
        print(f"\n  zone_bonus={zb}")
        df_z = df[df["zone_bonus"] == zb]
        for cname in df_z["condition"].unique():
            d = df_z[df_z["condition"] == cname]
            n = len(d)
            s1   = d["stage1_pass"].mean()
            coll = d["c_collapse"].mean()
            corr = d["intervention_correct"].mean()
            jo   = d["j_oracle_train"].mean()
            js   = d["j_s_train"].mean()
            print(f"    {cname:25s}: Stage1={s1:.0%}({d['stage1_pass'].sum()}/{n}), "
                  f"J_oracle={jo:.1f}, J_S={js:.1f}, "
                  f"collapse={coll:.0%}, intervention_correct={corr:.0%}")

    print(f"\nAdoption criteria:")
    print(f"  AA >= {crit['aa_min']}, J_oracle > {crit['j_oracle_min']}, "
          f"J_S_rev_ratio < {crit['j_s_rev_ratio_max']}")


def _save_summary_txt(df: pd.DataFrame, cfg: dict, output_dir: Path) -> None:
    lines = [f"=== {cfg.get('name', 'experiment')} ===", cfg.get("description", ""), ""]
    crit = cfg["adoption_criteria"]
    lines.append(f"Pre-fixed adoption criteria:")
    lines.append(f"  Stage1: AA >= {crit['aa_min']} AND J_oracle > {crit['j_oracle_min']}")
    lines.append(f"  Stage2: J_S_rev < {crit['j_s_rev_ratio_max']} * J_S_train  (only c_correlated)")
    lines.append(f"  Ablation: J_oracle(corr) > J_oracle(no_c) > {crit.get('j_oracle_no_c_min', 50)}")
    lines.append(f"  Intervention: selected == 'c (spurious)'  (c_correlated only)")
    lines.append("")

    for zb in sorted(df["zone_bonus"].unique()):
        lines.append(f"zone_bonus={zb}")
        df_z = df[df["zone_bonus"] == zb]
        for cname in df_z["condition"].unique():
            d = df_z[df_z["condition"] == cname]
            n = len(d)
            lines.append(
                f"  {cname}: AA={d['aa_train'].mean():.3f}+-{d['aa_train'].std():.3f}, "
                f"J_oracle={d['j_oracle_train'].mean():.1f}+-{d['j_oracle_train'].std():.1f}, "
                f"J_S={d['j_s_train'].mean():.1f}, "
                f"collapse={d['c_collapse'].mean():.0%}, "
                f"correct={d['intervention_correct'].mean():.0%} ({d['intervention_correct'].sum()}/{n})"
            )
        lines.append("")

    (output_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"summary.txt -> {output_dir / 'summary.txt'}")


def _plot(df: pd.DataFrame, output_dir: Path, cfg: dict) -> None:
    conditions = [c["name"] for c in cfg["ablation_conditions"]]
    zone_bonuses = sorted(df["zone_bonus"].unique())
    n_zb = len(zone_bonuses)
    n_cond = len(conditions)

    fig, axes = plt.subplots(2, n_zb, figsize=(5 * n_zb, 8))
    if n_zb == 1:
        axes = axes[:, np.newaxis]

    for zi, zb in enumerate(zone_bonuses):
        df_z = df[df["zone_bonus"] == zb]

        # Top: J_oracle per condition
        ax = axes[0, zi]
        means = [df_z[df_z["condition"] == c]["j_oracle_train"].mean() for c in conditions]
        stds  = [df_z[df_z["condition"] == c]["j_oracle_train"].std()  for c in conditions]
        colors = ["tomato" if "correlated" in c else ("steelblue" if "random" in c else "gray")
                  for c in conditions]
        ax.bar(range(n_cond), means, yerr=stds, color=colors, capsize=4)
        ax.set_xticks(range(n_cond)); ax.set_xticklabels(conditions, rotation=20, ha="right", fontsize=7)
        ax.axhline(cfg["adoption_criteria"]["j_oracle_min"], color="red", linestyle="--", linewidth=0.8)
        ax.set_title(f"J_oracle (zone_bonus={zb})")
        ax.set_ylabel("Mean episode reward")

        # Bottom: J_S_train vs J_S_rev per condition
        ax = axes[1, zi]
        x = np.arange(n_cond)
        w = 0.35
        means_tr  = [df_z[df_z["condition"] == c]["j_s_train"].mean()      for c in conditions]
        means_rev = [df_z[df_z["condition"] == c]["j_s_c_reversed"].mean() for c in conditions]
        ax.bar(x - w/2, means_tr,  w, label="J_S_train",   color="steelblue")
        ax.bar(x + w/2, means_rev, w, label="J_S_reversed", color="tomato")
        ax.set_xticks(x); ax.set_xticklabels(conditions, rotation=20, ha="right", fontsize=7)
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_title(f"Surrogate: train vs c-reversed (zone_bonus={zb})")
        ax.set_ylabel("Mean episode reward")
        ax.legend(fontsize=7)

    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=120)
    plt.close()


if __name__ == "__main__":
    main()
