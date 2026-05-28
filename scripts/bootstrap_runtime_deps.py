"""
Download heavyweight runtime binaries and minimal RVC weights for VC inference
(Hubert content encoder + RMVPE pitch; see `VC.vc_inference` / `Pipeline.get_f0`).

Layout:
  bin/whisper-server[.exe] (+ bundled DLLs on Windows)
  bin/llama-server[.exe] (+ bundled libs; shared with ffmpeg-static)
  models/rvc/base/hubert/hubert_base.pt
  models/rvc/base/rmvpe/rmvpe.pt
  models/rvc/weights/   — place your *.pth voice checkpoints here (see weight_root)

Environment (optional):
  WHISPERCPP_VARIANT   cuda | cpu  (default: cuda on Windows x64 when available, else cpu)
  WHISPERCPP_ASSET_NAME  Full GitHub release asset filename override
  WHISPERCPP_SKIP      set to 1 to skip whisper.cpp server download
  LLAMACPP_VARIANT     cuda | cpu | rocm | vulkan  (default: cuda on Windows x64 when available)
  LLAMACPP_ASSET_NAME  Full GitHub release asset filename override
  LLAMACPP_SKIP        set to 1 to skip llama.cpp server download
  RVC_SKIP             set to 1 to skip RVC HF download
  RVC_ASSETS_REVISION  Hugging Face revision for lj1995/VoiceConversionWebUI (default: main)

See:
  whisper.cpp https://github.com/ggml-org/whisper.cpp/releases/tag/v1.8.4
  llama.cpp   https://github.com/ggml-org/llama.cpp/releases/tag/b9381
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import stat
import sys
import tarfile
import tempfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import requests

WHISPERCPP_TAG = "v1.8.4"
WHISPERCPP_RELEASE_BASE = (
    f"https://github.com/ggml-org/whisper.cpp/releases/download/{WHISPERCPP_TAG}"
)
LLAMACPP_TAG = "b9381"
LLAMACPP_RELEASE_BASE = f"https://github.com/ggml-org/llama.cpp/releases/download/{LLAMACPP_TAG}"

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


@dataclass(frozen=True)
class _ReleaseAsset:
    filename: str
    archive: Literal["zip", "tar.gz"]
    extract_mode: Literal["flat", "release_dir"]


def _server_binary_name(system: str, base: str) -> str:
    return f"{base}.exe" if system == "Windows" else base


def _normalize_variant(variant: str, allowed: set[str], default: str) -> str:
    v = variant.lower().strip()
    if v not in allowed:
        print(f"Unknown variant {variant!r}; using {default}.")
        return default
    return v


def _resolve_whisper_asset(machine: str, system: str, variant: str) -> _ReleaseAsset | None:
    override = os.environ.get("WHISPERCPP_ASSET_NAME", "").strip()
    if override:
        archive: Literal["zip", "tar.gz"] = (
            "tar.gz" if override.endswith(".tar.gz") else "zip"
        )
        mode: Literal["flat", "release_dir"] = (
            "release_dir" if archive == "zip" and "bin" in override else "flat"
        )
        return _ReleaseAsset(override, archive, mode)

    m = machine.lower()
    v = _normalize_variant(variant, {"cuda", "cpu"}, "cuda")

    if system == "Windows":
        is_arm = os.environ.get("PROCESSOR_ARCHITECTURE", "").upper() == "ARM64" or "arm" in m
        if is_arm:
            print("  Windows ARM: whisper.cpp CUDA builds are x64-only; using cpu.")
            v = "cpu"
        if m not in {"x86_64", "amd64"} and not is_arm:
            print(f"ERROR: Unsupported Windows machine for whisper.cpp: {machine!r}", file=sys.stderr)
            return None
        if v == "cuda":
            return _ReleaseAsset("whisper-cublas-12.4.0-bin-x64.zip", "zip", "release_dir")
        return _ReleaseAsset("whisper-bin-x64.zip", "zip", "release_dir")

    if system == "Linux":
        print(
            "ERROR: whisper.cpp v1.8.4 has no official Linux server binary in GitHub releases.\n"
            "  Set WHISPERCPP_ASSET_NAME to a compatible asset, or WHISPERCPP_SKIP=1 and install manually.\n"
            f"  Release index: https://github.com/ggml-org/whisper.cpp/releases/tag/{WHISPERCPP_TAG}",
            file=sys.stderr,
        )
        return None

    if system == "Darwin":
        print(
            "ERROR: whisper.cpp v1.8.4 macOS release ships an xcframework only (no whisper-server binary).\n"
            "  Set WHISPERCPP_SKIP=1 and install whisper-server manually, or set WHISPERCPP_ASSET_NAME.",
            file=sys.stderr,
        )
        return None

    print(f"ERROR: Unsupported OS for whisper.cpp bootstrap: {system!r}", file=sys.stderr)
    return None


def _resolve_llama_asset(machine: str, system: str, variant: str) -> _ReleaseAsset | None:
    override = os.environ.get("LLAMACPP_ASSET_NAME", "").strip()
    if override:
        archive: Literal["zip", "tar.gz"] = (
            "tar.gz" if override.endswith(".tar.gz") else "zip"
        )
        return _ReleaseAsset(override, archive, "flat")

    m = machine.lower()
    v = _normalize_variant(variant, {"cuda", "cpu", "rocm", "vulkan"}, "cuda")
    tag = LLAMACPP_TAG

    if system == "Windows":
        is_arm = os.environ.get("PROCESSOR_ARCHITECTURE", "").upper() == "ARM64" or "arm" in m
        if is_arm:
            if v == "cuda":
                print("  Windows ARM: llama.cpp CUDA builds are x64-only; using cpu arm64.")
                v = "cpu"
            return _ReleaseAsset(f"llama-{tag}-bin-win-cpu-arm64.zip", "zip", "flat")
        if m not in {"x86_64", "amd64"}:
            print(f"ERROR: Unsupported Windows machine for llama.cpp: {machine!r}", file=sys.stderr)
            return None
        if v == "cuda":
            return _ReleaseAsset(f"llama-{tag}-bin-win-cuda-12.4-x64.zip", "zip", "flat")
        if v == "vulkan":
            return _ReleaseAsset(f"llama-{tag}-bin-win-vulkan-x64.zip", "zip", "flat")
        return _ReleaseAsset(f"llama-{tag}-bin-win-cpu-x64.zip", "zip", "flat")

    if system == "Linux":
        if m in {"x86_64", "amd64"}:
            if v == "cuda":
                print(
                    "  Linux x64: no official CUDA zip in this release; using ubuntu cpu build.",
                    file=sys.stderr,
                )
                v = "cpu"
            if v == "rocm":
                return _ReleaseAsset(f"llama-{tag}-bin-ubuntu-rocm-7.2-x64.tar.gz", "tar.gz", "flat")
            if v == "vulkan":
                return _ReleaseAsset(
                    f"llama-{tag}-bin-ubuntu-vulkan-x64.tar.gz", "tar.gz", "flat"
                )
            return _ReleaseAsset(f"llama-{tag}-bin-ubuntu-x64.tar.gz", "tar.gz", "flat")
        if m in {"aarch64", "arm64"}:
            if v == "vulkan":
                return _ReleaseAsset(
                    f"llama-{tag}-bin-ubuntu-vulkan-arm64.tar.gz", "tar.gz", "flat"
                )
            return _ReleaseAsset(f"llama-{tag}-bin-ubuntu-arm64.tar.gz", "tar.gz", "flat")
        print(f"ERROR: Unsupported Linux machine for llama.cpp: {machine!r}", file=sys.stderr)
        return None

    if system == "Darwin":
        if m in {"aarch64", "arm64"}:
            return _ReleaseAsset(f"llama-{tag}-bin-macos-arm64.tar.gz", "tar.gz", "flat")
        if m == "x86_64":
            return _ReleaseAsset(f"llama-{tag}-bin-macos-x64.tar.gz", "tar.gz", "flat")
        print(f"ERROR: Unsupported macOS machine for llama.cpp: {machine!r}", file=sys.stderr)
        return None

    print(f"ERROR: Unsupported OS for llama.cpp bootstrap: {system!r}", file=sys.stderr)
    return None


def _marker_stamp(tag: str, variant: str, asset: _ReleaseAsset) -> str:
    return f"{tag}\n{variant}\n{asset.filename}\n"


def _installed_marker_matches(marker: Path, stamp: str, server_bin: Path, *, force: bool) -> bool:
    if force or not server_bin.is_file():
        return False
    if not marker.is_file():
        return False
    return marker.read_text(encoding="utf-8") == stamp


def _chmod_executable(path: Path) -> None:
    mode = path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    path.chmod(mode)


def _extract_zip(archive: Path, dest_dir: Path, *, extract_mode: Literal["flat", "release_dir"]) -> None:
    prefix = "Release/" if extract_mode == "release_dir" else ""
    with zipfile.ZipFile(archive) as zf:
        for member in zf.namelist():
            if prefix and not member.startswith(prefix):
                continue
            rel = member[len(prefix) :] if prefix else member
            if not rel or rel.endswith("/"):
                continue
            target = dest_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def _extract_tar_gz(archive: Path, dest_dir: Path) -> None:
    with tarfile.open(archive, "r:gz") as tf:
        tf.extractall(dest_dir, filter="data")


def _install_release_tree(staging_dir: Path, dest_dir: Path, *, merge: bool = False) -> None:
    if not merge and dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    children = list(staging_dir.iterdir())
    if len(children) == 1 and children[0].is_dir():
        source_root = children[0]
    else:
        source_root = staging_dir
    for item in source_root.iterdir():
        target = dest_dir / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=merge)
        else:
            shutil.copy2(item, target)


def _download_release_asset(
    *,
    label: str,
    tag: str,
    release_base: str,
    out_dir: Path,
    asset: _ReleaseAsset,
    server_name: str,
    variant: str,
    force: bool,
    resolve_fallback: Callable[[str, str, str], _ReleaseAsset | None] | None = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    server_bin = out_dir / server_name
    marker = out_dir / f".{label}-version"
    stamp = _marker_stamp(tag, variant, asset)

    if _installed_marker_matches(marker, stamp, server_bin, force=force):
        print(f"{label} {tag} ({asset.filename}) already present at {server_bin}, skipping.")
        return

    candidates = [asset]
    if resolve_fallback and variant == "cuda":
        fallback = resolve_fallback(platform.machine(), platform.system(), "cpu")
        if fallback and fallback.filename != asset.filename:
            candidates.append(fallback)

    last_error: Exception | None = None
    for candidate in candidates:
        if candidate is not asset:
            print(f"  Falling back to {candidate.filename} ...")
            stamp = _marker_stamp(tag, "cpu", candidate)

        url = f"{release_base}/{candidate.filename}"
        print(f"Downloading {label} {tag}: {candidate.filename} ...")

        with tempfile.TemporaryDirectory(prefix=f"{label}_") as tmp_s:
            tmp = Path(tmp_s)
            archive_path = tmp / candidate.filename
            try:
                _download_url(url, archive_path)
            except requests.HTTPError as e:
                last_error = e
                if candidate is not candidates[-1]:
                    continue
                raise

            extract_root = tmp / "extract"
            extract_root.mkdir()
            if candidate.archive == "zip":
                _extract_zip(archive_path, extract_root, extract_mode=candidate.extract_mode)
            else:
                _extract_tar_gz(archive_path, extract_root)

            _install_release_tree(extract_root, out_dir, merge=out_dir.name == "bin")

        if not server_bin.is_file():
            raise SystemExit(
                f"{label} install incomplete: expected {server_bin} after extracting {candidate.filename}"
            )

        if platform.system() != "Windows":
            _chmod_executable(server_bin)

        marker.write_text(stamp, encoding="utf-8")
        print(f"  -> {server_bin}")
        return

    if last_error:
        raise last_error


def download_whispercpp(*, project_root: Path, force: bool) -> None:
    if os.environ.get("WHISPERCPP_SKIP") == "1":
        print("whisper.cpp download skipped (WHISPERCPP_SKIP=1).")
        return

    system = platform.system()
    machine = platform.machine()
    variant = os.environ.get("WHISPERCPP_VARIANT", "cuda")
    asset = _resolve_whisper_asset(machine, system, variant)
    if asset is None:
        raise SystemExit(1)

    out_dir = project_root / "bin"
    server_name = _server_binary_name(system, "whisper-server")

    def _cpu_fallback(m: str, s: str, _v: str) -> _ReleaseAsset | None:
        return _resolve_whisper_asset(m, s, "cpu")

    _download_release_asset(
        label="whispercpp",
        tag=WHISPERCPP_TAG,
        release_base=WHISPERCPP_RELEASE_BASE,
        out_dir=out_dir,
        asset=asset,
        server_name=server_name,
        variant=variant,
        force=force,
        resolve_fallback=_cpu_fallback if variant == "cuda" else None,
    )


def download_llamacpp(*, project_root: Path, force: bool) -> None:
    if os.environ.get("LLAMACPP_SKIP") == "1":
        print("llama.cpp download skipped (LLAMACPP_SKIP=1).")
        return

    system = platform.system()
    machine = platform.machine()
    variant = os.environ.get("LLAMACPP_VARIANT", "cuda")
    asset = _resolve_llama_asset(machine, system, variant)
    if asset is None:
        raise SystemExit(1)

    out_dir = project_root / "bin"
    server_name = _server_binary_name(system, "llama-server")

    def _cpu_fallback(m: str, s: str, _v: str) -> _ReleaseAsset | None:
        return _resolve_llama_asset(m, s, "cpu")

    _download_release_asset(
        label="llamacpp",
        tag=LLAMACPP_TAG,
        release_base=LLAMACPP_RELEASE_BASE,
        out_dir=out_dir,
        asset=asset,
        server_name=server_name,
        variant=variant,
        force=force,
        resolve_fallback=_cpu_fallback if variant == "cuda" else None,
    )


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
        print(
            f"ERROR: Unsupported Linux machine type for ffmpeg-static: {machine!r}", file=sys.stderr
        )
        return None

    if sys_norm == "Darwin":
        if m in {"arm64", "aarch64"}:
            return ("ffmpeg-darwin-arm64", "ffprobe-darwin-arm64")
        if m in {"x86_64"}:
            return ("ffmpeg-darwin-x64", "ffprobe-darwin-x64")
        print(
            f"ERROR: Unsupported macOS machine type for ffmpeg-static: {machine!r}", file=sys.stderr
        )
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

    (bin_dir / ".ffmpeg-static-version").write_text(FFMPEG_STATIC_TAG + "\n", encoding="utf-8")

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
        description="Download whisper.cpp, llama.cpp, ffmpeg/ffprobe, and RVC runtime assets."
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if version markers indicate an existing install.",
    )
    p.add_argument("--skip-whispercpp", action="store_true", help="Skip whisper.cpp server.")
    p.add_argument("--skip-llamacpp", action="store_true", help="Skip llama.cpp server.")
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

    if args.skip_whispercpp:
        os.environ["WHISPERCPP_SKIP"] = "1"
    if args.skip_llamacpp:
        os.environ["LLAMACPP_SKIP"] = "1"
    if args.skip_rvc:
        os.environ["RVC_SKIP"] = "1"

    download_whispercpp(project_root=root, force=args.force)
    download_llamacpp(project_root=root, force=args.force)
    if not args.skip_ffmpeg:
        download_ffmpeg_and_ffprobe(project_root=root, force=args.force)
    download_rvc_assets(project_root=root, force=args.force, revision=args.rvc_revision)

    print("bootstrap_runtime_deps.py finished.")


if __name__ == "__main__":
    main()
