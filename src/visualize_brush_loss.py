"""
Visualize the brushstroke smoothness loss L_brush for a given image.

NOTE: CROP_BOX and CROSS_ROW are tuned for lotus2.png (frog region).
      Adjust them before running on other images.

Outputs (saved to data/brush_loss/<img_name>/):
  frag/0_original.png      — original RGB crop
  frag/1_edge_weight.png   — w_{i,j} = clamp(exp(-alpha*|grad I_gray|), min=min_conn)
  frag/2_depth_grad.png    — ||grad D_pred||_1 = |dx D| + |dy D|  (hot colormap)
  frag/3_loss_heatmap.png  — w * ||grad D||_1  (hot colormap)
  crosssection.png         — 1-D signals along CROSS_ROW
"""

import os
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Parameters (match ChinesePaintingLoss in marigold_dc.py) ──────────────────
ALPHA_SMOOTH     = 1.0
MIN_CONNECTIVITY = 0.3

# ── Frog crop: PIL (left, top, right, bottom) ─────────────────────────────────
CROP_BOX = (120, 368, 205, 424)

# ── Cross-section row (in original image y-coordinate) ────────────────────────
CROSS_ROW = 395

# ── Sobel kernels ─────────────────────────────────────────────────────────────
SOBEL_X = torch.tensor([[-1,0,1],[-2,0,2],[-1,0,1]], dtype=torch.float32).view(1,1,3,3)
SOBEL_Y = torch.tensor([[-1,-2,-1],[0,0,0],[1,2,1]], dtype=torch.float32).view(1,1,3,3)


def sobel_grad_mag(gray_np: np.ndarray) -> np.ndarray:
    t  = torch.from_numpy(gray_np).unsqueeze(0).unsqueeze(0)
    gx = F.conv2d(t, SOBEL_X, padding=1)
    gy = F.conv2d(t, SOBEL_Y, padding=1)
    return torch.sqrt(gx**2 + gy**2 + 1e-6).clamp(max=2.0).squeeze().numpy()


def edge_weight(grad_mag: np.ndarray) -> np.ndarray:
    return np.clip(np.exp(-ALPHA_SMOOTH * grad_mag), a_min=MIN_CONNECTIVITY, a_max=None)


def depth_grad_l1(depth_np: np.ndarray) -> np.ndarray:
    t  = torch.from_numpy(depth_np).unsqueeze(0).unsqueeze(0)
    gx = F.conv2d(t, SOBEL_X, padding=1)
    gy = F.conv2d(t, SOBEL_Y, padding=1)
    return (gx.abs() + gy.abs()).squeeze().numpy()


def save_gray(arr: np.ndarray, path: str):
    Image.fromarray((arr.clip(0, 1) * 255).astype(np.uint8), mode="L").save(path)


def save_hot(arr: np.ndarray, path: str):
    """Hot colormap (black→red→yellow→white). Outputs black if arr is uniform."""
    mn, mx = arr.min(), arr.max()
    n = (arr - mn) / (mx - mn + 1e-8)
    u = (n * 255).astype(np.int32)
    r = np.clip(u * 3,       0, 255).astype(np.uint8)
    g = np.clip(u * 3 - 255, 0, 255).astype(np.uint8)
    b = np.clip(u * 3 - 510, 0, 255).astype(np.uint8)
    Image.fromarray(np.stack([r, g, b], axis=-1), mode="RGB").save(path)


def main(img_path: str, depth_path: str):
    img_name = os.path.splitext(os.path.basename(img_path))[0]
    out_dir  = os.path.join(PROJECT_ROOT, "data", "brush_loss", img_name)
    frag_dir = os.path.join(out_dir, "frag")
    os.makedirs(frag_dir, exist_ok=True)

    # ── Load ──────────────────────────────────────────────────────────────────
    rgb  = Image.open(img_path).convert("RGB")
    dep  = Image.open(depth_path).convert("L").resize(rgb.size, Image.BILINEAR)

    H, W = rgb.size[1], rgb.size[0]
    rgb_np   = np.array(rgb, dtype=np.float32) / 255.0
    depth_np = np.array(dep, dtype=np.float32) / 255.0
    gray_np  = 0.299*rgb_np[:,:,0] + 0.587*rgb_np[:,:,1] + 0.114*rgb_np[:,:,2]

    # ── Bounds check ──────────────────────────────────────────────────────────
    l, t, r, b = CROP_BOX
    assert 0 <= l < r <= W and 0 <= t < b <= H, \
        f"CROP_BOX {CROP_BOX} out of bounds for image size ({W}, {H})"
    assert 0 <= CROSS_ROW < H, \
        f"CROSS_ROW {CROSS_ROW} out of bounds for image height {H}"

    # ── Compute maps ──────────────────────────────────────────────────────────
    img_grad = sobel_grad_mag(gray_np)
    w        = edge_weight(img_grad)
    dgrad    = depth_grad_l1(depth_np)
    loss_map = w * dgrad

    # ── Save crops ────────────────────────────────────────────────────────────
    Image.fromarray((rgb_np[t:b, l:r] * 255).astype(np.uint8), mode="RGB") \
         .save(os.path.join(frag_dir, "0_original.png"))
    save_gray(w[t:b, l:r],        os.path.join(frag_dir, "1_edge_weight.png"))
    save_hot( dgrad[t:b, l:r],    os.path.join(frag_dir, "2_depth_grad.png"))
    save_hot( loss_map[t:b, l:r], os.path.join(frag_dir, "3_loss_heatmap.png"))
    print(f"Saved 4 crop images → {frag_dir}")

    # ── Cross-section plot ────────────────────────────────────────────────────
    row = CROSS_ROW
    xs  = np.arange(l, r)

    fig, axes = plt.subplots(4, 1, figsize=(7, 6), sharex=True)
    signals = [
        (gray_np[row, l:r],   r"$I^{\mathrm{gray}}$",       "black"),
        (w[row, l:r],         r"$w_{i,j}$",                  "steelblue"),
        (dgrad[row, l:r],     r"$\|\nabla D\|_1$",           "darkorange"),
        (loss_map[row, l:r],  r"$w \cdot \|\nabla D\|_1$",   "crimson"),
    ]
    for ax, (sig, label, color) in zip(axes, signals):
        ax.plot(xs, sig, color=color, linewidth=1.2)
        ax.set_ylabel(label, fontsize=8)
        ax.grid(True, linewidth=0.4, alpha=0.5)
        ax.tick_params(labelsize=7)
    axes[-1].set_xlabel("pixel x", fontsize=8)
    plt.tight_layout()

    cross_path = os.path.join(out_dir, "crosssection.png")
    plt.savefig(cross_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved cross-section → {cross_path}")


if __name__ == "__main__":
    img_path   = os.path.join(PROJECT_ROOT, "data", "input", "lotus2.png")
    depth_path = os.path.join(PROJECT_ROOT, "data", "DA2",   "lotus2.png")
    main(img_path, depth_path)
