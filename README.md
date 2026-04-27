# Sean TCP — 大專案管理 Repo

這個 repo 作為總管理層，使用 Git Submodules 統一管理各子專案。

## 目錄結構

```
.
├── projects/          # 各子專案 (git submodules)
│   └── Uni3C/         # https://github.com/nervouswizard/Uni3C
├── comfyui/
│   └── workflows/     # ComfyUI workflow (.json)
├── docs/              # 跨專案文件
└── scripts/           # 自動化腳本
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

## 子專案列表

| 名稱 | 路徑 | 來源 |
|------|------|------|
| Uni3C | `projects/Uni3C` | https://github.com/nervouswizard/Uni3C |
