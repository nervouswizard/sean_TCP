# Sean TCP — 大專案管理 Repo

這個 repo 作為總管理層，使用 Git Submodules 統一管理各子專案。

---

## 國畫 → 2.5D 影片完整流程

本專案將單張國畫圖片轉換為具有景深感的 2.5D 動態影片，流程分為五個階段。

```
單張國畫圖片
     │
     ▼
【階段零】初始深度估算（觀察用）
  projects/Marigold-DC（不帶稀疏引導，純單目深度估算）
     │  輸出: initial_depth.npy + 視覺化深度圖
     │
     ▼  ← 人工觀察：哪些區域的深度判斷是錯誤的？
     │     例如：國畫留白被誤判為前景、墨色濃淡與遠近不符等
     │
     ▼
【階段一】手動標注稀疏深度控制點
  src/depth_hints/point_selector.py
     │  輸出: *_points.json + *_mask.npy（稀疏深度遮罩）
     │
     ▼
【階段二】稀疏深度 → 稠密深度圖
  projects/Marigold-DC（帶稀疏引導，測試時擴散引導）
     │  輸出: dense_depth.npy（全圖每像素皆有深度值）
     │
     ▼
【階段三】深度圖 → 3D 點雲
  comfyui/workflows/Cloud point gen Workflow.json
  （使用 Depth Anything V3）
     │  輸出: pointcloud（RGB 著色 3D 點雲）
     │
     ▼
【階段四】點雲 + 攝影機軌跡 → 2.5D 影片
  projects/Uni3C（PCDController）
     │  輸出: result.mp4
     ▼
完成！2.5D 動態影片
```

### 階段零：初始深度估算（觀察用）

在手動標注之前，先以**無引導**模式跑一次 Marigold，取得初始深度圖：

```bash
python -m marigold_dc --in-image painting.png --out-depth initial_depth.npy
```

用 `src/visualization/draw_npy.py` 視覺化輸出，觀察哪些區域深度有誤（例如國畫留白、皴法筆觸、墨色濃淡造成的誤判），作為下一步標注的依據。

### 階段一：手動標注稀疏深度控制點

根據階段零觀察到的錯誤，使用互動式 GUI 在問題區域點選控制點並指定正確深度值：

```bash
python src/depth_hints/point_selector.py
```

- 在圖片上點擊選取控制點（最多 20 個顯示於右側面板）
- 透過滑桿設定每個點的深度值（0 = 最近，1 = 最遠）
- 按「儲存」輸出 `*_points.json`（座標＋深度值）與 `*_mask.npy`（稀疏遮罩）
- 用 `src/visualization/visualize_points.py` 確認標注位置正確

### 階段二：稀疏深度 → 稠密深度圖（Marigold-DC）

Marigold-DC（ICCV 2025）在去噪擴散的推論過程中以控制點為條件，將稀疏遮罩補全為稠密深度圖：

```bash
python -m marigold_dc \
    --in-image painting.png \
    --in-depth painting_mask.npy \
    --out-depth dense_depth.npy
```

用 `src/visualization/draw_npy.py` 驗證輸出深度圖的分布與統計是否符合預期。

### 階段三：深度圖 → 3D 點雲（ComfyUI + Depth Anything V3）

開啟 ComfyUI 並載入 `comfyui/workflows/Cloud point gen Workflow.json`。

工作流程節點鏈：
```
LoadImage（原始國畫）
    └→ DepthAnything_V3  →  depth / confidence / intrinsics
            └→ DA3_ToPointCloud（反投影為 3D 點雲，以原圖 RGB 著色）
                    └→ DA3_SavePointCloud  →  pointcloud 檔案
                            └→ DA3_PreviewPointCloud（預覽）
```

### 階段四：點雲 + 攝影機軌跡 → 2.5D 影片（Uni3C）

Uni3C（SIGGRAPH Asia 2025）的 PCDController 以點雲為 3D 空間條件驅動視訊擴散模型。

