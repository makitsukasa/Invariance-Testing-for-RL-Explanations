"""Waterbirds dataset loader + GrabCut-based interventions."""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms


_IMAGENET_MEAN = (0.485, 0.456, 0.406)
_IMAGENET_STD  = (0.229, 0.224, 0.225)

TRAIN_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(_IMAGENET_MEAN, _IMAGENET_STD),
])

EVAL_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(_IMAGENET_MEAN, _IMAGENET_STD),
])


def grabcut_mask(img_np: np.ndarray, n_iter: int = 3) -> np.ndarray:
    """Return binary foreground mask (1=foreground) via GrabCut.

    img_np: HxWx3 uint8 RGB
    """
    h, w = img_np.shape[:2]
    bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    mask = np.zeros((h, w), np.uint8)
    rect = (w // 8, h // 8, w * 3 // 4, h * 3 // 4)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(bgr, mask, rect, bgd_model, fgd_model, n_iter, cv2.GC_INIT_WITH_RECT)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
    return fg


def background_replace(img_np: np.ndarray, fg_mask: np.ndarray,
                        bg_pool: list[np.ndarray], rng: random.Random) -> np.ndarray:
    """Replace background pixels with a random background from bg_pool."""
    bg = rng.choice(bg_pool)
    bg_resized = cv2.resize(bg, (img_np.shape[1], img_np.shape[0]))
    out = img_np.copy()
    out[fg_mask == 0] = bg_resized[fg_mask == 0]
    return out


def foreground_noise(img_np: np.ndarray, fg_mask: np.ndarray,
                     std: float, rng: np.random.Generator) -> np.ndarray:
    """Add Gaussian noise to foreground pixels."""
    out = img_np.astype(np.float32)
    noise = rng.normal(0, std * 255, img_np.shape).astype(np.float32)
    out[fg_mask == 1] += noise[fg_mask == 1]
    out = np.clip(out, 0, 255).astype(np.uint8)
    return out


class WaterbirdsDataset(Dataset):
    """Waterbirds dataset with optional perturbation mode.

    mode:
      'normal'           : no perturbation
      'bg_replace'       : replace background with random image from bg_pool
      'fg_noise'         : add Gaussian noise to foreground
    """

    def __init__(
        self,
        root: str,
        split: str = "train",
        transform=None,
        mode: str = "normal",
        bg_pool: Optional[list[np.ndarray]] = None,
        fg_noise_std: float = 0.2,
        seed: int = 0,
        mask_cache: Optional[dict] = None,
    ):
        self.root = Path(root)
        self.transform = transform or EVAL_TRANSFORM
        self.mode = mode
        self.bg_pool = bg_pool or []
        self.fg_noise_std = fg_noise_std
        self._rng = random.Random(seed)
        self._np_rng = np.random.default_rng(seed)
        self.mask_cache = mask_cache if mask_cache is not None else {}

        meta = pd.read_csv(self.root / "metadata.csv")
        split_id = {"train": 0, "val": 1, "test": 2}[split]
        self.df = meta[meta["split"] == split_id].reset_index(drop=True)

    def __len__(self) -> int:
        return len(self.df)

    def _load_img(self, row) -> np.ndarray:
        path = self.root / row["img_filename"]
        img = Image.open(path).convert("RGB")
        return np.array(img)

    def _get_mask(self, idx: int, img_np: np.ndarray) -> np.ndarray:
        if idx not in self.mask_cache:
            self.mask_cache[idx] = grabcut_mask(img_np)
        return self.mask_cache[idx]

    def __getitem__(self, idx: int):
        row = self.df.iloc[idx]
        img_np = self._load_img(row)

        if self.mode == "bg_replace" and self.bg_pool:
            mask = self._get_mask(idx, img_np)
            img_np = background_replace(img_np, mask, self.bg_pool, self._rng)
        elif self.mode == "fg_noise":
            mask = self._get_mask(idx, img_np)
            img_np = foreground_noise(img_np, mask, self.fg_noise_std, self._np_rng)

        img_pil = Image.fromarray(img_np)
        x = self.transform(img_pil)
        y = int(row["y"])
        return x, y


def build_bg_pool(root: str, split: str = "train",
                  n_samples: int = 200, seed: int = 0) -> list[np.ndarray]:
    """Collect n_samples dataset images to use as background donors.

    We use the full image because the composited background covers most pixels.
    background_replace() applies GrabCut on the test image to isolate FG,
    then copies background pixels from these donor images.
    """
    rng = random.Random(seed)
    meta = pd.read_csv(Path(root) / "metadata.csv")
    split_id = {"train": 0, "val": 1, "test": 2}[split]
    rows = meta[meta["split"] == split_id].to_dict("records")
    rng.shuffle(rows)

    pool: list[np.ndarray] = []
    for row in rows:
        if len(pool) >= n_samples:
            break
        path = Path(root) / row["img_filename"]
        if not path.exists():
            continue
        img = Image.open(path).convert("RGB")
        pool.append(np.array(img))
    return pool
