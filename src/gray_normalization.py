"""
Save the normalized grayscale image I^gray used in ChinesePaintingLoss.
Formula: I^gray = 0.299*R + 0.587*G + 0.114*B  (values in [0, 1])
"""

import os
import numpy as np
from PIL import Image


def to_gray(img_np: np.ndarray) -> np.ndarray:
    """img_np: float32 [H, W, 3] in [0, 1] → gray [H, W] in [0, 1]"""
    return 0.299 * img_np[:, :, 0] + 0.587 * img_np[:, :, 1] + 0.114 * img_np[:, :, 2]


def main(image_path: str):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    img = Image.open(image_path).convert("RGB")
    img_np = np.array(img, dtype=np.float32) / 255.0

    gray_uint8 = (to_gray(img_np) * 255).clip(0, 255).astype(np.uint8)

    img_name = os.path.splitext(os.path.basename(image_path))[0]
    out_dir = os.path.join(project_root, 'data', 'gray_normalization')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{img_name}.png")

    Image.fromarray(gray_uint8, mode='L').save(out_path)
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    image_path = os.path.join(project_root, 'data', 'input', 'lotus2.png')
    main(image_path)
