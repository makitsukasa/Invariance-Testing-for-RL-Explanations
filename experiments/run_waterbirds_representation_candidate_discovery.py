"""exp026: Waterbirds candidate discovery with CLIP / SSL representations.

This experiment compares representation-based candidate discovery methods on
Waterbirds and measures how well their top-1 candidate aligns with the
confirmation signal from exp022.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import yaml
from PIL import Image

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from experiments.src.representation_backends import build_backend, cosine_distance

SPURIOUS_FEATURE = "background"
CAUSAL_FEATURE = "foreground"

_WORKER_BASE_MASK_CACHE: dict[int, np.ndarray] | None = None
_WORKER_CACHE_PATH: str | None = None
_BACKEND_OBJECTS: dict[str, object] | None = None


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _config_hash(cfg: dict) -> str:
    return json.dumps(cfg, sort_keys=True, ensure_ascii=False).encode("utf-8").hex()[:32]


def _load_metadata(root: str) -> pd.DataFrame:
    meta = pd.read_csv(Path(root) / "metadata.csv")
    meta["split"] = meta["split"].astype(int)
    meta["y"] = meta["y"].astype(int)
    meta["place"] = meta["place"].astype(int)
    return meta


def _load_img(root: str, rel_path: str) -> np.ndarray:
    return np.array(Image.open(Path(root) / rel_path).convert("RGB"))


def _select_eval_rows(meta: pd.DataFrame, n_eval: int, seed: int) -> pd.DataFrame:
    rows = meta[meta["split"] == 2].reset_index(drop=True).copy()
    rows["dataset_idx"] = np.arange(len(rows), dtype=int)
    rng = np.random.default_rng(seed)
    order = np.arange(len(rows))
    rng.shuffle(order)
    rows = rows.iloc[order[: min(n_eval, len(rows))]].reset_index(drop=True)
    return rows


def _perturb_mask(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius == 0:
        return mask
    k = abs(int(radius)) * 2 + 1
    kernel = np.ones((k, k), np.uint8)
    if radius > 0:
        out = cv2.dilate(mask.astype(np.uint8), kernel, iterations=1)
    else:
        out = cv2.erode(mask.astype(np.uint8), kernel, iterations=1)
    return (out > 0).astype(np.uint8)


def _resize_to(img_np: np.ndarray, shape_hw: tuple[int, int]) -> np.ndarray:
    h, w = shape_hw
    return cv2.resize(img_np, (w, h), interpolation=cv2.INTER_AREA)


def _apply_background_replacement(img_np: np.ndarray, fg_mask: np.ndarray, donor_np: np.ndarray) -> np.ndarray:
    donor_np = _resize_to(donor_np, img_np.shape[:2])
    out = img_np.copy()
    out[fg_mask == 0] = donor_np[fg_mask == 0]
    return out


def _apply_foreground_replacement(img_np: np.ndarray, fg_mask: np.ndarray, donor_np: np.ndarray) -> np.ndarray:
    donor_np = _resize_to(donor_np, img_np.shape[:2])
    out = img_np.copy()
    out[fg_mask == 1] = donor_np[fg_mask == 1]
    return out


def _build_class_donor_pool(root: str, meta: pd.DataFrame, y: int, n_samples: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    rows = meta[(meta["split"] == 0) & (meta["y"] == y)].to_dict("records")
    rng.shuffle(rows)
    pool: list[np.ndarray] = []
    for row in rows:
        if len(pool) >= n_samples:
            break
        pool.append(_load_img(root, row["img_filename"]))
    return pool


def _load_or_build_mask_cache(root: str, output_dir: Path, cfg: dict) -> dict[int, np.ndarray]:
    external = cfg.get("input", {}).get("mask_cache_path")
    if external:
        ext_path = ROOT / external
        if ext_path.exists():
            return torch.load(ext_path, map_location="cpu", weights_only=False)
    path = output_dir / "base_mask_cache.pt"
    if path.exists():
        return torch.load(path, map_location="cpu", weights_only=False)
    raise FileNotFoundError(f"mask cache not found: {path}")


def _init_worker(cache_path: str, repr_cfg: dict) -> None:
    global _WORKER_BASE_MASK_CACHE, _WORKER_CACHE_PATH, _BACKEND_OBJECTS
    _WORKER_CACHE_PATH = cache_path
    _WORKER_BASE_MASK_CACHE = torch.load(cache_path, map_location="cpu", weights_only=False)
    _BACKEND_OBJECTS = {}
    for spec in repr_cfg["methods"]:
        backend = build_backend(spec["backend"])
        _BACKEND_OBJECTS[str(spec["name"])] = backend
    try:
        cv2.setNumThreads(1)
    except Exception:
        pass


def _task_label(task: tuple[int, int]) -> str:
    seed, n_eval = task
    return f"seed={seed}, n_eval={n_eval}"


def _condition_slug(n_eval: int) -> str:
    return f"n_eval_{int(n_eval):04d}"


def _seed_log_path(output_dir: Path, n_eval: int, seed: int) -> Path:
    log_dir = output_dir / "seed_logs" / _condition_slug(n_eval)
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"seed_{seed:03d}.log"


def _save_records(records: list[dict], path: Path) -> pd.DataFrame:
    df = pd.DataFrame(records)
    if df.empty:
        df.to_csv(path, index=False)
        return df
    df = df.drop_duplicates(subset=["seed", "n_eval", "mask_radius", "method"], keep="last")
    df = df.sort_values(["n_eval", "mask_radius", "seed", "method"]).reset_index(drop=True)
    df.to_csv(path, index=False)
    return df


def _completed_tasks(df: pd.DataFrame, methods: list[str], radii: list[int]) -> set[tuple[int, int]]:
    if df.empty:
        return set()
    completed: set[tuple[int, int]] = set()
    target_count = len(methods) * len(radii)
    grouped = df.groupby(["seed", "n_eval"])
    for (seed, n_eval), group in grouped:
        if len(group) == target_count:
            completed.add((int(seed), int(n_eval)))
    return completed


def _estimate_remaining_minutes(cfg: dict, tasks: list[tuple[int, int]], n_workers: int) -> float:
    est = float(cfg.get("runtime", {}).get("estimated_minutes_per_task", 12.0))
    return (len(tasks) * est) / max(1, n_workers)


def _update_meta(
    meta_path: Path,
    cfg: dict,
    state: str,
    output_dir: Path,
    session_id: str,
    started_at: str,
    planned_tasks: list[tuple[int, int]],
    completed_tasks: list[tuple[int, int]],
    n_workers: int,
    estimate_minutes: float,
    no_resume: bool,
    completed_at: str | None = None,
) -> None:
    meta = {
        "experiment": cfg["name"],
        "state": state,
        "session_id": session_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "output_dir": str(output_dir).replace("\\", "/"),
        "config_hash": _config_hash(cfg),
        "resume_enabled": not no_resume,
        "planned_tasks": [{"seed": s, "n_eval": n} for s, n in planned_tasks],
        "completed_tasks": [{"seed": s, "n_eval": n} for s, n in completed_tasks],
        "n_workers": int(n_workers),
        "estimated_minutes_total": float(estimate_minutes),
        "estimated_minutes_per_task": float(cfg.get("runtime", {}).get("estimated_minutes_per_task", 0.0)),
        "mask_radii": [int(r) for r in cfg["intervention"]["mask_radii"]],
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_runtime_session(
    runtime_path: Path,
    session_id: str,
    started_at: str,
    ended_at: str,
    elapsed_sec: float,
    state: str,
    completed_task_count: int,
    planned_task_count: int,
    note: str,
) -> None:
    record = {
        "session_id": session_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "elapsed_sec": round(elapsed_sec, 3),
        "elapsed_hms": time.strftime("%H:%M:%S", time.gmtime(max(0.0, elapsed_sec))),
        "state": state,
        "completed_tasks": int(completed_task_count),
        "planned_tasks": int(planned_task_count),
        "note": note,
    }
    if runtime_path.exists():
        df = pd.read_csv(runtime_path)
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    else:
        df = pd.DataFrame([record])
    df.to_csv(runtime_path, index=False)


def _score_to_record(
    *,
    seed: int,
    n_eval: int,
    radius: int,
    method: str,
    scores: dict[str, float],
    reference: dict[str, float | bool],
    elapsed_sec: float,
) -> dict:
    ordered = [name for name, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]
    selected_feature = ordered[0]
    return {
        "seed": int(seed),
        "n_eval": int(n_eval),
        "mask_radius": int(radius),
        "method": method,
        "selected_feature": selected_feature,
        "selected_score": float(scores[selected_feature]),
        "bg_score": float(scores[SPURIOUS_FEATURE]),
        "fg_score": float(scores[CAUSAL_FEATURE]),
        "top1_hit": bool(selected_feature == SPURIOUS_FEATURE),
        "pc_reference_feature": SPURIOUS_FEATURE if bool(reference["delta_correct"]) else CAUSAL_FEATURE,
        "pc_top1_alignment": bool(selected_feature == (SPURIOUS_FEATURE if bool(reference["delta_correct"]) else CAUSAL_FEATURE)),
        "pc_delta_bg": float(reference["delta_bg"]),
        "pc_delta_fg": float(reference["delta_fg"]),
        "score_gap": float(scores[SPURIOUS_FEATURE] - scores[CAUSAL_FEATURE]),
        "task_elapsed_sec": float(elapsed_sec),
    }


def run_one_task(
    seed: int,
    n_eval: int,
    cfg: dict,
    delta_reference: dict[tuple[int, int], dict[str, float | bool]],
    output_dir: str,
) -> tuple[list[dict], list[str]]:
    global _WORKER_BASE_MASK_CACHE, _BACKEND_OBJECTS
    if _WORKER_BASE_MASK_CACHE is None or _BACKEND_OBJECTS is None:
        raise RuntimeError("worker is not initialized")

    root = cfg["data"]["root"]
    radii = [int(r) for r in cfg["intervention"]["mask_radii"]]
    donor_pool_n = int(cfg["candidate_discovery"]["donor_pool_n"])
    batch_size = int(cfg["candidate_discovery"]["batch_size"])
    outdir = Path(output_dir)
    logs = [
        f"\n{'=' * 60}",
        f"Seed {seed} / n_eval={n_eval}",
        f"{'=' * 60}",
    ]
    t0 = time.time()

    meta = _load_metadata(root)
    eval_rows = _select_eval_rows(meta, n_eval=n_eval, seed=seed)
    bg_pool_by_y = {
        0: _build_class_donor_pool(root, meta, y=0, n_samples=donor_pool_n, seed=seed),
        1: _build_class_donor_pool(root, meta, y=1, n_samples=donor_pool_n, seed=seed),
    }
    fg_pool_by_y = {
        0: _build_class_donor_pool(root, meta, y=0, n_samples=donor_pool_n, seed=seed + 97),
        1: _build_class_donor_pool(root, meta, y=1, n_samples=donor_pool_n, seed=seed + 97),
    }

    rng = np.random.default_rng(seed + n_eval * 17)
    donor_choices_bg = [int(rng.integers(0, donor_pool_n)) for _ in range(len(eval_rows))]
    donor_choices_fg = [int(rng.integers(0, donor_pool_n)) for _ in range(len(eval_rows))]

    examples: list[dict] = []
    for idx, row in enumerate(eval_rows.to_dict("records")):
        img_np = _load_img(root, row["img_filename"])
        dataset_idx = int(row["dataset_idx"])
        mask = _WORKER_BASE_MASK_CACHE[dataset_idx]
        examples.append({"img_np": img_np, "mask": mask, "y": int(row["y"])})

    records: list[dict] = []
    for radius in radii:
        orig_images: list[np.ndarray] = []
        bg_images: list[np.ndarray] = []
        fg_images: list[np.ndarray] = []
        for ex_idx, ex in enumerate(examples):
            y_i = int(ex["y"])
            mask = _perturb_mask(ex["mask"], radius)
            bg_donor = bg_pool_by_y[y_i][donor_choices_bg[ex_idx]]
            fg_donor = fg_pool_by_y[y_i][donor_choices_fg[ex_idx]]
            orig_images.append(ex["img_np"])
            bg_images.append(_apply_background_replacement(ex["img_np"], mask, bg_donor))
            fg_images.append(_apply_foreground_replacement(ex["img_np"], mask, fg_donor))

        ref_key = (int(seed), int(radius))
        if ref_key not in delta_reference:
            raise KeyError(f"Missing exp022 reference for seed={seed}, radius={radius}")
        ref = delta_reference[ref_key]

        for method_spec in cfg["representations"]["methods"]:
            method_name = str(method_spec["name"])
            backend = _BACKEND_OBJECTS[method_name]
            orig_emb = backend.encode(orig_images, batch_size=batch_size)
            bg_emb = backend.encode(bg_images, batch_size=batch_size)
            fg_emb = backend.encode(fg_images, batch_size=batch_size)
            bg_score = float(cosine_distance(orig_emb, bg_emb).mean())
            fg_score = float(cosine_distance(orig_emb, fg_emb).mean())
            records.append(
                _score_to_record(
                    seed=seed,
                    n_eval=n_eval,
                    radius=radius,
                    method=method_name,
                    scores={SPURIOUS_FEATURE: bg_score, CAUSAL_FEATURE: fg_score},
                    reference=ref,
                    elapsed_sec=time.time() - t0,
                )
            )
        logs.append(f"  radius={radius}: processed {len(cfg['representations']['methods'])} backends")

    logs.append(f"    Task elapsed: {time.time() - t0:.1f} sec")
    return records, logs


def _worker(args):
    seed, n_eval, cfg, delta_reference, output_dir = args
    return run_one_task(seed, n_eval, cfg, delta_reference, output_dir)


def _save_seed_log(output_dir: Path, n_eval: int, seed: int, logs: list[str]) -> None:
    _seed_log_path(output_dir, n_eval, seed).write_text("\n".join(logs) + "\n", encoding="utf-8")


def _save_summary(df: pd.DataFrame, cfg: dict, output_dir: Path, elapsed_sec: float) -> None:
    methods = [str(m["name"]) for m in cfg["representations"]["methods"]]
    n_eval_values = [int(v) for v in cfg["evaluation"]["n_eval_values"]]
    radii = [int(r) for r in cfg["intervention"]["mask_radii"]]

    lines = [
        f"=== {cfg['name']} ===",
        cfg.get("description", ""),
        "",
        f"Seeds      : {cfg['evaluation']['seeds']}",
        f"n_eval     : {n_eval_values}",
        f"mask_radii : {radii}",
        f"Methods    : {methods}",
        f"Elapsed    : {elapsed_sec / 60.0:.1f} min",
        "",
    ]
    for method in methods:
        lines.append(f"[{method}]")
        lines.append(f"{'n_eval':>6} | {'radius':>6} | {'top1':>6} | {'pc_align':>8} | {'score_gap':>9}")
        lines.append("-" * 46)
        sub = df[df["method"] == method]
        for n_eval in n_eval_values:
            for radius in radii:
                cond = sub[(sub["n_eval"] == n_eval) & (sub["mask_radius"] == radius)]
                if cond.empty:
                    continue
                lines.append(
                    f"{n_eval:>6d} | {radius:>6d} | "
                    f"{cond['top1_hit'].mean():>6.0%} | "
                    f"{cond['pc_top1_alignment'].mean():>8.0%} | "
                    f"{cond['score_gap'].mean():>9.3f}"
                )
        lines.append("")
    (output_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")


def _plot(df: pd.DataFrame, cfg: dict, output_dir: Path) -> None:
    if df.empty:
        return
    methods = [str(m["name"]) for m in cfg["representations"]["methods"]]
    n_eval_values = [int(v) for v in cfg["evaluation"]["n_eval_values"]]
    radii = [int(r) for r in cfg["intervention"]["mask_radii"]]

    fig, axes = plt.subplots(len(methods), 2, figsize=(10, 3.2 * len(methods)))
    if len(methods) == 1:
        axes = np.array([axes])

    for row_idx, method in enumerate(methods):
        sub = df[df["method"] == method]
        top1_grid = np.zeros((len(radii), len(n_eval_values)))
        align_grid = np.zeros((len(radii), len(n_eval_values)))
        for i, radius in enumerate(radii):
            for j, n_eval in enumerate(n_eval_values):
                cond = sub[(sub["mask_radius"] == radius) & (sub["n_eval"] == n_eval)]
                top1_grid[i, j] = cond["top1_hit"].mean() if not cond.empty else np.nan
                align_grid[i, j] = cond["pc_top1_alignment"].mean() if not cond.empty else np.nan

        ax = axes[row_idx, 0]
        im = ax.imshow(top1_grid, vmin=0.0, vmax=1.0, aspect="auto", cmap="viridis")
        ax.set_title(f"{method}: background selected")
        ax.set_xticks(range(len(n_eval_values)))
        ax.set_xticklabels([str(v) for v in n_eval_values])
        ax.set_yticks(range(len(radii)))
        ax.set_yticklabels([str(r) for r in radii])
        ax.set_xlabel("n_eval")
        ax.set_ylabel("mask_radius")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

        ax = axes[row_idx, 1]
        im = ax.imshow(align_grid, vmin=0.0, vmax=1.0, aspect="auto", cmap="magma")
        ax.set_title(f"{method}: align with exp022 Delta")
        ax.set_xticks(range(len(n_eval_values)))
        ax.set_xticklabels([str(v) for v in n_eval_values])
        ax.set_yticks(range(len(radii)))
        ax.set_yticklabels([str(r) for r in radii])
        ax.set_xlabel("n_eval")
        ax.set_ylabel("mask_radius")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=140)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    output_dir = ROOT / (args.outdir or cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    partial_path = output_dir / "results_partial.csv"
    results_path = output_dir / "results.csv"
    runtime_path = output_dir / "runtime_sessions.csv"
    meta_path = output_dir / "meta.json"

    delta_df = pd.read_csv(ROOT / cfg["input"]["exp022_results_csv"])
    delta_reference = {
        (int(row["seed"]), int(row["mask_radius"])): {
            "delta_bg": float(row["delta_bg"]),
            "delta_fg": float(row["delta_fg"]),
            "delta_correct": bool(row["delta_correct"]),
        }
        for _, row in delta_df.iterrows()
    }

    base_cache = _load_or_build_mask_cache(cfg["data"]["root"], output_dir, cfg)
    local_cache_path = output_dir / "base_mask_cache.pt"
    if not local_cache_path.exists():
        torch.save(base_cache, local_cache_path)

    seeds = [int(seed) for seed in cfg["evaluation"]["seeds"]]
    n_eval_values = [int(v) for v in cfg["evaluation"]["n_eval_values"]]
    methods = [str(m["name"]) for m in cfg["representations"]["methods"]]
    radii = [int(r) for r in cfg["intervention"]["mask_radii"]]
    n_workers = int(cfg.get("n_workers", 1))
    tasks = [(seed, n_eval) for n_eval in n_eval_values for seed in seeds]

    existing_records: list[dict] = []
    completed = set()
    if partial_path.exists() and not args.no_resume:
        try:
            existing_df = pd.read_csv(partial_path)
            if not existing_df.empty:
                existing_records = existing_df.to_dict("records")
                completed = _completed_tasks(existing_df, methods, radii)
                print(f"[RESUME] loaded {len(existing_records)} rows from {partial_path}", flush=True)
        except Exception as e:
            print(f"[RESUME] failed to load partial results: {e}", flush=True)

    pending = [task for task in tasks if task not in completed]
    estimate_remaining = _estimate_remaining_minutes(cfg, pending, n_workers)
    session_id = f"{cfg['name']}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    started_at = _now_str()

    print(f"Experiment : {cfg['name']}", flush=True)
    print(f"Outdir     : {output_dir}", flush=True)
    print(f"Pending    : {len(pending)} / {len(tasks)} tasks", flush=True)
    print(f"Estimated remaining runtime: {estimate_remaining:.1f} minutes", flush=True)

    _update_meta(
        meta_path=meta_path,
        cfg=cfg,
        state="running",
        output_dir=output_dir,
        session_id=session_id,
        started_at=started_at,
        planned_tasks=tasks,
        completed_tasks=sorted(completed),
        n_workers=n_workers,
        estimate_minutes=estimate_remaining,
        no_resume=args.no_resume,
    )

    t0 = time.time()
    records = list(existing_records)
    all_logs: dict[tuple[int, int], list[str]] = {}

    with ProcessPoolExecutor(
        max_workers=n_workers,
        initializer=_init_worker,
        initargs=(str(local_cache_path), cfg["representations"]),
    ) as executor:
        futures = {
            executor.submit(_worker, (*task, cfg, delta_reference, str(output_dir))): task
            for task in pending
        }
        for future in as_completed(futures):
            task = futures[future]
            seed, n_eval = task
            task_records, logs = future.result()
            records.extend(task_records)
            all_logs[task] = logs
            df_partial = _save_records(records, partial_path)
            _save_seed_log(output_dir, n_eval, seed, logs)
            _update_meta(
                meta_path=meta_path,
                cfg=cfg,
                state="running",
                output_dir=output_dir,
                session_id=session_id,
                started_at=started_at,
                planned_tasks=tasks,
                completed_tasks=sorted(_completed_tasks(df_partial, methods, radii)),
                n_workers=n_workers,
                estimate_minutes=estimate_remaining,
                no_resume=args.no_resume,
            )
            print(f"[DONE] {_task_label(task)}", flush=True)

    for task in sorted(all_logs):
        for line in all_logs[task]:
            print(line, flush=True)

    final_df = _save_records(records, results_path)
    elapsed_sec = time.time() - t0
    _save_summary(final_df, cfg, output_dir, elapsed_sec=elapsed_sec)
    _plot(final_df, cfg, output_dir)

    ended_at = _now_str()
    completed_final = sorted(_completed_tasks(final_df, methods, radii))
    _update_meta(
        meta_path=meta_path,
        cfg=cfg,
        state="completed",
        output_dir=output_dir,
        session_id=session_id,
        started_at=started_at,
        planned_tasks=tasks,
        completed_tasks=completed_final,
        n_workers=n_workers,
        estimate_minutes=estimate_remaining,
        no_resume=args.no_resume,
        completed_at=ended_at,
    )
    _append_runtime_session(
        runtime_path=runtime_path,
        session_id=session_id,
        started_at=started_at,
        ended_at=ended_at,
        elapsed_sec=elapsed_sec,
        state="completed",
        completed_task_count=len(completed_final),
        planned_task_count=len(tasks),
        note="Main sweep session.",
    )

    print(f"\nResults: {output_dir}", flush=True)
    print(f"Elapsed: {elapsed_sec / 60.0:.1f} minutes", flush=True)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    main()
