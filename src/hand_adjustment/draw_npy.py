import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import matplotlib
from matplotlib.font_manager import FontProperties
import os

# 設置中文字體 - 方法1：使用字體名稱
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Heiti TC', 'sans-serif'] 
matplotlib.rcParams['axes.unicode_minus'] = False  # 正確顯示負號

# 讀取.npy檔案
# depth_map = np.load('hand_adjustment/ComfyUI_temp_sgucl_00002__mask.npy')
depth_map = np.load('ComfyUI_temp_sgucl_00002__mask.npy')

# 打印numpy數組的尺寸
print("深度圖尺寸:", depth_map.shape)

# 計算統計信息
# 先過濾掉零值（通常在深度圖中零表示無效或缺失數據）
valid_depths = depth_map[depth_map > 0]

# 計算各種統計量
stats = {
    "有效點數量": len(valid_depths),
    "最小值": np.min(valid_depths),
    "最大值": np.max(valid_depths),
    "平均值": np.mean(valid_depths),
    "中位數": np.median(valid_depths),
    "標準差": np.std(valid_depths),
    "第25百分位": np.percentile(valid_depths, 25),
    "第75百分位": np.percentile(valid_depths, 75),
    "總點數": depth_map.size,
    "缺失點數量": depth_map.size - len(valid_depths),
    "稀疏度": 100 * len(valid_depths) / depth_map.size
}

# 打印統計信息
print("深度圖統計信息:")
for key, value in stats.items():
    if isinstance(value, np.ndarray):
        value = float(value)  # 轉換numpy類型為Python原生類型以便更好地顯示
    
    if isinstance(value, float):
        print(f"{key}: {value:.4f}")
    else:
        print(f"{key}: {value}")

# 獲取非零深度值的坐標
y_indices, x_indices = np.nonzero(depth_map)
values = depth_map[y_indices, x_indices]

# 自動調整點的大小 - 根據圖像尺寸
height, width = depth_map.shape
# 計算適合的點大小 - 較小的圖像需要較大的點，較大的圖像需要較小的點
point_size = max(1, min(50, 5000 / max(width, height)))
print(f"自動調整點大小: {point_size}")

# 繪製深度分布的直方圖
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plt.hist(valid_depths, bins=50, color='skyblue', edgecolor='black', range=(0, 1))

# 使用沒有中文字符的標題，避免顯示方塊
plt.title('Depth Value Histogram')
plt.xlabel('Depth')
plt.ylabel('Frequency')
plt.xlim(0, 1)  # 確保x軸範圍為0到1

# 繪製散點圖
plt.subplot(1, 2, 2)

# 動態調整散點圖顯示
# 如果點數過多，可能需要採樣顯示或減小點的大小
max_points_to_display = 100000  # 設置一個合理的閾值以保持性能
if len(values) > max_points_to_display:
    # 隨機採樣顯示部分點
    idx = np.random.choice(len(values), max_points_to_display, replace=False)
    x_sample = x_indices[idx]
    y_sample = y_indices[idx]
    v_sample = values[idx]
    scatter = plt.scatter(x_sample, y_sample, c=v_sample, cmap='plasma', s=point_size)
    print(f"點數太多，顯示 {max_points_to_display} 個樣本點")
else:
    scatter = plt.scatter(x_indices, y_indices, c=values, cmap='plasma', s=point_size)

plt.colorbar(scatter, label='Depth')
plt.gca().invert_yaxis()
plt.title(f'Depth Points (Valid: {len(valid_depths)})')

# 設置坐標軸範圍以匹配深度圖尺寸
plt.xlim(0, width)
plt.ylim(height, 0)  # 注意y軸是反轉的

# 保持圖像比例，避免變形
plt.gca().set_aspect('equal')

plt.tight_layout()
plt.savefig('depth_stats_and_visualization.png', dpi=300)
plt.show()

# 額外添加：只顯示放大的散點圖
plt.figure(figsize=(12, 10))

# 再次檢查點數，適應散點圖顯示
if len(values) > max_points_to_display:
    scatter2 = plt.scatter(x_sample, y_sample, c=v_sample, cmap='plasma', s=point_size*2)  # 稍微放大點
