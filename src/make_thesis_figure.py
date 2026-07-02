"""
Generate a thesis-ready composite figure for L_brush visualization.

Layout: 4 crops in a row with arrows and math labels underneath.
Output: data/brush_loss/lotus2/thesis_figure.png
"""

import os
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = ["Arial Unicode MS", "Hiragino Sans GB", "STHeiti", "DejaVu Sans"]
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FRAG_DIR = os.path.join(PROJECT_ROOT, "data", "brush_loss", "lotus2", "frag")
OUT_PATH  = os.path.join(PROJECT_ROOT, "data", "brush_loss", "lotus2", "thesis_figure.png")

PANELS = [
    ("0_original.png",      "原圖 (RGB)",   r"$I^{\mathrm{rgb}}$"),
    ("1_edge_weight.png",   "邊緣權重",      r"$w_{i,j}$"),
    ("2_depth_grad.png",    "深度梯度",      r"$\|\nabla D\|_1$"),
    ("3_loss_heatmap.png",  "損失貢獻",      r"$w \cdot \|\nabla D\|_1$"),
]

UPSCALE = 4


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    fig, axes = plt.subplots(1, 4, figsize=(11, 3.2),
                             gridspec_kw={"wspace": 0.12})

    for ax, (fname, zh_label, math_label) in zip(axes, PANELS):
        img = Image.open(os.path.join(FRAG_DIR, fname)).convert("RGB")
        w, h = img.size
        img = img.resize((w * UPSCALE, h * UPSCALE), Image.NEAREST)
        ax.imshow(np.array(img))
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xlabel(f"{zh_label}\n{math_label}", fontsize=10, labelpad=6)

    # ── Draw arrows after layout is finalized ─────────────────────────────────
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    for i in range(3):
        bb_left  = axes[i].get_window_extent(renderer)
        bb_right = axes[i + 1].get_window_extent(renderer)
        fig.patches.append(
            FancyArrowPatch(
                posA=fig.transFigure.inverted().transform((bb_left.x1  + 4, bb_left.y0  + bb_left.height / 2)),
                posB=fig.transFigure.inverted().transform((bb_right.x0 - 4, bb_right.y0 + bb_right.height / 2)),
                transform=fig.transFigure,
                arrowstyle="->",
                color="#555555",
                linewidth=1.5,
                mutation_scale=14,
            )
        )

    plt.suptitle(
        r"筆觸感知平滑損失 $\mathcal{L}_{\mathrm{brush}}$ — 各中間量可視化（青蛙局部）",
        fontsize=11, y=1.01
    )

    plt.savefig(OUT_PATH, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved → {OUT_PATH}")


if __name__ == "__main__":
    main()
