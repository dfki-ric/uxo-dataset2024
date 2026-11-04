#!/usr/bin/env python3
"""Log UXO dataset 2024 recordings to Rerun.

Per recording this logs, on the `aris_frame` (sequence) and `time` (timestamp) timelines:

- the gantry/AR3 pose chain from ``calibration/transforms.yaml`` + ``gantry.csv`` + AR3 pan/tilt/roll
  (``aris_frame_meta.csv``), the same composition as ``_create_ar3_df`` in ``scripts/release_1_export.py``
- the GoPro frame as a pinhole camera in 3D, with the 2D bounding-box labels (label coords x3)
- the ARIS polar image (2D) and the raw ARIS frame back-projected as a 3D sonar fan in the sonar frame
- the ARIS field of view as a frustum in 3D, and both the frustum and the sonar returns projected into the
  GoPro image. The ARIS cannot resolve elevation, so --overlay-mode picks how returns are drawn:
  band (default, each return spread over the vertical aperture as a heatmap) or line (zero elevation)
- the target pose, the full AR3 trajectory, gantry/AR3 scalars, notes, and the target's textured 3D scan

Usage:
    python rerun_viz/log_to_rerun.py data_download/extracted/uxo_samples/2023-09-20_180722 --spawn
    python rerun_viz/log_to_rerun.py data_download/extracted/uxo_samples --save-dir data_download/rrd
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import rerun as rr
import rerun.blueprint as rrb
import yaml
from scipy.spatial.transform import Rotation as R

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts" / "common"))
from aris_definitions import BeamWidthsAris3000_128  # noqa: E402

# notes.txt "target:" keyword -> (frame in transforms.yaml, 3D model file stem)
TARGETS = {
    "100lbs": ("target/100lbs", "100lbs"),
    "mortar": ("target/mortar_shell", "mortar_shell"),
    "incendiary": ("target/incendiary", "incindiary"),
}

# GoPro intrinsics for 1920x1080, "linear" lens mode (calibration/camera_parameters/camera_parameter_linear.txt).
# Distortion is ignored here; frames are logged as-is.
GOPRO_K = np.array([[1473.04513, 0.0, 969.389055], [0.0, 1478.33421, 540.775107], [0.0, 0.0, 1.0]])
LABEL_SCALE = 3  # README: "Labels for GoPro frames (multiply coordinates by 3!)"
BAND_DOWNSCALE = 4


# ---------------------------------------------------------------- transforms
def _to_mat(entry: dict) -> np.ndarray:
    t, q = entry["translation"], entry["rotation"]
    m = np.eye(4)
    m[:3, :3] = R.from_quat([q["x"], q["y"], q["z"], q["w"]]).as_matrix()
    m[:3, 3] = [t["x"], t["y"], t["z"]]
    return m


def load_static_tfs(path: Path) -> dict[str, tuple[str, np.ndarray]]:
    tf = yaml.safe_load(path.read_text())
    return {e["frame_id"]: (e["parent_frame_id"], _to_mat(e)) for e in tf["setup"] + tf["targets"]}


def chain(tfs: dict, frame: str, stop: str) -> np.ndarray:
    """Pose of `frame` expressed in `stop`."""
    m = np.eye(4)
    while frame != stop:
        parent, a = tfs[frame]
        m = a @ m
        frame = parent
    return m


def tf3d(m: np.ndarray) -> rr.Transform3D:
    return rr.Transform3D(translation=m[:3, 3], quaternion=R.from_matrix(m[:3, :3]).as_quat())


# ---------------------------------------------------------------- sonar
BEAM_ANGLES = np.deg2rad(np.array(BeamWidthsAris3000_128)[:, 0])


def sonar_returns(raw: np.ndarray, window_start: float, window_length: float, threshold: int, step: int):
    """Returns of a raw ARIS frame (samples x beams) above `threshold` as (range [m], beam angle [rad], intensity)."""
    n_bins, n_beams = raw.shape
    assert n_beams == len(BEAM_ANGLES), f"expected {len(BEAM_ANGLES)} beams, got {n_beams}"
    sub = raw[::step]
    rng = window_start + (np.arange(n_bins)[::step] + 0.5) * window_length / n_bins
    bins, beams = np.nonzero(sub >= threshold)
    return rng[bins], BEAM_ANGLES[beams], sub[bins, beams]


_INFERNO = cv2.applyColorMap(np.arange(256, dtype=np.uint8)[:, None], cv2.COLORMAP_INFERNO)[:, 0, ::-1]


def colormap(values: np.ndarray, lo: int, hi: int = 120, alpha: int = 255) -> np.ndarray:
    """Inferno colours for intensities in [lo, hi], skipping the near-black low end so returns stay visible."""
    t = np.clip((values.astype(float) - lo) / max(hi - lo, 1), 0, 1)
    rgb = _INFERNO[(80 + t * 175).astype(np.uint8)]
    return np.concatenate([rgb, np.full((len(values), 1), alpha, np.uint8)], axis=1)


# Horizontal aperture from the outer beam edges of the ARIS 3000 beam table (~30 deg).
AZ_MIN = np.deg2rad(BeamWidthsAris3000_128[0][1])
AZ_MAX = np.deg2rad(BeamWidthsAris3000_128[-1][2])
SONAR_COLOR = [255, 140, 0]


def _spherical(r, az, el) -> np.ndarray:
    """Sonar frame point: z forward, x lateral (beam angle), y vertical (elevation)."""
    r, az, el = np.broadcast_arrays(r, az, el)
    return np.stack([r * np.cos(el) * np.sin(az), r * np.sin(el), r * np.cos(el) * np.cos(az)], axis=-1)


def sonar_frustum(r_near: float, r_far: float, elev_deg: float, n: int = 32) -> list[np.ndarray]:
    """Line strips outlining the ARIS field of view: an annular sector, `elev_deg` tall, between r_near and r_far."""
    el = np.deg2rad(elev_deg) / 2
    az = np.linspace(AZ_MIN, AZ_MAX, n)
    els = np.linspace(-el, el, n // 4)
    strips = []
    for r in (r_near, r_far):
        strips += [_spherical(r, az, -el), _spherical(r, az, el)]  # bottom / top arcs
        strips += [_spherical(r, AZ_MIN, els), _spherical(r, AZ_MAX, els)]  # left / right edges
    for a in (AZ_MIN, AZ_MAX):
        for e in (-el, el):
            strips.append(np.stack([np.zeros(3), _spherical(r_far, a, e)]))  # apex -> far corners
    strips.append(np.stack([np.zeros(3), _spherical(r_far, 0.0, 0.0)]))  # boresight
    return strips


def project(pts_sonar: np.ndarray, cam_from_sonar: np.ndarray, size=(1920, 1080), margin: float = 0.0):
    """Project sonar-frame points into GoPro pixels. Returns (uv, mask of points in front and within the image)."""
    pc = pts_sonar @ cam_from_sonar[:3, :3].T + cam_from_sonar[:3, 3]
    z = pc[:, 2]
    uv = (pc @ GOPRO_K.T)[:, :2] / np.where(z > 1e-6, z, np.nan)[:, None]
    w, h = size
    ok = (z > 0.05) & (uv[:, 0] >= -margin) & (uv[:, 0] < w + margin) & (uv[:, 1] >= -margin) & (uv[:, 1] < h + margin)
    return uv, ok


def beam_weight(el: np.ndarray, elev_deg: float) -> np.ndarray:
    """Vertical beam pattern: Gaussian that is -3 dB (0.5) at the edges of the nominal aperture."""
    half = np.deg2rad(elev_deg) / 2
    return np.exp(-np.log(2) * (el / half) ** 2)


def render_band(r, th, val, cam_from_sonar, elev_deg: float, lo: int, hi: int, alpha: int,
                size=(1920, 1080), down: int = 4, n_el: int = 41) -> bytes:
    """Spread every return over its elevation arc, splat the arcs into an image (max per pixel) and return an
    RGBA PNG at 1/`down` of the GoPro resolution (scale it by `down` when displaying).
    Colour = intensity x vertical beam weight; transparent where empty."""
    w, h = size[0] // down, size[1] // down
    el = np.linspace(-np.deg2rad(elev_deg) / 2, np.deg2rad(elev_deg) / 2, n_el)
    pts = _spherical(r[:, None], th[:, None], el[None, :]).reshape(-1, 3)
    t = np.clip((val.astype(float) - lo) / max(hi - lo, 1), 0, 1)
    strength = (t[:, None] * beam_weight(el, elev_deg)[None, :]).ravel()
    uv, ok = project(pts, cam_from_sonar, size=size)
    px = (uv[ok] / down).astype(int)
    buf = np.zeros((h, w), np.float32)
    np.maximum.at(buf, (np.clip(px[:, 1], 0, h - 1), np.clip(px[:, 0], 0, w - 1)), strength[ok])
    buf = cv2.GaussianBlur(cv2.dilate(buf, np.ones((3, 3), np.uint8)), (3, 3), 0)
    rgb = _INFERNO[(80 + buf * 175).astype(np.uint8)]
    a = (np.clip(buf * 1.5, 0, 1) * alpha).astype(np.uint8)  # boost so mid-strength returns are visible
    return cv2.imencode(".png", cv2.cvtColor(np.dstack([rgb, a]), cv2.COLOR_RGBA2BGRA))[1].tobytes()


def project_strips(strips: list[np.ndarray], cam_from_sonar: np.ndarray) -> list[np.ndarray]:
    """Project 3D strips into the image, splitting them where they leave the (padded) image or go behind the camera."""
    out = []
    for s in strips:
        if len(s) == 2:  # straight segments: resample so they bend correctly when clipped
            s = s[0] + np.linspace(0, 1, 32)[:, None] * (s[1] - s[0])
        uv, ok = project(s, cam_from_sonar, margin=2000)
        breaks = np.flatnonzero(np.diff(ok.astype(int))) + 1
        out += [seg for seg, k in zip(np.split(uv, breaks), np.split(ok, breaks)) if k[0] and len(seg) > 1]
    return out


# ---------------------------------------------------------------- logging
def blueprint() -> rrb.Blueprint:
    return rrb.Blueprint(
        rrb.Horizontal(
            rrb.Vertical(
                rrb.Spatial3DView(name="Scene", origin="world"),
                rrb.Tabs(
                    rrb.TimeSeriesView(name="AR3 pan/tilt/roll [deg]", origin="plots/ar3_deg"),
                    rrb.TimeSeriesView(name="Gantry xyz [m]", origin="plots/gantry"),
                ),
                row_shares=[3, 1],
            ),
            rrb.Vertical(
                rrb.Spatial2DView(name="GoPro", origin="world/crane/ar3/camera"),
                rrb.Spatial2DView(name="ARIS polar", origin="sonar_polar"),
                rrb.Tabs(
                    rrb.Spatial3DView(name="Target scan", origin="target_model"),
                    rrb.TextDocumentView(name="Notes", origin="notes"),
                ),
            ),
            column_shares=[3, 2],
        ),
        collapse_panels=True,
    )


def log_recording(rec_dir: Path, tfs: dict, models_dir: Path, args) -> None:
    notes = (rec_dir / "notes.txt").read_text()
    key = next((k for k in TARGETS if k in notes.lower()), None)

    gantry = pd.read_csv(rec_dir / "gantry.csv", index_col="aris_frame_idx")
    meta = pd.read_csv(rec_dir / "aris_frame_meta.csv", index_col="FrameIndex")
    frames = gantry.index[:: args.every]

    ar3_static = tfs["setup/ar3"][1]
    rr.log("world", rr.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)
    sonar_in_ar3 = chain(tfs, "setup/sonar", "setup/ar3")
    camera_in_ar3 = chain(tfs, "setup/camera", "setup/ar3")
    cam_from_sonar = np.linalg.inv(camera_in_ar3) @ sonar_in_ar3
    rr.log("world/crane/ar3/sonar", tf3d(sonar_in_ar3), static=True)
    rr.log("world/crane/ar3/sonar", rr.TransformAxes3D(0.1), static=True)
    rr.log("world/crane/ar3/camera", tf3d(camera_in_ar3), static=True)
    rr.log(
        "world/crane/ar3/camera",
        rr.Pinhole(image_from_camera=GOPRO_K, resolution=[1920, 1080], camera_xyz=rr.ViewCoordinates.RDF,
                   image_plane_distance=0.3),
        static=True,
    )
    # The band overlay is rendered at 1/BAND_DOWNSCALE resolution (keeps .rrd size down) and scaled up here.
    rr.log("world/crane/ar3/camera/sonar_band", rr.Transform3D(scale=[BAND_DOWNSCALE, BAND_DOWNSCALE, 1]),
           static=True)
    rr.log("notes", rr.TextDocument(f"# {rec_dir.name}\n\n{notes}", media_type="text/markdown"), static=True)

    if key:
        frame_id, model = TARGETS[key]
        target = tfs[frame_id][1]
        rr.log(f"world/{frame_id}", tf3d(target), rr.TransformAxes3D(0.15), static=True)
        rr.log(f"world/{frame_id}/origin", rr.Points3D([[0, 0, 0]], radii=0.02, labels=[key],
                                                       colors=[[255, 200, 0]]), static=True)
        obj = models_dir / f"{model}.obj"
        if obj.exists():
            # Photogrammetry scan in its own (unregistered) frame and scale, so it gets a separate view.
            rr.log("target_model", rr.Asset3D(path=obj), static=True)

    # Full AR3 trajectory (static), computed from all frames.
    traj = gantry[["x", "y", "z"]].to_numpy() + ar3_static[:3, 3]
    rr.log("world/trajectory", rr.LineStrips3D([traj], radii=0.004, colors=[[80, 160, 255]]), static=True)

    last_window = None
    for idx in frames:
        m = meta.loc[idx]
        rr.set_time("aris_frame", sequence=int(idx))
        rr.set_time("time", timestamp=np.datetime64(int(m["FrameTime"]), "us"))

        # crane carriage (translation only) -> AR3 (static offset + pan/tilt/roll)
        rr.log("world/crane", rr.Transform3D(translation=gantry.loc[idx, ["x", "y", "z"]].to_numpy(float)))
        rot = R.from_matrix(ar3_static[:3, :3]) * R.from_euler(
            "xyz", m[["SonarRoll", "SonarTilt", "SonarPan"]].to_numpy(float), degrees=True)
        rr.log("world/crane/ar3", rr.Transform3D(translation=ar3_static[:3, 3], quaternion=rot.as_quat()))

        gp = rec_dir / "gopro" / f"{idx:04}.jpg"
        if gp.exists():
            rr.log("world/crane/ar3/camera", rr.EncodedImage(path=gp))
        lab = rec_dir / "labels" / f"{idx:04}.json"
        if lab.exists():
            d = json.loads(lab.read_text())
            box = np.array([d["x_min"], d["y_min"], d["x_max"], d["y_max"]]) * LABEL_SCALE
            rr.log("world/crane/ar3/camera/label",
                   rr.Boxes2D(array=box, array_format=rr.Box2DFormat.XYXY, labels=[d["class"]],
                              colors=[[0, 255, 120]]))
        else:
            rr.log("world/crane/ar3/camera/label", rr.Clear(recursive=False))

        pol = rec_dir / "aris_polar" / f"{idx:04}.png"
        if pol.exists():
            rr.log("sonar_polar", rr.EncodedImage(path=pol))

        w_start, w_len = float(m["WindowStart"]), float(m["WindowLength"])
        raw = cv2.imread(str(rec_dir / "aris_raw" / f"{idx:04}.pgm"), cv2.IMREAD_GRAYSCALE)
        r, th, val = sonar_returns(raw, w_start, w_len, args.threshold, args.bin_step)
        pts = _spherical(r, th, np.zeros_like(r))  # zero elevation
        rr.log("world/crane/ar3/sonar/fan", rr.Points3D(pts, colors=colormap(val, args.threshold), radii=0.004))

        # Sonar field of view (static relative to the camera unless the range window changes)
        if (w_start, w_len) != last_window:
            last_window = (w_start, w_len)
            frustum = sonar_frustum(w_start, w_start + w_len, args.sonar_elevation)
            rr.log("world/crane/ar3/sonar/frustum",
                   rr.LineStrips3D(frustum, colors=[SONAR_COLOR], radii=rr.Radius.ui_points(1.0)))
            rr.log("world/crane/ar3/camera/sonar_frustum",
                   rr.LineStrips2D(project_strips(frustum, cam_from_sonar), colors=[SONAR_COLOR],
                                   radii=rr.Radius.ui_points(1.0), draw_order=40))

        # Sonar returns in the GoPro image. The ARIS has no elevation resolution, so either spread each return
        # over its elevation arc ("band"), or place it at zero elevation ("line").
        if args.overlay_mode == "band":
            png = render_band(r, th, val, cam_from_sonar, args.sonar_elevation, args.threshold, 120,
                              args.overlay_alpha, down=BAND_DOWNSCALE)
            rr.log("world/crane/ar3/camera/sonar_band",
                   rr.EncodedImage(contents=png, media_type="image/png", draw_order=5,
                                   magnification_filter="Linear"))
        else:
            uv, ok = project(pts, cam_from_sonar)
            rr.log("world/crane/ar3/camera/sonar_overlay",
                   rr.Points2D(uv[ok], colors=colormap(val[ok], args.threshold, alpha=args.overlay_alpha),
                               radii=rr.Radius.ui_points(args.overlay_radius), draw_order=30))

        rr.log("plots/gantry", rr.Scalars(gantry.loc[idx, ["x", "y", "z"]].to_numpy(float)))
        rr.log("plots/ar3_deg", rr.Scalars(m[["SonarPan", "SonarTilt", "SonarRoll"]].to_numpy(float)))

    rr.log("plots/gantry", rr.SeriesLines(names=["x", "y", "z"]), static=True)
    rr.log("plots/ar3_deg", rr.SeriesLines(names=["pan", "tilt", "roll"]), static=True)


def find_recordings(paths: list[Path]) -> list[Path]:
    out = []
    for p in paths:
        if (p / "gantry.csv").exists():
            out.append(p)
        else:
            out += sorted(d for d in p.iterdir() if (d / "gantry.csv").exists() and not d.name.startswith("."))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", type=Path, help="recording folder(s) or a folder containing recordings")
    ap.add_argument("--calibration", type=Path, default=REPO / "calibration" / "transforms.yaml")
    ap.add_argument("--models", type=Path, default=REPO / "data_download" / "extracted" / "3d_models")
    ap.add_argument("--every", type=int, default=1, help="log every n-th frame")
    ap.add_argument("--threshold", type=int, default=35, help="min raw ARIS intensity (0-255) for 3D fan points")
    ap.add_argument("--bin-step", type=int, default=2, help="range-bin subsampling for the 3D fan")
    ap.add_argument("--sonar-elevation", type=float, default=14.0,
                    help="ARIS vertical aperture in degrees for the frustum (ARIS 3000: 14)")
    ap.add_argument("--overlay-mode", choices=["band", "line"], default="band",
                    help="how sonar returns are placed in the GoPro image: 'band' spreads each return over the "
                         "vertical aperture (heatmap); 'line' puts it at zero elevation")
    ap.add_argument("--overlay-alpha", type=int, default=200, help="max alpha (0-255) of the sonar overlay")
    ap.add_argument("--overlay-radius", type=float, default=2.0,
                    help="UI-point radius of sonar points in the image (line mode)")
    ap.add_argument("--spawn", action="store_true", help="stream into a spawned Rerun viewer")
    ap.add_argument("--save-dir", type=Path, help="write one .rrd per recording here")
    args = ap.parse_args()
    if not (args.spawn or args.save_dir):
        ap.error("pass --spawn and/or --save-dir")

    tfs = load_static_tfs(args.calibration)
    for rec_dir in find_recordings(args.paths):
        # Non-default overlay modes get their own recording id so they don't merge with band-mode files.
        name = rec_dir.name if args.overlay_mode == "band" else f"{rec_dir.name} ({args.overlay_mode})"
        print(f"logging {name} ...", flush=True)
        rec = rr.RecordingStream("uxo_dataset2024", recording_id=name)
        with rec:
            rr.send_recording_name(name)
            sinks = []
            if args.spawn:
                rr.spawn(connect=False)
                sinks.append(rr.GrpcSink())
            if args.save_dir:
                args.save_dir.mkdir(parents=True, exist_ok=True)
                sinks.append(rr.FileSink(args.save_dir / f"{rec_dir.name}.rrd"))
            rr.set_sinks(*sinks, default_blueprint=blueprint())
            log_recording(rec_dir, tfs, args.models, args)
        rec.flush()


if __name__ == "__main__":
    main()
