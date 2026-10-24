"""exp009: ColoredMNIST spurious_p sweep (exp005 non-RL equivalent)."""

import sys
import os
import numpy as np
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from experiments.run_colored_mnist import run_one_seed


def main():
    cfg_path = (sys.argv[1] if len(sys.argv) > 1
                else os.path.join(os.path.dirname(__file__),
                                  "configs", "exp009_cmnist_psweep.yaml"))
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    os.makedirs(cfg["output_dir"], exist_ok=True)

    seeds = cfg["evaluation"]["seeds"]
    p_values = cfg["data"]["p_values"]

    print(f"Experiment : {cfg['name']}")
    print(f"Seeds      : {seeds}")
    print(f"p_values   : {p_values}")
    print()

    # per-p results: p -> list of seed records
    by_p = {}

    for p in p_values:
        print(f"{'='*60}")
        print(f"spurious_p = {p}")
        print(f"{'='*60}")

        seed_cfg = dict(cfg)
        seed_cfg["data"] = dict(cfg["data"])
        seed_cfg["data"]["spurious_p"] = p

        records = []
        for seed in seeds:
            rec = run_one_seed(seed, seed_cfg)
            records.append(rec)
            print(f"[DONE] seed={seed}: AA={rec['aa']:.3f}, "
                  f"Δ_hue={rec['delta_hue']:.3f}, Δ_struct={rec['delta_struct']:.3f}, "
                  f"correct={rec['correct']}, collapse={rec['collapse']}")
        by_p[p] = records
        print()

    # Summary table
    print("=" * 60)
    print("SUMMARY")
    print(f"{'p':>4}  {'AA>=0.9':>8}  {'detect':>7}  {'Stage2':>7}  {'e2e':>5}  mean_AA  mean_J_oracle")
    rows = []
    for p in p_values:
        recs = by_p[p]
        n = len(recs)
        aa_pass   = sum(r["aa_pass"] for r in recs)
        correct   = sum(r["correct"] for r in recs)
        collapsed = sum(r["collapse"] for r in recs)
        e2e       = sum(r["correct"] and r["collapse"] for r in recs)
        mean_aa   = np.mean([r["aa"] for r in recs])
        mean_jo   = np.mean([r["j_oracle"] for r in recs])
        print(f"{p:>4}  {aa_pass}/{n}       {correct}/{n}      {collapsed}/{n}      {e2e}/{n}   {mean_aa:.3f}    {mean_jo:.3f}")
        rows.append((p, aa_pass, correct, collapsed, e2e, mean_aa, mean_jo, n))

    # Save summary
    summary_path = os.path.join(cfg["output_dir"], "summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"=== {cfg['name']} ===\n")
        f.write(f"stage2_p={cfg['data']['stage2_p']}\n\n")
        f.write(f"{'p':>4}  {'AA>=0.9':>8}  {'detect':>7}  {'Stage2':>7}  {'e2e':>5}  mean_AA  mean_J_oracle\n")
        for (p, aa_pass, correct, collapsed, e2e, mean_aa, mean_jo, n) in rows:
            f.write(f"{p:>4}  {aa_pass}/{n}       {correct}/{n}      {collapsed}/{n}      {e2e}/{n}   {mean_aa:.3f}    {mean_jo:.3f}\n")
        f.write("\nPer-seed:\n")
        for p in p_values:
            for r in by_p[p]:
                f.write(f"  p={p} seed={r['seed']}: AA={r['aa']:.3f}, "
                        f"J_oracle={r['j_oracle']:.3f}, "
                        f"delta_hue={r['delta_hue']:.3f}, delta_struct={r['delta_struct']:.3f}, "
                        f"correct={r['correct']}, collapse={r['collapse']}\n")


if __name__ == "__main__":
    main()
