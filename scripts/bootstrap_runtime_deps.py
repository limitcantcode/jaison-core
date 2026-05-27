"""
Download heavyweight runtime binaries and minimal RVC weights for VC inference
(Hubert content encoder + RMVPE pitch; see `VC.vc_inference` / `Pipeline.get_f0`).

Layout:
  models/kobold/koboldcpp[.exe]
  models/rvc/base/hubert/hubert_base.pt
  models/rvc/base/rmvpe/rmvpe.pt
  models/rvc/weights/   — place your *.pth voice checkpoints here (see weight_root)

Not downloaded (unused by VC inference path): pretrained G/D blobs, UVR5 weights,
rmvpe.onnx (only needed for DirectML / DeviceType privateuseone).

Environment (optional):
  KOBOLDCPP_VARIANT   cuda | nocuda | oldpc  (default: cuda — NVIDIA-oriented builds where available)
  KOBOLDCPP_ASSET_NAME  Full GitHub asset filename override (needed for linux aarch64: no official v1.113.2 build)
  KOBOLDCPP_SKIP      set to 1 to skip KoboldCPP download
  RVC_SKIP            set to 1 to skip RVC HF download
  RVC_ASSETS_REVISION Hugging Face revision for lj1995/VoiceConversionWebUI (default: main)

Hubert + rmvpe file source: Hugging Face `lj1995/VoiceConversionWebUI`
(legacy parity with subsets of Retrieval-based-Voice-Conversion tooling).

See: KoboldCPP https://github.com/LostRuins/koboldcpp/releases/tag/v1.113.2
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import stat
import sys
import tempfile
from pathlib import Path

import requests


KOBOLDCPP_TAG = "v1.113.2"
RELEASE_BASE = f"https://github.com/LostRuins/koboldcpp/releases/download/{KOBOLDCPP_TAG}"

FFMPEG_STATIC_TAG = "b6.1.1"
FFMPEG_STATIC_RELEASE_BASE = (
    f"https://github.com/eugeneware/ffmpeg-static/releases/download/{FFMPEG_STATIC_TAG}"
)
HF_RVC_REPO = os.environ.get("RVC_REPO_ID", "lj1995/VoiceConversionWebUI")

RVC_ALLOW_PATTERNS = [
    "hubert_base.pt",
    "rmvpe.pt",
]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _download_url(url: str, dest: Path, *, chunk: int = 8 * 1024 * 1024) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix(dest.suffix + ".partial")
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        written = 0
        with partial.open("wb") as f:
            for block in r.iter_content(chunk_size=chunk):
                if block:
                    f.write(block)
                    written += len(block)
                    if written and written % (256 * chunk) < chunk:
                        print(f"  ... {written // (1024 * 1024)} MiB")
    partial.replace(dest)


def _resolve_kobold_asset_name(machine: str, system: str, variant: str) -> str | None:
    """Return GitHub release asset basename, or None if user must supply KOBOLDCPP_ASSET_NAME."""
    ov = os.environ.get("KOBOLDCPP_ASSET_NAME", "").strip()
    if ov:
        return ov

    m = machine.lower()
    v = variant.lower().strip()

    if system == "Windows":
        is_arm_win = os.environ.get("PROCESSOR_ARCHITECTURE", "").upper() == "ARM64" or "arm" in m
        if is_arm_win:
            print(
                "  Windows ARM: using koboldcpp-nocuda.exe (no CUDA KoboldCPP for this CPU class)."
            )
            return "koboldcpp-nocuda.exe"
        if v not in {"cuda", "nocuda", "oldpc"}:
            print(f"Unknown KOBOLDCPP_VARIANT={v!r}; using cuda.")
            v = "cuda"
        names = {
            "cuda": "koboldcpp.exe",
            "nocuda": "koboldcpp-nocuda.exe",
            "oldpc": "koboldcpp-oldpc.exe",
        }
        return names[v]

    if system == "Linux":
        if m in {"aarch64", "arm64"}:
            print(
                "ERROR: KoboldCPP v1.113.2 has no official linux aarch64 GitHub asset.\n"
                "  Set KOBOLDCPP_ASSET_NAME to a release asset name you can run on this machine,\n"
                "  or set KOBOLDCPP_SKIP=1 and install KoboldCPP manually into models/kobold/.\n"
                "  Release index: "
                + f"https://github.com/LostRuins/koboldcpp/releases/tag/{KOBOLDCPP_TAG}",
                file=sys.stderr,
            )
            return None

        if m in {"x86_64", "amd64"}:
            if v not in {"cuda", "nocuda", "oldpc"}:
                print(f"Unknown KOBOLDCPP_VARIANT={v!r}; using cuda.")
                v = "cuda"
            names = {
                "cuda": "koboldcpp-linux-x64",
                "nocuda": "koboldcpp-linux-x64-nocuda",
                "oldpc": "koboldcpp-linux-x64-oldpc",
            }
            return names[v]

        print(f"ERROR: Unsupported Linux machine type: {machine!r}", file=sys.stderr)
        return None

    if system == "Darwin":
        if m in {"aarch64", "arm64"}:
            return "koboldcpp-mac-arm64"
        print(
            f"ERROR: KoboldCPP v1.113.2 has no macOS Intel build; machine={machine!r}",
            file=sys.stderr,
        )
        return None

    print(f"ERROR: Unsupported OS for Kobold bootstrap: {system!r}", file=sys.stderr)
    return None


def _kobold_destination_name(system: str) -> Path:
    return Path("koboldcpp.exe") if system == "Windows" else Path("koboldcpp")


def _maybe_skip_kobold(out_dir: Path, force: bool) -> bool:
    marker = out_dir / ".koboldcpp-version"
    dest_name = _kobold_destination_name(platform.system())
    binary = out_dir / dest_name

    version_label = marker.read_text(encoding="utf-8").strip() if marker.is_file() else None
    if not force and binary.is_file() and version_label == KOBOLDCPP_TAG:
        print(f"KoboldCPP {KOBOLDCPP_TAG} already present at {binary}, skipping.")
        return True
    return False


def download_koboldcpp(*, project_root: Path, force: bool) -> None:
    if os.environ.get("KOBOLDCPP_SKIP") == "1":
        print("KoboldCPP download skipped (KOBOLDCPP_SKIP=1).")
        return

    out_dir = project_root / "models" / "kobold"
    out_dir.mkdir(parents=True, exist_ok=True)

    if _maybe_skip_kobold(out_dir, force):
        return

    system = platform.system()
    variant = os.environ.get("KOBOLDCPP_VARIANT", "cuda")
    asset = _resolve_kobold_asset_name(platform.machine(), system, variant)
    if asset is None:
        raise SystemExit(1)

    url = f"{RELEASE_BASE}/{asset}"
    dest_bin = _kobold_destination_name(system)
    staging = out_dir / asset
    final = out_dir / dest_bin

    print(f"Downloading KoboldCPP {KOBOLDCPP_TAG}: {asset} ...")
    _download_url(url, staging)

    if final != staging:
        if final.exists():
            final.unlink()

        shutil.move(staging, final)

    if system != "Windows":
        mode = final.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        final.chmod(mode)

    (out_dir / ".koboldcpp-version").write_text(KOBOLDCPP_TAG + "\n", encoding="utf-8")

    print(f"  -> {final}")


def _ffmpeg_static_asset_names(system: str, machine: str) -> tuple[str, str] | None:
    """Return (ffmpeg_asset, ffprobe_asset) names for ffmpeg-static b6.1.1, or None if unsupported."""
    sys_norm = system
    m = machine.lower()

    if sys_norm == "Windows":
        # We only support 64-bit Windows here.
        arch = os.environ.get("PROCESSOR_ARCHITECTURE", "").lower() or m
        if "64" not in arch and "x64" not in arch and "amd64" not in arch:
            print(
                f"ERROR: Unsupported Windows architecture for ffmpeg-static: {arch!r}.",
                file=sys.stderr,
            )
            return None
        return ("ffmpeg-win32-x64", "ffprobe-win32-x64")

    if sys_norm == "Linux":
        if m in {"x86_64", "amd64"}:
            return ("ffmpeg-linux-x64", "ffprobe-linux-x64")
        if m in {"aarch64", "arm64"}:
            return ("ffmpeg-linux-arm64", "ffprobe-linux-arm64")
        if m in {"armv7l", "armv6l", "arm"}:
            return ("ffmpeg-linux-arm", "ffprobe-linux-arm")
        if m in {"i386", "i686"}:
            return ("ffmpeg-linux-ia32", "ffprobe-linux-ia32")
        print(f"ERROR: Unsupported Linux machine type for ffmpeg-static: {machine!r}", file=sys.stderr)
        return None

    if sys_norm == "Darwin":
        if m in {"arm64", "aarch64"}:
            return ("ffmpeg-darwin-arm64", "ffprobe-darwin-arm64")
        if m in {"x86_64"}:
            return ("ffmpeg-darwin-x64", "ffprobe-darwin-x64")
        print(f"ERROR: Unsupported macOS machine type for ffmpeg-static: {machine!r}", file=sys.stderr)
        return None

    print(f"ERROR: Unsupported OS for ffmpeg-static bootstrap: {system!r}", file=sys.stderr)
    return None


def _ffmpeg_static_destination_names(system: str) -> tuple[Path, Path]:
    if system == "Windows":
        return (Path("ffmpeg.exe"), Path("ffprobe.exe"))
    return (Path("ffmpeg"), Path("ffprobe"))


def _ffmpeg_static_installed(bin_dir: Path, force: bool) -> bool:
    marker = bin_dir / ".ffmpeg-static-version"
    ffmpeg_dest, ffprobe_dest = _ffmpeg_static_destination_names(platform.system())
    ffmpeg_bin = bin_dir / ffmpeg_dest
    ffprobe_bin = bin_dir / ffprobe_dest

    version_label = marker.read_text(encoding="utf-8").strip() if marker.is_file() else None
    if (
        not force
        and ffmpeg_bin.is_file()
        and ffprobe_bin.is_file()
        and version_label == FFMPEG_STATIC_TAG
    ):
        print(f"ffmpeg-static {FFMPEG_STATIC_TAG} already present in {bin_dir}, skipping.")
        return True
    return False


def download_ffmpeg_and_ffprobe(*, project_root: Path, force: bool) -> None:
    bin_dir = project_root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    if _ffmpeg_static_installed(bin_dir, force):
        return

    system = platform.system()
    machine = platform.machine()

    assets = _ffmpeg_static_asset_names(system, machine)
    if assets is None:
        raise SystemExit(1)

    ffmpeg_asset, ffprobe_asset = assets
    ffmpeg_dest_name, ffprobe_dest_name = _ffmpeg_static_destination_names(system)

    ffmpeg_staging = bin_dir / ffmpeg_asset
    ffprobe_staging = bin_dir / ffprobe_asset

    ffmpeg_final = bin_dir / ffmpeg_dest_name
    ffprobe_final = bin_dir / ffprobe_dest_name

    print(f"Downloading ffmpeg-static {FFMPEG_STATIC_TAG} binaries for {system} / {machine} ...")

    ffmpeg_url = f"{FFMPEG_STATIC_RELEASE_BASE}/{ffmpeg_asset}"
    ffprobe_url = f"{FFMPEG_STATIC_RELEASE_BASE}/{ffprobe_asset}"

    print(f"  -> ffmpeg from {ffmpeg_url}")
    _download_url(ffmpeg_url, ffmpeg_staging)

    print(f"  -> ffprobe from {ffprobe_url}")
    _download_url(ffprobe_url, ffprobe_staging)

    if ffmpeg_final.exists():
        ffmpeg_final.unlink()
    if ffprobe_final.exists():
        ffprobe_final.unlink()

    shutil.move(ffmpeg_staging, ffmpeg_final)
    shutil.move(ffprobe_staging, ffprobe_final)

    if system != "Windows":
        for final in (ffmpeg_final, ffprobe_final):
            mode = final.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            final.chmod(mode)

    (bin_dir / ".ffmpeg-static-version").write_text(
        FFMPEG_STATIC_TAG + "\n", encoding="utf-8"
    )

    print(f"  ffmpeg -> {ffmpeg_final}")
    print(f"  ffprobe -> {ffprobe_final}")


def _rvc_minimal_installed(base: Path) -> bool:
    return (base / "hubert" / "hubert_base.pt").is_file() and (
        base / "rmvpe" / "rmvpe.pt"
    ).is_file()


def ensure_rvc_voice_weights_dir(project_root: Path) -> Path:
    """Directory for VC `.pth` checkpoints (`weight_root` in `.env-template`)."""
    voices = project_root / "models" / "rvc" / "weights"
    voices.mkdir(parents=True, exist_ok=True)
    return voices


def download_rvc_assets(*, project_root: Path, force: bool, revision: str | None) -> None:
    if os.environ.get("RVC_SKIP") == "1":
        print("RVC inference weights skipped (RVC_SKIP=1).")
        ensure_rvc_voice_weights_dir(project_root)
        return

    try:
        from huggingface_hub import snapshot_download
    except ImportError as e:
        raise SystemExit(
            "huggingface-hub is required. Install deps with `uv sync` then rerun."
        ) from e

    base = project_root / "models" / "rvc" / "base"
    marker = base / ".rvc-base-stamp"

    revision = revision or os.environ.get("RVC_ASSETS_REVISION", "main")

    stamp = f"{HF_RVC_REPO}@{revision}\n"

    if (
        not force
        and _rvc_minimal_installed(base)
        and marker.is_file()
        and marker.read_text(encoding="utf-8") == stamp
    ):
        print("RVC inference weights (hubert + rmvpe) already installed, skipping.")
        return

    print(
        f"Fetching Hubert + RMVPE checkpoints from {HF_RVC_REPO}@{revision} ..."
        " (much smaller than full WebUI bundle)"
    )

    with tempfile.TemporaryDirectory(prefix="rvc_hf_") as staging_s:
        staging = Path(staging_s)
        snapshot_download(
            repo_id=HF_RVC_REPO,
            revision=revision,
            local_dir=str(staging),
            allow_patterns=RVC_ALLOW_PATTERNS,
        )

        hubert_pt = staging / "hubert_base.pt"
        rmpt = staging / "rmvpe.pt"

        missing = [
            label
            for label, ok in (
                ("hubert_base.pt", hubert_pt.is_file()),
                ("rmvpe.pt", rmpt.is_file()),
            )
            if not ok
        ]

        if missing:
            raise SystemExit(f"HF snapshot incomplete — missing after download: {missing}")

        base.mkdir(parents=True, exist_ok=True)

        hubert_dir = base / "hubert"
        hubert_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(hubert_pt, hubert_dir / "hubert_base.pt")

        rm_dest = base / "rmvpe"
        if rm_dest.exists():
            shutil.rmtree(rm_dest)
        rm_dest.mkdir(parents=True, exist_ok=True)
        shutil.move(rmpt, rm_dest / "rmvpe.pt")

    marker.write_text(stamp, encoding="utf-8")

    voices = ensure_rvc_voice_weights_dir(project_root)

    print(f"  -> {base}")
    print(f"  (place RVC *.pth models under {voices})")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download KoboldCPP, ffmpeg/ffprobe, and RVC runtime assets."
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if version markers indicate an existing install.",
    )
    p.add_argument("--skip-kobold", action="store_true", help="Skip KoboldCPP.")
    p.add_argument(
        "--skip-ffmpeg",
        action="store_true",
        help="Skip ffmpeg/ffprobe ffmpeg-static binaries.",
    )
    p.add_argument("--skip-rvc", action="store_true", help="Skip RVC HF download.")
    p.add_argument(
        "--rvc-revision", default=None, help="HF revision for lj1995/VoiceConversionWebUI."
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = _project_root()

    if args.skip_kobold:
        os.environ["KOBOLDCPP_SKIP"] = "1"

    if args.skip_rvc:
        os.environ["RVC_SKIP"] = "1"

    download_koboldcpp(project_root=root, force=args.force)
    if not args.skip_ffmpeg:
        download_ffmpeg_and_ffprobe(project_root=root, force=args.force)
    download_rvc_assets(project_root=root, force=args.force, revision=args.rvc_revision)

    print("bootstrap_runtime_deps.py finished.")


if __name__ == "__main__":
    main()
