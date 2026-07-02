#!/usr/bin/env python
"""
Depth map -> point cloud (PLY).

Reads a single depth image (8/16-bit grayscale, or a 3-channel image whose
channels are identical, e.g. the DA2 / Marigold maps in data/), back-projects
every valid pixel through a pinhole camera model and writes a PLY point cloud.
If an RGB image is supplied the points are coloured with it.

The output PLY is written with per-point RGB, so it can be opened directly
with the existing viewer:

    python preview_pointcloud.py out.ply

Depth convention
----------------
Depth-Anything / Marigold PNG previews follow the display convention that a
brighter pixel is *nearer* (inverse depth), so the raw value is treated as
inverse depth by default (--depth-mode inverse).

NOTE for this project: the Marigold-DC .npy depth maps use the opposite,
metric convention 0 = near, 1 = far (see draw_npy.py / point_selector.py). If
you feed such a map (or any image where a brighter pixel is *farther*), pass
--depth-mode linear, otherwise the resulting cloud will be depth-inverted.

The normalized value is mapped into the metric range [--z-near, --z-far].

Usage
-----
    python depth_to_pointcloud.py data/DA2/human.png -o data/point_cloud/human.ply
    python depth_to_pointcloud.py data/DA2/human.png --rgb data/input/human.png \
        -o data/point_cloud/human.ply
    python depth_to_pointcloud.py depth.png --fov 60 --depth-mode linear --preview

Run it with the ComfyUI conda env python (it has numpy / pillow / open3d):
    D:/anaconda3/envs/comfyui/python.exe depth_to_pointcloud.py depth.png -o out.ply

Dependencies: numpy + pillow (required). open3d only needed for --preview.
"""

import argparse
import os

import numpy as np


# --------------------------------------------------------------------------- #
# IO
# --------------------------------------------------------------------------- #
def load_gray(path):
    """Load an image as a 2-D float array of raw depth values.

    Handles 8/16-bit grayscale and 3-channel images with identical channels
    (the DA2 maps are stored this way). Returns (depth[H,W] float32, maxval)."""
    from PIL import Image

    im = Image.open(path)
    arr = np.asarray(im)
    if arr.ndim == 1:
        raise ValueError(f"{path}: expected a 2-D image, got a 1-D array "
                         f"(shape {arr.shape}); is this really a depth map?")
    if arr.ndim == 3:
        # collapse RGB(A) -> single channel; use channel 0 (channels are equal
        # for the depth maps, and luminance is a safe fallback otherwise)
        if arr.shape[2] >= 3 and not (np.array_equal(arr[..., 0], arr[..., 1])
                                      and np.array_equal(arr[..., 1], arr[..., 2])):
            arr = (0.299 * arr[..., 0] + 0.587 * arr[..., 1]
                   + 0.114 * arr[..., 2])
        else:
            arr = arr[..., 0]

    maxval = 65535.0 if arr.dtype == np.uint16 else 255.0
    return arr.astype(np.float32), maxval


def load_rgb(path, shape_hw):
    """Load an RGB image and resize to (H, W) if needed. Returns [H,W,3] uint8."""
    from PIL import Image

    im = Image.open(path).convert("RGB")
    if im.size != (shape_hw[1], shape_hw[0]):   # PIL size is (W, H)
        im = im.resize((shape_hw[1], shape_hw[0]), Image.BILINEAR)
    return np.asarray(im, dtype=np.uint8)


# --------------------------------------------------------------------------- #
# Depth -> 3-D
# --------------------------------------------------------------------------- #
def depth_to_metric(raw, maxval, mode, z_near, z_far):
    """Map raw depth values (0..maxval) to metric Z in [z_near, z_far]."""
    norm = np.clip(raw / maxval, 0.0, 1.0)          # 0..1
    if mode == "inverse":
        # bright (norm=1) -> near (z_near); dark (norm=0) -> far (z_far)
        z = z_far - norm * (z_far - z_near)
    else:  # linear: bright -> far
        z = z_near + norm * (z_far - z_near)
    return z.astype(np.float32)


def backproject(z, fx, fy, cx, cy):
    """Pinhole back-projection. z is [H,W]; returns points [H,W,3]."""
    h, w = z.shape
    us, vs = np.meshgrid(np.arange(w, dtype=np.float32),
                         np.arange(h, dtype=np.float32))
    x = (us - cx) / fx * z
    y = (vs - cy) / fy * z
    # image y grows downward; flip so the cloud is right-side up in viewers
    return np.stack([x, -y, -z], axis=-1)


def intrinsics_from_fov(w, h, fov_deg):
    """Focal length from a horizontal field of view (degrees); centred cx/cy."""
    fx = fy = (0.5 * w) / np.tan(0.5 * np.deg2rad(fov_deg))
    return fx, fy, w / 2.0, h / 2.0


