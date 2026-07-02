"""
Plot the whitespace mask sigmoid used in ChinesePaintingLoss.
w_white = sigmoid((I_gray - 0.85) * 20)
Output: data/white_sigmoid.png
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = ["Arial Unicode MS", "Hiragino Sans GB", "STHeiti", "DejaVu Sans"]
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(PROJECT_ROOT, "data", "white_sigmoid.png")

THRESHOLD = 0.85
SCALE     = 20


def sigmoid(x, threshold=THRESHOLD, scale=SCALE):
    return 1.0 / (1.0 + np.exp(-(x - threshold) * scale))


def main():
    x = np.linspace(0, 1, 500)
    y = sigmoid(x)

    fig, ax = plt.subplots(figsize=(3.5, 2.5))

    ax.plot(x, y, color="#C0392B", linewidth=2.5)

    ax.set_xlim(0, 1)
    ax.set_ylim(-0.05, 1.08)
    ax.axis("off")

    plt.tight_layout(pad=0.2)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    plt.savefig(OUT_PATH, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved → {OUT_PATH}")


if __name__ == "__main__":
    main()
