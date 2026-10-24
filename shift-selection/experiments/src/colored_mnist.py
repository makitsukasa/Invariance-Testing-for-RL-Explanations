import numpy as np
import torch
from torch.utils.data import Dataset
import torchvision


class ColoredMNIST(Dataset):
    """Binary ColoredMNIST.

    Digits 0-4 → class 0 (red), digits 5-9 → class 1 (green).
    spurious_p: probability that color does NOT match class label.
      0.0 = perfect correlation (color is fully spurious)
      0.5 = random (no correlation)
      1.0 = perfect anti-correlation
    """

    COLORS = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])  # red, green

    def __init__(self, root, train=True, spurious_p=0.0, label_noise_p=0.0, seed=42):
        rng = np.random.default_rng(seed)
        mnist = torchvision.datasets.MNIST(root=root, train=train, download=True)

        images = mnist.data.numpy().astype(np.float32) / 255.0  # (N, 28, 28)
        labels = (mnist.targets.numpy() >= 5).astype(int)       # binary, ground truth

        # Apply label noise: flip labels with label_noise_p before color assignment.
        # This makes structure predict noisy_labels at (1 - label_noise_p) accuracy,
        # so color can become a better shortcut when spurious_p < label_noise_p.
        noisy_labels = labels.copy()
        if label_noise_p > 0.0:
            flip_labels = rng.random(len(labels)) < label_noise_p
            noisy_labels[flip_labels] = 1 - noisy_labels[flip_labels]

        # Color is assigned based on noisy labels, then flipped with spurious_p
        color_class = noisy_labels.copy()
        flip_color = rng.random(len(noisy_labels)) < spurious_p
        color_class[flip_color] = 1 - color_class[flip_color]

        self.images = self._colorize(images, color_class)  # (N, 3, 28, 28)
        self.labels = torch.tensor(noisy_labels, dtype=torch.long)  # train/eval target

    def _colorize(self, images, color_class):
        gray = torch.tensor(images).unsqueeze(1)            # (N, 1, 28, 28)
        c = self.COLORS[color_class].reshape(-1, 3, 1, 1)  # (N, 3, 1, 1)
        return gray * c                                     # (N, 3, 28, 28)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.images[idx], self.labels[idx]


def hue_shuffle(images, seed=None):
    """Replace each image's color with a randomly chosen red or green."""
    gen = torch.Generator()
    if seed is not None:
        gen.manual_seed(seed)
    N = images.shape[0]
    lum = images.max(dim=1, keepdim=True).values          # (N, 1, 28, 28)
    rand_class = torch.randint(0, 2, (N,), generator=gen)
    c = ColoredMNIST.COLORS[rand_class].reshape(-1, 3, 1, 1)
    return lum * c


def structure_noise(images, std=0.3, seed=None):
    """Add Gaussian noise to all channels."""
    gen = torch.Generator()
    if seed is not None:
        gen.manual_seed(seed)
    noise = torch.randn(images.shape, generator=gen) * std
    return torch.clamp(images + noise, 0.0, 1.0)