**Step 1：渲染攝影機軌跡參考幀**

```bash
python cam_render.py \
    --reference_image painting.png \
    --output_path outputs/result \
    --traj_type "orbit"   # orbit / swing / custom / free1~5
```

可調攝影機參數：`d_r`（距離）、`d_theta`（仰俯角）、`d_phi`（水平旋轉）、`x/y/z_offset`（平移）、`focal_length`（焦距）。

**Step 2：生成最終影片**

```bash
python cam_control.py \
    --reference_image painting.png \
    --render_path outputs/result \
    --output_path outputs/result/final.mp4 \
    --prompt "A serene Chinese ink painting landscape with misty mountains..."
```

PCDController 將點雲渲染的參考幀注入視訊擴散模型，填補視角切換時的遮擋空洞並維持國畫風格一致性，輸出流暢的 2.5D 影片。

---

## 目錄結構

```
.
├── projects/                  # 各子專案 (git submodules)
│   ├── Uni3C/                 # https://github.com/nervouswizard/Uni3C
│   └── Marigold-DC/           # https://github.com/nervouswizard/Marigold-DC
├── src/
│   ├── depth_hints/           # 產生 Marigold-DC 稀疏深度參考輸入
│   │   └── point_selector.py  # 互動式點選與深度值標注工具
│   └── visualization/         # 輸入與輸出結果確認工具
│       ├── draw_npy.py        # 深度圖統計與視覺化
│       └── visualize_points.py# 已儲存點位的視覺化
├── comfyui/
│   └── workflows/             # ComfyUI workflow (.json)
├── docs/                      # 跨專案文件
└── scripts/                   # 自動化腳本
```

## 初始化

首次 clone 後，執行以下指令以拉取所有子專案：

```bash
git clone --recurse-submodules <this-repo-url>
# 或已 clone 後：
git submodule update --init --recursive
```

## 更新子專案

```bash
# 更新全部子專案到最新 commit
git submodule update --remote --merge

# 更新單一子專案
git submodule update --remote projects/Uni3C
```

## 工具說明

### `src/depth_hints/` — Marigold-DC 稀疏深度參考輸入

手動指定影像中特定位置的深度值，產生稀疏深度 hint，作為 Marigold-DC 的深度條件輸入。

| 腳本 | 功能 |
|------|------|
| `point_selector.py` | 互動式 GUI：在原始影像上點擊選取控制點，透過滑桿為每個點指定深度值 (0–1)，支援儲存/復原/清除，輸出 `.json`（座標＋數值）與 `.npy` 稀疏深度遮罩 |

### `src/visualization/` — 結果確認工具

| 腳本 | 功能 |
|------|------|
| `visualize_points.py` | 讀取 `point_selector.py` 輸出的 JSON，將控制點以色彩標記疊回原圖，支援兩種 JSON 格式（含/不含深度值） |
| `draw_npy.py` | 載入 `.npy` 深度圖，輸出統計資訊（有效點數、最大/最小/平均/中位數/標準差），並生成直方圖、散點圖、黑底版本與疊加原圖等四張視覺化 PNG |

**典型工作流程：**
```
原始影像
  → (Marigold-DC 初始推論)              # 無引導，觀察深度分布
  → visualization/draw_npy.py           # 確認初始深度圖，找出誤判區域
  → depth_hints/point_selector.py       # 手動指定稀疏深度參考點 → *_points.json + *_mask.npy
  → visualization/visualize_points.py  # 確認點位標注是否正確
  → (Marigold-DC 引導推論)              # 帶稀疏 hint 重新推論
  → visualization/draw_npy.py           # 確認輸出深度圖分佈與統計
```

---

## 子專案列表

| 名稱 | 路徑 | 來源 |
|------|------|------|
| Uni3C | `projects/Uni3C` | https://github.com/nervouswizard/Uni3C |
| Marigold-DC | `projects/Marigold-DC` | https://github.com/nervouswizard/Marigold-DC |
