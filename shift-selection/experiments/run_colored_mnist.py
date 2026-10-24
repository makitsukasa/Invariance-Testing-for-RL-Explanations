"""exp008: ColoredMNIST + CNN surrogate distillation + intervention test."""

import sys
import os
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from experiments.src.colored_mnist import ColoredMNIST, hue_shuffle, structure_noise


# ── model ────────────────────────────────────────────────────────────────────

class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Flatten(),
            nn.Linear(32 * 7 * 7, 128), nn.ReLU(),
            nn.Linear(128, 2),
        )

    def forward(self, x):
        return self.net(x)


# ── training helpers ──────────────────────────────────────────────────────────

def train_model(model, loader, epochs, lr):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    model.train()
    for _ in range(epochs):
        for x, y in loader:
            opt.zero_grad()
            criterion(model(x), y).backward()
            opt.step()


def predict(model, images):
    model.eval()
    with torch.no_grad():
        return model(images).argmax(1)


def batch_predict(model, images, batch_size=512):
    preds = []
    for i in range(0, len(images), batch_size):
        preds.append(predict(model, images[i:i + batch_size]))
    return torch.cat(preds)


def accuracy_on(model, images, labels):
    preds = batch_predict(model, images)
    return (preds == labels).float().mean().item()


def agreement(model_a, model_b, images):
    pa = batch_predict(model_a, images)
    pb = batch_predict(model_b, images)
    return (pa == pb).float().mean().item()


# ── experiment ────────────────────────────────────────────────────────────────

def run_one_seed(seed, cfg):
    torch.manual_seed(seed)
    np.random.seed(seed)

    data_cfg = cfg["data"]
    oracle_cfg = cfg["oracle"]
    surr_cfg = cfg["surrogate"]
    eval_cfg = cfg["evaluation"]

    # [1/4] Load data
    label_noise_p = data_cfg.get("label_noise_p", 0.0)
    train_ds = ColoredMNIST(data_cfg["root"], train=True,
                             spurious_p=data_cfg["spurious_p"],
                             label_noise_p=label_noise_p, seed=seed)
    test_corr = ColoredMNIST(data_cfg["root"], train=False,
                              spurious_p=data_cfg["spurious_p"],
                              label_noise_p=label_noise_p, seed=seed + 1000)
    test_anti = ColoredMNIST(data_cfg["root"], train=False,
                              spurious_p=data_cfg["stage2_p"],
                              label_noise_p=label_noise_p, seed=seed + 2000)

    train_loader = DataLoader(train_ds, batch_size=oracle_cfg["batch_size"], shuffle=True)

    # [2/4] Train oracle
    print(f"  [2/4] Oracle training...")
    oracle = CNN()
    train_model(oracle, train_loader, oracle_cfg["epochs"], oracle_cfg["lr"])
    j_oracle = accuracy_on(oracle, test_corr.images, test_corr.labels)

    # [3/4] Distill surrogate from oracle labels on training data
    print(f"  [3/4] Surrogate distillation...")
    oracle_labels = batch_predict(oracle, train_ds.images)
    distill_ds = TensorDataset(train_ds.images, oracle_labels)
    distill_loader = DataLoader(distill_ds, batch_size=surr_cfg["batch_size"], shuffle=True)

    surrogate = CNN()
    train_model(surrogate, distill_loader, surr_cfg["epochs"], surr_cfg["lr"])

    # Stage 1: AA
    aa = agreement(oracle, surrogate, test_corr.images)
    aa_pass = aa >= 0.9

    # [4/4] Intervention test
    print(f"  [4/4] Intervention test...")
    j_s_train = accuracy_on(surrogate, test_corr.images, test_corr.labels)

    j_hue    = accuracy_on(surrogate, hue_shuffle(test_corr.images, seed=seed),         test_corr.labels)
    j_struct = accuracy_on(surrogate, structure_noise(test_corr.images, seed=seed),     test_corr.labels)

    delta_hue    = j_s_train - j_hue
    delta_struct = j_s_train - j_struct

    selected = "hue" if delta_hue > delta_struct else "structure"
    correct  = selected == "hue"

    # Stage 2: anti-correlated distribution
    j_s_anti = accuracy_on(surrogate, test_anti.images, test_anti.labels)
    collapse = j_s_anti < eval_cfg["collapse_threshold"]

    print(f"    Stage 1: AA={aa:.3f} ({'PASS' if aa_pass else 'FAIL'}), J_oracle={j_oracle:.3f}, J_S_train={j_s_train:.3f}")
    print(f"    Stage 2 (anti-corr): J_S={j_s_anti:.3f} -> {'collapse' if collapse else 'no collapse'}")
    print(f"    Δ: hue={delta_hue:.3f}, structure={delta_struct:.3f}")
    print(f"    Auto-selected: {selected} -> {'CORRECT' if correct else 'WRONG'}")

    return {
        "seed": seed,
        "j_oracle": j_oracle,
        "aa": aa,
        "aa_pass": aa_pass,
        "j_s_train": j_s_train,
        "delta_hue": delta_hue,
        "delta_struct": delta_struct,
        "selected": selected,
        "correct": correct,
        "j_s_anti": j_s_anti,
        "collapse": collapse,
    }


