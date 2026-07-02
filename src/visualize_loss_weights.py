"""
Visualize intermediate maps used in ChinesePaintingLoss:
  1. I^gray        — luminance-weighted grayscale
  2. Sobel grad    — brushstroke edge magnitude
  3. Edge weight (raw)     — exp(-alpha * grad_mag), before min-clamp
  4. Edge weight (clamped) — clamp(raw, min=min_connectivity), final weight
  5. White mask    — sigmoid((I_gray - threshold) * 20)

Each map is saved as a standalone PNG to data/loss_weights/<img_name>/<name>.png
"""

import os
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F

# ── Parameters (match ChinesePaintingLoss instantiation in marigold_dc.py) ──
ALPHA_SMOOTH    = 1.0
WHITE_THRESHOLD = 0.85
MIN_CONNECTIVITY = 0.3

SOBEL_X = torch.tensor([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=torch.float32).view(1, 1, 3, 3)
SOBEL_Y = torch.tensor([[-1, -2, -1], [0,  0,  0], [1,  2,  1]], dtype=torch.float32).view(1, 1, 3, 3)


def save_float_map(arr: np.ndarray, path: str, cmap: str = "gray"):
    """arr: float [H, W] in [0, 1] → save as 8-bit PNG."""
    uint8 = (arr.clip(0, 1) * 255).astype(np.uint8)
    if cmap == "hot":
        # simple hot colormap: black → red → yellow → white
        u = uint8.astype(np.int32)
        r = np.clip(u * 3,       0, 255).astype(np.uint8)
        g = np.clip(u * 3 - 255, 0, 255).astype(np.uint8)
        b = np.clip(u * 3 - 510, 0, 255).astype(np.uint8)
        img = Image.fromarray(np.stack([r, g, b], axis=-1), mode="RGB")
    else:
        img = Image.fromarray(uint8, mode="L")
    img.save(path)


def process(image_path: str, out_root: str):
    img_name = os.path.splitext(os.path.basename(image_path))[0]
    out_dir  = os.path.join(out_root, img_name)
    os.makedirs(out_dir, exist_ok=True)

    # Load image
    img    = Image.open(image_path).convert("RGB")
    img_np = np.array(img, dtype=np.float32) / 255.0   # [H, W, 3]

    # ── 1. I^gray ──────────────────────────────────────────────────────────
    gray = 0.299 * img_np[:, :, 0] + 0.587 * img_np[:, :, 1] + 0.114 * img_np[:, :, 2]
    save_float_map(gray, os.path.join(out_dir, "1_gray.png"))

    # ── Convert to torch for convolutions ──────────────────────────────────
    t = torch.from_numpy(gray).unsqueeze(0).unsqueeze(0)   # [1, 1, H, W]

    gx = F.conv2d(t, SOBEL_X, padding=1)
    gy = F.conv2d(t, SOBEL_Y, padding=1)
    grad_mag = torch.sqrt(gx**2 + gy**2 + 1e-6)
    grad_mag = torch.clamp(grad_mag, max=2.0)

    # ── 2. Sobel gradient magnitude ────────────────────────────────────────
    grad_np = grad_mag.squeeze().numpy()
    save_float_map(grad_np / 2.0, os.path.join(out_dir, "2_sobel_grad.png"), cmap="hot")

    # ── 3. Raw edge weight  exp(-alpha * grad_mag) ─────────────────────────
    raw_weight = torch.exp(-ALPHA_SMOOTH * grad_mag).squeeze().numpy()
    save_float_map(raw_weight, os.path.join(out_dir, "3_edge_weight_raw.png"))

    # ── 4. Clamped edge weight  clamp(raw, min=min_connectivity) ──────────
    clamped_weight = np.clip(raw_weight, a_min=MIN_CONNECTIVITY, a_max=None)
    save_float_map(clamped_weight, os.path.join(out_dir, "4_edge_weight_clamped.png"))

    # ── 5. White / saliency mask ────────────────────────────────────────────
    white_mask = 1.0 / (1.0 + np.exp(-(gray - WHITE_THRESHOLD) * 20))
    save_float_map(white_mask, os.path.join(out_dir, "5_white_mask.png"))

    # ── 6. White loss  M^white * D_pred^2 ───────────────────────────────────
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    depth_path   = os.path.join(project_root, "data", "DA2", img_name + ".png")
    if os.path.exists(depth_path):
        dep     = Image.open(depth_path).convert("L").resize(img.size, Image.BILINEAR)
        dep_np  = np.array(dep, dtype=np.float32) / 255.0
        white_loss = white_mask * dep_np ** 2
        save_float_map(white_loss / (white_loss.max() + 1e-8),
                       os.path.join(out_dir, "6_white_loss.png"), cmap="hot")
        print(f"[{img_name}] saved 6 maps → {out_dir}")
    else:
        print(f"[{img_name}] saved 5 maps → {out_dir} (no depth map found for map 6)")


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir    = os.path.join(project_root, "data", "input")
    out_root     = os.path.join(project_root, "data", "loss_weights")

    if not os.path.isdir(input_dir):
        print(f"Input directory not found: {input_dir}")
        raise SystemExit(1)

    images = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    if not images:
        print(f"No images found in {input_dir}")
    else:
        for path in sorted(images):
            process(path, out_root)
