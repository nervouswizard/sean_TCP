#!/usr/bin/env python
"""
Standalone Point Cloud / Gaussian PLY previewer.

Reproduces the "DA3 Preview Point Cloud / Gaussians" ComfyUI node
(nodes/preview_nodes.py) as a plain script, so you can view a .ply file
without running ComfyUI.

The DA3 nodes save ASCII PLY files with:
  - point cloud : x y z [red green blue] [confidence] [view_id]
  - gaussians   : x y z scale_0..2 rot_0..3 red green blue opacity
Both store per-point RGB, so the same viewer works for either one.

Usage
-----
    python preview_pointcloud.py path/to/cloud.ply
    python preview_pointcloud.py cloud.ply --color-mode view_id
    python preview_pointcloud.py cloud.ply --point-size 3 --backend matplotlib

Run it with the ComfyUI conda env python (it already has the deps):
    D:/anaconda3/envs/comfyui/python.exe preview_pointcloud.py cloud.ply

Dependencies: numpy (required), and one of open3d (preferred) or matplotlib
for display. plyfile is used if available (handles binary PLY + custom
properties); otherwise a built-in ASCII reader is used as a fallback.
"""

import argparse
import sys

import numpy as np


# 8-colour palette matching DA3_PreviewPointCloud._color_by_view_id
VIEW_ID_PALETTE = np.array([
    [1.0, 0.0, 0.0],   # view 0 - red
    [0.0, 0.0, 1.0],   # view 1 - blue
    [0.0, 1.0, 0.0],   # view 2 - green
    [1.0, 1.0, 0.0],   # view 3 - yellow
    [1.0, 0.0, 1.0],   # view 4 - magenta
    [0.0, 1.0, 1.0],   # view 5 - cyan
    [1.0, 0.5, 0.0],   # view 6 - orange
    [0.5, 0.0, 1.0],   # view 7 - purple
], dtype=np.float32)


# --------------------------------------------------------------------------- #
# PLY reading
# --------------------------------------------------------------------------- #
def read_ply(path):
    """Return (points[N,3] float32, colors[N,3] 0..1 or None,
               confidence[N] or None, view_id[N] int or None)."""
    try:
        return _read_ply_plyfile(path)
    except ImportError:
        print("[info] plyfile not installed, falling back to ASCII reader")
        return _read_ply_ascii(path)


def _read_ply_plyfile(path):
    from plyfile import PlyData  # raises ImportError if missing

    ply = PlyData.read(path)
    v = ply["vertex"].data
    names = v.dtype.names

    points = np.stack([v["x"], v["y"], v["z"]], axis=-1).astype(np.float32)

    colors = None
    if {"red", "green", "blue"}.issubset(names):
        colors = np.stack([v["red"], v["green"], v["blue"]], axis=-1).astype(np.float32) / 255.0

    confidence = v["confidence"].astype(np.float32) if "confidence" in names else None
    view_id = v["view_id"].astype(np.int32) if "view_id" in names else None

    return points, colors, confidence, view_id


def _read_ply_ascii(path):
    """Minimal ASCII PLY reader (mirrors the DA3 node), supports the
    optional confidence / view_id properties written by DA3."""
    points, colors, confidence_vals, view_ids = [], [], [], []
    has_color = has_confidence = has_view_id = False
    num_vertices = 0

    with open(path, "r") as f:
        if f.readline().strip() != "ply":
            raise ValueError("Not a valid PLY file")
        while True:
            line = f.readline().strip()
            if line.startswith("element vertex"):
                num_vertices = int(line.split()[-1])
            elif line.startswith("property") and "red" in line:
                has_color = True
            elif line.startswith("property") and "confidence" in line:
                has_confidence = True
            elif line.startswith("property") and "view_id" in line:
                has_view_id = True
            elif line == "end_header":
                break

        for _ in range(num_vertices):
            parts = f.readline().split()
            points.append([float(parts[0]), float(parts[1]), float(parts[2])])
            idx = 3
            if has_color:
                colors.append([int(parts[idx]) / 255.0,
                               int(parts[idx + 1]) / 255.0,
                               int(parts[idx + 2]) / 255.0])
                idx += 3
            if has_confidence:
                confidence_vals.append(float(parts[idx])); idx += 1
            if has_view_id:
                view_ids.append(int(parts[idx])); idx += 1

    return (
        np.asarray(points, dtype=np.float32),
        np.asarray(colors, dtype=np.float32) if has_color else None,
        np.asarray(confidence_vals, dtype=np.float32) if has_confidence else None,
        np.asarray(view_ids, dtype=np.int32) if has_view_id else None,
    )


