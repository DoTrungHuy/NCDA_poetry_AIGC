#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NCDA 提交前合规检查脚本。

针对 2026 第14届未来设计师 NCDA 非命题赛道 1-L1 AIGC-图片类，检查：
1. works 目录是否至少有 5 张 JPG 系列图；
2. 每张 JPG 是否不超过 5MB；
3. A3 宣传海报是否为 3508x4961、300dpi、JPG 且不超过 5MB；
4. 创作过程 PDF、宣讲视频、平台文案与提交清单是否存在；
5. 视频是否为可读取的 MP4，且不超过 3 分钟和 300MB；
6. 文件名中是否明显包含作者、学校等匿名评审不建议出现的信息。

注意：脚本只能检查文件结构与尺寸，不能替代人工审查画面内容。
"""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from PIL import Image

MAX_JPG_MB = 5
MAX_VIDEO_MB = 300
MAX_VIDEO_SECONDS = 180
A3_SIZE = (3508, 4961)  # 297mm x 420mm at 300dpi
A3_TOLERANCE = 80


def size_mb(path: Path) -> float:
    return path.stat().st_size / 1024 / 1024


def list_images(directory: Path, suffixes: Iterable[str]) -> List[Path]:
    if not directory.exists():
        return []
    suffixes = tuple(s.lower() for s in suffixes)
    return sorted([p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in suffixes])


def is_near_a3_vertical(path: Path) -> Tuple[bool, str]:
    try:
        with Image.open(path) as img:
            w, h = img.size
            dpi = img.info.get("dpi", None)
    except Exception as exc:
        return False, f"无法读取图片：{exc}"

    size_ok = abs(w - A3_SIZE[0]) <= A3_TOLERANCE and abs(h - A3_SIZE[1]) <= A3_TOLERANCE
    vertical_ok = h > w
    dpi_ok = False
    dpi_note = "，DPI=缺失"
    if dpi and len(dpi) >= 2:
        dpi_ok = abs(dpi[0] - 300) <= 5 and abs(dpi[1] - 300) <= 5
        dpi_note = f"，DPI=({dpi[0]:.1f}, {dpi[1]:.1f})"
    return size_ok and vertical_ok and dpi_ok, f"尺寸={w}x{h}{dpi_note}"


def check_forbidden_names(paths: List[Path], forbidden_terms: List[str]) -> List[str]:
    warnings = []
    if not forbidden_terms:
        return warnings
    for path in paths:
        name = path.name.lower()
        for term in forbidden_terms:
            t = term.strip().lower()
            if t and t in name:
                warnings.append(f"文件名可能包含匿名评审不建议出现的信息：{path}")
    return warnings


def detect_layout(root: Path) -> Dict[str, Optional[Path]]:
    if (root / "a3_poster.jpg").exists():
        return {
            "works_dir": root / "works",
            "a3_path": root / "a3_poster.jpg",
            "process_pdf": root / "process" / "creation_process.pdf",
            "platform_copy": root / "PLATFORM_COPY.md",
            "video_path": root / "video" / "声入诗境_宣讲视频.mp4",
            "video_script": root / "video" / "narration_script.md",
            "manifest": root / "submission_manifest.json",
        }
    return {
        "works_dir": root / "works",
        "a3_path": next(iter(list_images(root / "a3_posters", [".jpg", ".jpeg"])), None),
        "process_pdf": root / "process" / "creation_process.pdf",
        "platform_copy": root / "process_report.md",
        "video_path": next(iter(list_images(root / "video", [".mp4"])), None),
        "video_script": None,
        "manifest": root / "submission_manifest.json",
    }


def probe_video(path: Path) -> Tuple[bool, str]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return False, "未找到 ffprobe，无法验证视频编码和时长"
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration,size:stream=codec_name,codec_type,width,height",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        duration = float(payload.get("format", {}).get("duration", 0))
        streams = payload.get("streams", [])
        video_stream = next((item for item in streams if item.get("codec_type") == "video"), {})
        audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), {})
        codec = video_stream.get("codec_name", "unknown")
        audio_codec = audio_stream.get("codec_name", "missing")
        width = video_stream.get("width", 0)
        height = video_stream.get("height", 0)
        ok = (
            0 < duration <= MAX_VIDEO_SECONDS
            and codec == "h264"
            and audio_codec == "aac"
            and width == 1920
            and height == 1080
        )
        return ok, (
            f"时长={duration:.1f}s，视频编码={codec}，音频编码={audio_codec}，"
            f"尺寸={width}x{height}"
        )
    except (OSError, subprocess.CalledProcessError, ValueError, json.JSONDecodeError) as exc:
        return False, f"无法读取视频：{exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="NCDA AIGC 图片类提交前检查")
    parser.add_argument("--dir", default="submission", help="提交包目录，默认 submission")
    parser.add_argument(
        "--forbidden",
        nargs="*",
        default=[],
        help="需要在文件名中规避的作者、学校、指导教师等关键词，例如 --forbidden 张三 某某大学"
    )
    args = parser.parse_args()

    root = Path(args.dir)
    layout = detect_layout(root)
    works_dir = layout["works_dir"]
    a3_path = layout["a3_path"]
    process_pdf = layout["process_pdf"]
    platform_copy = layout["platform_copy"]
    video_path = layout["video_path"]
    video_script = layout["video_script"]
    manifest = layout["manifest"]

    errors: List[str] = []
    warnings: List[str] = []

    print("=" * 72)
    print("NCDA 1-L1 AIGC-图片类提交前检查")
    print(f"检查目录：{root.resolve()}")
    print("=" * 72)

    works = list_images(works_dir, [".jpg", ".jpeg"])
    if len(works) < 5:
        errors.append(f"作品图不足 5 张：当前 {len(works)} 张，NCDA AIGC-图片类要求 5 张或以上成系列套图。")
    else:
        print(f"[OK] 作品图数量：{len(works)} 张")

    for img_path in works:
        mb = size_mb(img_path)
        if mb > MAX_JPG_MB:
            errors.append(f"作品图超过 5MB：{img_path} ({mb:.2f}MB)")
        else:
            print(f"[OK] 作品图大小：{img_path.name} ({mb:.2f}MB)")

    a3_images = [a3_path] if a3_path and a3_path.exists() else []
    if not a3_images:
        errors.append("未找到 A3 宣传海报。")
    else:
        print(f"[OK] A3 宣传海报数量：{len(a3_images)} 张")
        for poster in a3_images:
            ok, detail = is_near_a3_vertical(poster)
            mb = size_mb(poster)
            if not ok:
                warnings.append(f"A3 海报尺寸可能不符合 297mm×420mm 300dpi：{poster}，{detail}")
            if mb > MAX_JPG_MB:
                errors.append(f"A3 宣传海报超过 5MB：{poster} ({mb:.2f}MB)")
            print(f"[INFO] A3 海报：{poster.name}，{detail}，{mb:.2f}MB")

    if not process_pdf or not process_pdf.exists() or process_pdf.stat().st_size == 0:
        errors.append("缺少有效的创作过程 PDF。")
    else:
        print(f"[OK] 创作过程 PDF：{process_pdf.name} ({size_mb(process_pdf):.2f}MB)")

    if not platform_copy or not platform_copy.exists():
        errors.append("缺少平台投稿文案。")
    else:
        print(f"[OK] 平台投稿文案：{platform_copy.name}")

    if video_script and not video_script.exists():
        errors.append("缺少宣讲视频文稿。")
    elif video_script:
        print(f"[OK] 宣讲视频文稿：{video_script.name}")

    if not video_path or not video_path.exists() or video_path.stat().st_size == 0:
        errors.append("缺少有效的 MP4 宣讲视频。")
    else:
        video_mb = size_mb(video_path)
        video_ok, video_detail = probe_video(video_path)
        if video_mb > MAX_VIDEO_MB:
            errors.append(f"宣讲视频超过 300MB：{video_path} ({video_mb:.2f}MB)")
        if not video_ok:
            errors.append(f"宣讲视频规格不符合要求：{video_detail}")
        else:
            print(f"[OK] 宣讲视频：{video_detail}，{video_mb:.2f}MB")

    if not manifest or not manifest.exists():
        errors.append("缺少 submission_manifest.json 提交清单。")
    else:
        try:
            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            deliverables = manifest_data.get("deliverables", [])
            missing = [
                item.get("path", "")
                for item in deliverables
                if not (Path(__file__).resolve().parent / item.get("path", "")).exists()
            ]
            if missing:
                errors.append("提交清单引用了不存在的文件：" + "，".join(missing))
            else:
                print(f"[OK] 提交清单：{len(deliverables)} 个正式文件")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"提交清单无法读取：{exc}")

    checked_paths = works + a3_images
    for optional_path in (process_pdf, platform_copy, video_path, video_script, manifest):
        if optional_path and optional_path.exists():
            checked_paths.append(optional_path)
    warnings.extend(check_forbidden_names(checked_paths, args.forbidden))

    if warnings:
        print("\n[WARN] 需要人工确认：")
        for item in warnings:
            print(f"- {item}")

    if errors:
        print("\n[FAIL] 存在必须修正的问题：")
        for item in errors:
            print(f"- {item}")
        return 1

    print("\n[PASS] 文件结构与硬性规格初步符合 NCDA AIGC-图片类提交要求。")
    print("仍需人工检查：画面中不要出现作者姓名、指导教师姓名、学校名称、其他赛事 Logo 或无关标识。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
