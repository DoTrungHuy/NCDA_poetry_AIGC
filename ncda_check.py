#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NCDA 提交前合规检查脚本。

针对 2026 第14届未来设计师 NCDA 非命题赛道 1L AIGC-图片类，检查：
1. works 目录是否至少有 5 张 JPG 系列图；
2. 每张 JPG 是否不超过 5MB；
3. a3_posters 目录中的宣传海报是否为 A3 竖版 300dpi 附近尺寸；
4. process_report.md 与过程 JSON 是否存在；
5. 文件名中是否明显包含作者、学校等匿名评审不建议出现的信息。

注意：脚本只能检查文件结构与尺寸，不能替代人工审查画面内容。
"""

import argparse
import os
from pathlib import Path
from typing import Iterable, List, Tuple

from PIL import Image

MAX_JPG_MB = 5
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
    dpi_note = ""
    if dpi:
        dpi_note = f"，DPI={dpi}"
    return size_ok and vertical_ok, f"尺寸={w}x{h}{dpi_note}"


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


def main() -> int:
    parser = argparse.ArgumentParser(description="NCDA AIGC 图片类提交前检查")
    parser.add_argument("--dir", default="outputs/ncda_series", help="系列输出目录，默认 outputs/ncda_series")
    parser.add_argument(
        "--forbidden",
        nargs="*",
        default=[],
        help="需要在文件名中规避的作者、学校、指导教师等关键词，例如 --forbidden 张三 某某大学"
    )
    args = parser.parse_args()

    root = Path(args.dir)
    works_dir = root / "works"
    a3_dir = root / "a3_posters"
    process_dir = root / "process"
    process_report = root / "process_report.md"

    errors: List[str] = []
    warnings: List[str] = []

    print("=" * 72)
    print("NCDA 1L AIGC-图片类提交前检查")
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

    a3_images = list_images(a3_dir, [".jpg", ".jpeg"])
    if not a3_images:
        errors.append("未找到 A3 宣传海报：请检查 a3_posters 目录。")
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

    json_logs = list_images(process_dir, [".json"])
    if not process_report.exists():
        errors.append("缺少 process_report.md：AIGC 赛项需要 PDF 形式的创作过程描述，可由该文件整理导出。")
    else:
        print(f"[OK] 创作过程报告草稿：{process_report}")

    if not json_logs:
        warnings.append("未找到过程 JSON 记录：建议保留提示词、模型、生成时间等过程证据。")
    else:
        print(f"[OK] 过程 JSON 记录：{len(json_logs)} 个")

    warnings.extend(check_forbidden_names(works + a3_images + json_logs + [process_report], args.forbidden))

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
