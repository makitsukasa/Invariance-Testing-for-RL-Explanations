"""Representation backends for candidate discovery experiments.

The loaders are intentionally lazy so the module can be imported even when
optional dependencies such as `transformers` are not installed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from PIL import Image
from torchvision import models, transforms


@dataclass
class RepresentationBackend:
    name: str

    def encode(self, images: list[np.ndarray], batch_size: int = 32) -> np.ndarray:
        raise NotImplementedError


class TorchvisionResNet18Backend(RepresentationBackend):
    def __init__(self, name: str = "resnet18_imagenet") -> None:
        super().__init__(name=name)
        weights = models.ResNet18_Weights.IMAGENET1K_V1
        self.model = models.resnet18(weights=weights)
        self.model.fc = torch.nn.Identity()
        self.model.eval()
        self.transform = weights.transforms()

    def encode(self, images: list[np.ndarray], batch_size: int = 32) -> np.ndarray:
        batches: list[np.ndarray] = []
        for start in range(0, len(images), batch_size):
            chunk = images[start:start + batch_size]
            tensor = torch.stack([self.transform(Image.fromarray(img)) for img in chunk], dim=0)
            with torch.no_grad():
                emb = self.model(tensor).cpu().numpy()
            batches.append(emb)
        return np.concatenate(batches, axis=0)


class TransformersClipBackend(RepresentationBackend):
    def __init__(
        self,
        model_name_or_path: str,
        local_files_only: bool = True,
        name: str = "clip",
        cache_dir: str | None = None,
    ) -> None:
        super().__init__(name=name)
        try:
            from transformers import CLIPImageProcessor, CLIPModel
        except Exception as exc:  # pragma: no cover - depends on local optional deps
            raise RuntimeError("transformers is required for the CLIP backend") from exc
        self.processor = CLIPImageProcessor.from_pretrained(
            model_name_or_path, local_files_only=local_files_only, cache_dir=cache_dir
        )
        self.model = CLIPModel.from_pretrained(
            model_name_or_path, local_files_only=local_files_only, cache_dir=cache_dir
        )
        self.model.eval()

    def encode(self, images: list[np.ndarray], batch_size: int = 32) -> np.ndarray:
        batches: list[np.ndarray] = []
        for start in range(0, len(images), batch_size):
            chunk = [Image.fromarray(img) for img in images[start:start + batch_size]]
            inputs = self.processor(images=chunk, return_tensors="pt")
            with torch.no_grad():
                emb_t = self.model.get_image_features(pixel_values=inputs["pixel_values"])
                if not isinstance(emb_t, torch.Tensor) and hasattr(emb_t, "last_hidden_state"):
                    emb_t = emb_t.last_hidden_state[:, 0, :]
                emb = emb_t.cpu().numpy()
            batches.append(emb)
        return np.concatenate(batches, axis=0)


class TransformersAutoImageBackend(RepresentationBackend):
    def __init__(
        self,
        model_name_or_path: str,
        local_files_only: bool = True,
        pooling: str = "cls",
        name: str = "ssl",
        cache_dir: str | None = None,
    ) -> None:
        super().__init__(name=name)
        try:
            from transformers import AutoImageProcessor, AutoModel
        except Exception as exc:  # pragma: no cover - depends on local optional deps
            raise RuntimeError("transformers is required for the SSL backend") from exc
        self.processor = AutoImageProcessor.from_pretrained(
            model_name_or_path, local_files_only=local_files_only, cache_dir=cache_dir
        )
        self.model = AutoModel.from_pretrained(
            model_name_or_path, local_files_only=local_files_only, cache_dir=cache_dir
        )
        self.model.eval()
        self.pooling = pooling

    def encode(self, images: list[np.ndarray], batch_size: int = 32) -> np.ndarray:
        batches: list[np.ndarray] = []
        for start in range(0, len(images), batch_size):
            chunk = [Image.fromarray(img) for img in images[start:start + batch_size]]
            inputs = self.processor(images=chunk, return_tensors="pt")
            with torch.no_grad():
                outputs = self.model(**inputs)
            if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                emb = outputs.pooler_output.cpu().numpy()
            else:
                hidden = outputs.last_hidden_state
                if self.pooling == "mean":
                    emb = hidden.mean(dim=1).cpu().numpy()
                else:
                    emb = hidden[:, 0, :].cpu().numpy()
            batches.append(emb)
        return np.concatenate(batches, axis=0)


def build_backend(spec: dict[str, Any]) -> RepresentationBackend:
    backend_type = str(spec["backend_type"])
    if backend_type == "torchvision_resnet18":
        return TorchvisionResNet18Backend(name=spec.get("name", "resnet18_imagenet"))
    if backend_type == "transformers_clip":
        return TransformersClipBackend(
            model_name_or_path=str(spec["model_name_or_path"]),
            local_files_only=bool(spec.get("local_files_only", True)),
            name=spec.get("name", "clip"),
            cache_dir=spec.get("cache_dir"),
        )
    if backend_type == "transformers_auto_image":
        return TransformersAutoImageBackend(
            model_name_or_path=str(spec["model_name_or_path"]),
            local_files_only=bool(spec.get("local_files_only", True)),
            pooling=str(spec.get("pooling", "cls")),
            name=spec.get("name", "ssl"),
            cache_dir=spec.get("cache_dir"),
        )
    raise ValueError(f"Unknown backend_type: {backend_type}")


def cosine_distance(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    a = a / np.clip(np.linalg.norm(a, axis=1, keepdims=True), 1e-8, None)
    b = b / np.clip(np.linalg.norm(b, axis=1, keepdims=True), 1e-8, None)
    return 1.0 - np.sum(a * b, axis=1)