else:
    scatter2 = plt.scatter(x_indices, y_indices, c=values, cmap='plasma', s=point_size*2)  # 稍微放大點

plt.colorbar(scatter2, label='Depth')
plt.gca().invert_yaxis()
plt.title('Enlarged Depth Points')

# 設置坐標軸範圍以匹配深度圖尺寸
plt.xlim(0, width)
plt.ylim(height, 0)  # 注意y軸是反轉的

# 保持圖像比例，避免變形
plt.gca().set_aspect('equal')

plt.savefig('depth_points_enlarged.png', dpi=300)

print("正在生成黑底無標記圖像...")

# 創建一個新的 figure
# figsize 設置得大一些以保證解析度
plt.figure(figsize=(12, 10))

# --- 修改關鍵點 1: 設置背景為黑色 ---
# 設置 Figure (整個畫布) 的背景色
plt.gcf().set_facecolor('black')
# 設置 Axes (繪圖區域) 的背景色
plt.gca().set_facecolor('black')

# 繪製散點圖 (稍微放大點的大小 *2)
if len(values) > max_points_to_display:
    scatter2 = plt.scatter(x_sample, y_sample, c=v_sample, cmap='plasma', s=point_size*2)
elif len(values) > 0:
    scatter2 = plt.scatter(x_indices, y_indices, c=values, cmap='plasma', s=point_size*2)

# --- 修改關鍵點 2: 移除所有標記 ---
# 移除 Colorbar
# plt.colorbar(scatter2, label='Depth') # 註解掉

# 移除標題
# plt.title('Enlarged Depth Points') # 註解掉

# 關閉坐標軸 (這會同時移除標線、刻度、數字標籤)
plt.axis('off')

# 雖然關閉了坐標軸，但仍需要設置正確的範圍和方向
plt.gca().invert_yaxis()
plt.xlim(0, width)
plt.ylim(height, 0)

# 保持圖像比例
plt.gca().set_aspect('equal')

# --- 修改關鍵點 3: 無邊距儲存圖像 ---
save_path = 'depth_points_enlarged_black_bg.png'
# facecolor='black': 確保存檔時背景是黑色的
# bbox_inches='tight', pad_inches=0: 去除 Matplotlib 預設的白色邊框和間距
plt.savefig(save_path, dpi=300, facecolor='black', bbox_inches='tight', pad_inches=0)
plt.close() # 關閉圖形釋放記憶體

print(f"新的黑底圖像已成功保存至: {save_path}")

# 額外添加：將深度點疊加在原始圖片上
print("正在生成疊圖（深度點 + 原圖）...")

# 嘗試讀取原始圖片（與 .npy 同名的 .png）
original_image_path = 'hand_adjustment/ComfyUI_temp_sgucl_00002_.png'
if not os.path.exists(original_image_path):
    print(f"找不到原始圖片: {original_image_path}，跳過疊圖")
else:
    original_img = np.array(Image.open(original_image_path).convert('RGB'))
    orig_h, orig_w = original_img.shape[:2]

    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    # 顯示原始圖片
    ax.imshow(original_img, extent=[0, orig_w, orig_h, 0], aspect='equal', zorder=0)

    # 疊加深度點（使用半透明散點）
    if len(values) > max_points_to_display:
        # 若先前已採樣，直接使用採樣結果
        sc = ax.scatter(x_sample, y_sample, c=v_sample, cmap='plasma',
                        s=point_size * 3.5, alpha=0.6, zorder=1)
    else:
        sc = ax.scatter(x_indices, y_indices, c=values, cmap='plasma',
                        s=point_size * 3.5, alpha=0.6, zorder=1)

    plt.colorbar(sc, ax=ax, label='Depth')

    ax.set_xlim(0, orig_w)
    ax.set_ylim(orig_h, 0)
    ax.set_aspect('equal')
    ax.set_title('Depth Points Overlay on Original Image', color='white')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_edgecolor('white')

    overlay_save_path = 'depth_points_overlay.png'
    plt.savefig(overlay_save_path, dpi=300, facecolor='black', bbox_inches='tight')
    plt.close()
    print(f"疊圖已成功保存至: {overlay_save_path}")