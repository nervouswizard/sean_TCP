# Sean TCP — 大專案管理 Repo

這個 repo 作為總管理層，使用 Git Submodules 統一管理各子專案。

## 目錄結構

```
.
├── projects/                  # 各子專案 (git submodules)
│   ├── Uni3C/                 # https://github.com/nervouswizard/Uni3C
│   └── Marigold-DC/           # https://github.com/nervouswizard/Marigold-DC
├── src/
│   └── hand_adjustment/       # 深度圖手動調整工具組
│       ├── draw_npy.py        # 深度圖統計與視覺化
│       ├── point_selector.py  # 互動式點選與深度值標注工具
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

### `src/hand_adjustment/` — 深度圖手動調整工具組

深度估測模型在手部區域常有偏差，此工具組用於手動修正深度圖。

| 腳本 | 功能 |
|------|------|
| `draw_npy.py` | 載入 `.npy` 深度圖，輸出統計資訊（有效點數、最大/最小/平均/中位數/標準差），並生成直方圖、散點圖、黑底版本與疊加原圖等四張視覺化 PNG |
| `point_selector.py` | 互動式 GUI：在原始影像上點擊選取控制點，透過滑桿為每個點指定深度值 (0–1)，支援儲存/復原/清除，輸出 `.json`（座標＋數值）與 `.npy` 遮罩 |
| `visualize_points.py` | 讀取 `point_selector.py` 輸出的 JSON，將控制點以色彩標記疊回原圖，支援兩種 JSON 格式（含/不含深度值） |

**典型工作流程：**
```
原始影像
  → point_selector.py   # 手動點選控制點並賦予深度值 → *_points.json + *_mask.npy
  → visualize_points.py # 確認點位標注是否正確
  → draw_npy.py         # 確認最終深度圖分佈與統計
```

---

## 子專案列表

| 名稱 | 路徑 | 來源 |
|------|------|------|
| Uni3C | `projects/Uni3C` | https://github.com/nervouswizard/Uni3C |
| Marigold-DC | `projects/Marigold-DC` | https://github.com/nervouswizard/Marigold-DC |