# --------------------------------------------------------------------------- #
# PLY writing (ASCII, matches the format read by preview_pointcloud.py)
# --------------------------------------------------------------------------- #
def write_ply(path, points, colors=None):
    n = len(points)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    header = ["ply", "format ascii 1.0", f"element vertex {n}",
              "property float x", "property float y", "property float z"]
    if colors is not None:
        header += ["property uchar red", "property uchar green",
                   "property uchar blue"]
    header.append("end_header")

    # vectorised write: build the whole vertex block with numpy (a Python
    # per-point loop is minutes-slow at full resolution ~1M points).
    if colors is not None:
        rows = np.column_stack([points.astype(np.float32),
                                colors.astype(np.int32)])
        fmt = "%.6f %.6f %.6f %d %d %d"
    else:
        rows = points.astype(np.float32)
        fmt = "%.6f %.6f %.6f"

    with open(path, "w") as f:
        f.write("\n".join(header) + "\n")
        np.savetxt(f, rows, fmt=fmt)


def preview(points, colors):
    """Quick open3d preview (optional)."""
    try:
        import open3d as o3d
    except ImportError:
        print("[warn] open3d not available; skipping preview")
        return
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points.astype(np.float64))
    if colors is not None:
        pcd.colors = o3d.utility.Vector3dVector(colors.astype(np.float64) / 255.0)
    o3d.visualization.draw_geometries([pcd], window_name="Depth -> Point Cloud")


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description="Convert a depth map into a point cloud PLY.")
    ap.add_argument("depth", help="Path to the depth image (grayscale)")
    ap.add_argument("-o", "--output", default=None,
                    help="Output .ply path (default: <depth>_cloud.ply)")
    ap.add_argument("--rgb", default=None,
                    help="Optional RGB image to colour the points")
    ap.add_argument("--depth-mode", choices=["inverse", "linear"],
                    default="inverse",
                    help="inverse: bright=near (default, for DA/Marigold); "
                         "linear: bright=far")
    ap.add_argument("--z-near", type=float, default=1.0,
                    help="Metric Z for the nearest depth (default 1.0)")
    ap.add_argument("--z-far", type=float, default=4.0,
                    help="Metric Z for the farthest depth (default 4.0)")
    ap.add_argument("--fov", type=float, default=60.0,
                    help="Horizontal field of view in degrees (default 60)")
    ap.add_argument("--fx", type=float, default=None,
                    help="Focal length x in pixels (overrides --fov)")
    ap.add_argument("--fy", type=float, default=None, help="Focal length y")
    ap.add_argument("--cx", type=float, default=None, help="Principal point x")
    ap.add_argument("--cy", type=float, default=None, help="Principal point y")
    ap.add_argument("--stride", type=int, default=1,
                    help="Sample every Nth pixel to thin the cloud (default 1)")
    ap.add_argument("--min-depth", type=float, default=None,
                    help="Drop pixels whose raw value is <= this (0..maxval)")
    ap.add_argument("--preview", action="store_true",
                    help="Show the cloud with open3d after writing")
    args = ap.parse_args()

    if args.stride < 1:
        ap.error("--stride must be >= 1")
    if args.z_near >= args.z_far:
        ap.error("--z-near must be < --z-far")

    raw, maxval = load_gray(args.depth)
    h, w = raw.shape
    print(f"[loaded] depth {w}x{h} from {args.depth} (max value {maxval:.0f})")

    # intrinsics
    if args.fx is not None:
        fx = args.fx
        fy = args.fy if args.fy is not None else args.fx
        cx = args.cx if args.cx is not None else w / 2.0
        cy = args.cy if args.cy is not None else h / 2.0
    else:
        fx, fy, cx, cy = intrinsics_from_fov(w, h, args.fov)
    print(f"[camera] fx={fx:.1f} fy={fy:.1f} cx={cx:.1f} cy={cy:.1f}")

    z = depth_to_metric(raw, maxval, args.depth_mode, args.z_near, args.z_far)
    pts = backproject(z, fx, fy, cx, cy)            # [H,W,3]

    cols = None
    if args.rgb:
        cols = load_rgb(args.rgb, (h, w))
        print(f"[color] using {args.rgb}")

    # valid mask (optionally drop background by raw threshold) + stride
    valid = np.ones((h, w), dtype=bool)
    if args.min_depth is not None:
        valid &= raw > args.min_depth
    if args.stride > 1:
        s = np.zeros((h, w), dtype=bool)
        s[::args.stride, ::args.stride] = True
        valid &= s

    pts = pts[valid]
    cols = cols[valid] if cols is not None else None
    print(f"[points] {len(pts):,} points")

    out = args.output or (os.path.splitext(args.depth)[0] + "_cloud.ply")
    write_ply(out, pts, cols)
    print(f"[saved] {out}")

    if args.preview:
        preview(pts, cols)


if __name__ == "__main__":
    main()
