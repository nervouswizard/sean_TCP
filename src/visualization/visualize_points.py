import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import sys
import os

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


def load_points(json_path: str):
    """
    支援兩種 JSON 格式：
      格式 A（含深度值）: [{"position": [x, y], "value": v}, ...]
      格式 B（純座標）  : [[x, y], ...]
    回傳 list of (x, y, value_or_None)
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    if not raw:
        return []

    first = raw[0]
    # 格式 A
    if isinstance(first, dict) and 'position' in first:
        return [(entry['position'][0], entry['position'][1], entry.get('value')) for entry in raw]
    # 格式 B
    if isinstance(first, (list, tuple)) and len(first) == 2:
        return [(pt[0], pt[1], None) for pt in raw]

    raise ValueError(f"無法識別的 JSON 格式：{json_path}")


def visualize_points(image_path: str, json_path: str):
    """讀取 JSON 儲存的點，標記回原圖並顯示。"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"找不到圖片：{image_path}")
    image = np.array(Image.open(image_path))

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"找不到 JSON 檔：{json_path}")

    points = load_points(json_path)
    if not points:
        print("JSON 檔內沒有任何點資料。")
        return

    has_value = any(v is not None for _, _, v in points)

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.imshow(image)
    ax.set_title(f'標記點視覺化  |  共 {len(points)} 個點', fontsize=14)
    ax.axis('off')

    for i, (x, y, value) in enumerate(points):
        # 有深度值時用色彩對應，否則固定橘紅色
        if has_value and value is not None:
            color = plt.cm.RdYlBu_r(value)
            label = f'點{i+1}  ({x}, {y})\n深度: {value:.4f}'
        else:
            color = (1.0, 0.35, 0.15, 0.9)
            label = f'點{i+1}  ({x}, {y})'

        # 畫圓圈
        circle = patches.Circle(
            (x, y), radius=8,
            linewidth=2,
            edgecolor='white',
            facecolor=color,
            alpha=0.9,
            zorder=3
        )
        ax.add_patch(circle)

        # 點編號
        ax.text(
            x, y, str(i + 1),
            color='white', fontsize=7, fontweight='bold',
            ha='center', va='center', zorder=4
        )

        # 標籤
        ax.text(
            x + 12, y - 12, label,
            color='white', fontsize=8,
            bbox=dict(facecolor=color, alpha=0.75, boxstyle='round,pad=0.3'),
            zorder=4
        )

    # 只有含深度值時才顯示色條
    if has_value:
        sm = plt.cm.ScalarMappable(cmap='RdYlBu_r', norm=plt.Normalize(0, 1))
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.02)
        cbar.set_label('深度值', fontsize=11)

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    # 預設路徑（與 point_selector.py 相同資料夾）
    base_dir = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) == 3:
        img_path = sys.argv[1]
        json_path = sys.argv[2]
    else:
        img_path  = os.path.join(base_dir, 'ComfyUI_temp_sgucl_00002_.png')
        json_path = os.path.join(base_dir, 'human_points.json')

    visualize_points(img_path, json_path)