def main():
    cfg_path = (sys.argv[1] if len(sys.argv) > 1
                else os.path.join(os.path.dirname(__file__),
                                  "configs", "exp008_colored_mnist.yaml"))
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    os.makedirs(cfg["output_dir"], exist_ok=True)

    seeds = cfg["evaluation"]["seeds"]
    results = []

    print(f"Experiment : {cfg['name']}")
    print(f"Seeds      : {seeds}")
    print(f"spurious_p : {cfg['data']['spurious_p']} (train)  /  {cfg['data']['stage2_p']} (Stage 2)")
    print()

    for seed in seeds:
        print(f"{'='*60}")
        print(f"Seed {seed}")
        print(f"{'='*60}")
        rec = run_one_seed(seed, cfg)
        results.append(rec)
        print(f"[DONE] seed={seed}: AA={rec['aa']:.3f}, J_oracle={rec['j_oracle']:.3f}, "
              f"Δ_hue={rec['delta_hue']:.3f}, Δ_struct={rec['delta_struct']:.3f}, "
              f"selected={rec['selected']}, correct={rec['correct']}, collapse={rec['collapse']}")
        print()

    # Summary
    n = len(results)
    aa_pass   = sum(r["aa_pass"] for r in results)
    correct   = sum(r["correct"] for r in results)
    collapsed = sum(r["collapse"] for r in results)

    print("=" * 60)
    print(f"SUMMARY ({n} seeds)")
    print(f"  Stage 1 pass (AA>=0.9) : {aa_pass}/{n}")
    print(f"  Intervention correct   : {correct}/{n}")
    print(f"  Stage 2 collapse       : {collapsed}/{n}")
    print(f"  mean AA       : {np.mean([r['aa'] for r in results]):.3f}")
    print(f"  mean J_oracle : {np.mean([r['j_oracle'] for r in results]):.3f}")
    print(f"  mean Δ_hue    : {np.mean([r['delta_hue'] for r in results]):.3f}")
    print(f"  mean Δ_struct : {np.mean([r['delta_struct'] for r in results]):.3f}")

    # Save summary
    summary_path = os.path.join(cfg["output_dir"], "summary.txt")
    with open(summary_path, "w") as f:
        f.write(f"=== {cfg['name']} ===\n")
        f.write(f"spurious_p={cfg['data']['spurious_p']} (train), stage2_p={cfg['data']['stage2_p']}\n\n")
        f.write(f"Stage 1 pass (AA>=0.9): {aa_pass}/{n}\n")
        f.write(f"Intervention correct  : {correct}/{n}\n")
        f.write(f"Stage 2 collapse      : {collapsed}/{n}\n")
        f.write(f"mean AA       : {np.mean([r['aa'] for r in results]):.3f}\n")
        f.write(f"mean J_oracle : {np.mean([r['j_oracle'] for r in results]):.3f}\n")
        f.write(f"mean Δ_hue    : {np.mean([r['delta_hue'] for r in results]):.3f}\n")
        f.write(f"mean Δ_struct : {np.mean([r['delta_struct'] for r in results]):.3f}\n\n")
        for r in results:
            f.write(f"  seed={r['seed']}: AA={r['aa']:.3f}, J_oracle={r['j_oracle']:.3f}, "
                    f"Δ_hue={r['delta_hue']:.3f}, Δ_struct={r['delta_struct']:.3f}, "
                    f"selected={r['selected']}, correct={r['correct']}, collapse={r['collapse']}\n")


if __name__ == "__main__":
    main()