def color_by_view_id(view_id):
    """Map each point's view id to a palette colour (wraps past 8 views)."""
    idx = view_id.astype(np.int64) % len(VIEW_ID_PALETTE)
    return VIEW_ID_PALETTE[idx]


# --------------------------------------------------------------------------- #
# Viewers
# --------------------------------------------------------------------------- #
def view_open3d(points, colors, point_size, bg):
    import open3d as o3d

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points.astype(np.float64))
    if colors is not None:
        pcd.colors = o3d.utility.Vector3dVector(colors.astype(np.float64))

    # coordinate axes sized to the cloud
    extent = float(np.linalg.norm(points.max(0) - points.min(0)))
    axis = o3d.geometry.TriangleMesh.create_coordinate_frame(
        size=extent * 0.1 if extent > 0 else 1.0,
        origin=points.min(0),
    )

    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name="DA3 Point Cloud Preview")
    vis.add_geometry(pcd)
    vis.add_geometry(axis)
    opt = vis.get_render_option()
    opt.point_size = float(point_size)
    opt.background_color = np.asarray(bg, dtype=np.float64)
    print("[open3d] Left-drag: rotate | Wheel: zoom | Ctrl/Middle-drag: pan | Q/Esc: quit")
    vis.run()
    vis.destroy_window()


def view_matplotlib(points, colors, point_size, bg):
    import matplotlib.pyplot as plt

    # 3D scatter is slow; cap for interactivity
    cap = 200_000
    if len(points) > cap:
        sel = np.random.choice(len(points), cap, replace=False)
        points = points[sel]
        colors = colors[sel] if colors is not None else None
        print(f"[matplotlib] subsampled to {cap} points for rendering")

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor(bg)
    ax.scatter(points[:, 0], points[:, 1], points[:, 2],
               c=colors if colors is not None else None,
               s=point_size, marker=".", linewidths=0)
    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
    try:
        ax.set_box_aspect(np.ptp(points, axis=0))
    except Exception:
        pass
    plt.tight_layout()
    plt.show()


def pick_backend(name):
    if name != "auto":
        return name
    try:
        import open3d  # noqa: F401
        return "open3d"
    except ImportError:
        return "matplotlib"


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description="Preview a DA3 point cloud / gaussian PLY without ComfyUI.")
    ap.add_argument("file", help="Path to the .ply file")
    ap.add_argument("--color-mode", choices=["rgb", "view_id"], default="rgb",
                    help="rgb = original colours; view_id = colour by source view")
    ap.add_argument("--point-size", type=float, default=2.0)
    ap.add_argument("--backend", choices=["auto", "open3d", "matplotlib"],
                    default="auto")
    ap.add_argument("--max-points", type=int, default=2_000_000,
                    help="Random-subsample above this many points")
    ap.add_argument("--bg", default="0.1,0.1,0.1",
                    help="Background colour as R,G,B in 0..1")
    args = ap.parse_args()

    points, colors, confidence, view_id = read_ply(args.file)
    print(f"[loaded] {len(points):,} points from {args.file}")
    print(f"         colors={'yes' if colors is not None else 'no'}, "
          f"confidence={'yes' if confidence is not None else 'no'}, "
          f"view_id={'yes' if view_id is not None else 'no'}")

    if args.color_mode == "view_id":
        if view_id is not None:
            colors = color_by_view_id(view_id)
            print("[color] using per-view colouring")
        else:
            print("[warn] no view_id in file; keeping RGB colours")

    if len(points) > args.max_points:
        sel = np.random.choice(len(points), args.max_points, replace=False)
        points = points[sel]
        colors = colors[sel] if colors is not None else None
        print(f"[subsample] capped to {args.max_points:,} points")

    bg = [float(x) for x in args.bg.split(",")]

    backend = pick_backend(args.backend)
    print(f"[backend] {backend}")
    try:
        if backend == "open3d":
            view_open3d(points, colors, args.point_size, bg)
        else:
            view_matplotlib(points, colors, args.point_size, bg)
    except ImportError as e:
        sys.exit(f"[error] backend '{backend}' unavailable ({e}). "
                 f"Install open3d or matplotlib, or run with the comfyui "
                 f"conda env python.")


if __name__ == "__main__":
    main()
