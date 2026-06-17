#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Render an improved (P0-only) preview of the 声入诗境 series to review/.

This does NOT touch submission/. It reuses the typesetting helpers from
build_competition_package and overrides only the three P0 changes:
  1. Weaker right-side paper wash  -> let AIGC detail show through.
  2. Per-work red-muting strength  -> recover peach / maple / amber.
  3. Clean poster layout (main image + 5-thumb grid) instead of blurred blending.
"""

from __future__ import print_function

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

import build_competition_package as bcp

ROOT = bcp.ROOT
REVIEW_DIR = ROOT / "review"
REVIEW_DIR.mkdir(exist_ok=True)

# Per-work red muting strength. Warm poems keep their color; cool ones stay muted.
RED_STRENGTH = {
    "01": 0.08,  # 春晓 桃粉 - 几乎不压，保留粉
    "02": 0.14,  # 枫桥夜泊 枫锈 - 轻压
    "03": 0.62,  # 早发白帝城 雾金/石青 - 保持
    "04": 0.62,  # 鹿柴 苔绿/墨黑 - 保持
    "05": 0.10,  # 夜雨寄北 琥珀/枫褐 - 轻压
}

# Per-work color saturation factor. Warm poems get a boost, cool poems stay neutral.
COLOR_FACTOR = {
    "01": 1.16,  # 春晓 提桃粉豆青
    "02": 1.08,  # 枫桥夜泊 提枫锈
    "03": 0.86,  # 白帝城
    "04": 0.84,  # 鹿柴
    "05": 1.10,  # 夜雨 提琥珀
}

WORK_SIZE = bcp.WORK_SIZE
A3_SIZE = bcp.A3_SIZE


def add_right_paper_wash_soft(image):
    """Much weaker paper wash: alpha ceiling ~70 (was ~203). Lets AIGC show."""
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pixels = overlay.load()
    start = int(image.width * 0.72)  # also start further right
    for x in range(start, image.width):
        progress = (x - start) / float(max(1, image.width - start))
        alpha = int(4 + 66 * (progress ** 0.7))
        for y in range(image.height):
            pixels[x, y] = (245, 239, 224, alpha)
    return Image.alpha_composite(image.convert("RGBA"), overlay)


def compose_work_refined(item):
    source_path = bcp.SOURCE_DIR / item["source"]
    base = bcp.cover_resize(Image.open(str(source_path)).convert("RGB"), WORK_SIZE)
    # gentle contrast lift; warm pieces get a bit more to pop
    contrast = 1.08 if item["index"] in ("01", "02", "05") else 1.04
    base = ImageEnhance.Contrast(base).enhance(contrast)
    base = ImageEnhance.Color(base).enhance(COLOR_FACTOR[item["index"]])
    base = bcp.mute_warm_reds(base, strength=RED_STRENGTH[item["index"]])
    canvas = add_right_paper_wash_soft(base)
    draw = ImageDraw.Draw(canvas)

    title_font = bcp.load_font(bcp.CALLIGRAPHY_FONT, 88)
    body_font = bcp.load_font(bcp.CALLIGRAPHY_FONT, 47)
    meta_font = bcp.load_font(bcp.TEXT_FONT, 28)

    ink = (28, 27, 24, 244)
    muted = (75, 68, 58, 220)
    mark_colors = {
        "鸟鸣": (92, 105, 88, 148),
        "钟声": (122, 104, 73, 148),
        "猿啼": (72, 84, 91, 148),
        "人语回响": (77, 91, 82, 148),
        "夜雨": (68, 86, 99, 148),
    }

    title_x = 1275
    title_end = bcp.draw_vertical(draw, item["title"], title_x, 170, title_font, ink, gap=14)
    author = "〔{}〕{}".format(item["dynasty"], item["author"])
    bcp.draw_vertical(draw, author, 1178, title_end + 64, meta_font, muted, gap=8)
    bcp.draw_soundscape_mark(
        canvas,
        (1102, 184),
        78,
        mark_colors.get(item["sound"], (88, 91, 80, 145)),
        width=2,
    )
    bcp.draw_vertical_clauses(
        draw,
        item["poem"],
        start_x=1055,
        start_y=360,
        font=body_font,
        fill=ink,
        col_gap=72,
    )
    return canvas.convert("RGB")


def create_a3_poster_grid(work_paths):
    """Clean poster: top main image band + 5-thumbnail strip + title."""
    canvas = Image.new("RGBA", A3_SIZE, (244, 239, 226, 255))

    # --- Main image: a full-width band using the Gorge echo (03) as hero ---
    hero = bcp.cover_resize(
        Image.open(str(bcp.SOURCE_DIR / "03_gorge_echo.png")).convert("RGB"),
        (A3_SIZE[0], int(A3_SIZE[1] * 0.66)),
    )
    hero = ImageEnhance.Contrast(hero).enhance(1.02)
    hero = ImageEnhance.Color(hero).enhance(0.92)
    hero = bcp.mute_warm_reds(hero, strength=0.55).convert("RGBA")
    canvas.paste(hero, (0, 0))

    ink = (28, 26, 23, 255)
    muted = (82, 68, 52, 240)
    title_font = bcp.load_font(bcp.CALLIGRAPHY_FONT, 215)
    subtitle_font = bcp.load_font(bcp.TEXT_FONT, 56)
    label_font = bcp.load_font(bcp.TEXT_FONT, 40)
    number_font = bcp.load_font(bcp.LATIN_FONT, 34)

    draw = ImageDraw.Draw(canvas)
    # Title at top-right, vertical
    bcp.draw_vertical(draw, bcp.SERIES_TITLE, 3140, 360, title_font, ink, gap=22)
    bcp.draw_vertical(
        draw, "让不可见的声音穿过五重诗境", 2820, 440, subtitle_font, muted, gap=12
    )
    bcp.draw_soundscape_mark(canvas, (3120, 2400), 165, (75, 84, 79, 90), width=3)

    # --- Lower third: cream panel with 5 thumbnails in a row ---
    band_top = int(A3_SIZE[1] * 0.66)
    band_h = A3_SIZE[1] - band_top
    band = Image.new("RGBA", (A3_SIZE[0], band_h), (244, 239, 226, 255))
    canvas = Image.alpha_composite(canvas, Image.new("RGBA", A3_SIZE, (0, 0, 0, 0)))
    # paste cream band
    canvas.paste(band, (0, band_top))

    n = len(work_paths)
    margin_x = 180
    gap = 70
    thumb_w = (A3_SIZE[0] - 2 * margin_x - (n - 1) * gap) // n
    thumb_h = int(thumb_w * 2160 / 1440)
    thumb_y = band_top + 200
    draw = ImageDraw.Draw(canvas)

    for i, wp in enumerate(work_paths):
        x = margin_x + i * (thumb_w + gap)
        thumb = bcp.fit_resize(Image.open(str(wp)).convert("RGB"), (thumb_w, thumb_h))
        canvas.paste(thumb, (x, thumb_y))
        bcp.draw_rect_outline(draw, (x, thumb_y, x + thumb_w, thumb_y + thumb_h), (118, 94, 67), width=3)
        # label below
        item = bcp.SERIES[i]
        draw.text((x, thumb_y + thumb_h + 28), "{:02d}".format(i + 1), font=number_font, fill=(104, 105, 88))
        bcp.draw_vertical(draw, item["title"], x + thumb_w - 55, thumb_y + thumb_h + 30, label_font, ink, gap=6)

    # footer note
    footer_font = bcp.load_font(bcp.TEXT_FONT, 32)
    draw.text(
        (margin_x, A3_SIZE[1] - 90),
        "鸟鸣 · 钟声 · 猿啼 · 人语回响 · 夜雨",
        font=footer_font,
        fill=muted,
    )
    return canvas.convert("RGB")


def diff_heatmap(before, after, gain=4):
    """Amplify the absolute pixel difference `gain`x so changes are visible."""
    from PIL import ImageChops

    d = ImageChops.difference(before.convert("RGB"), after.convert("RGB"))
    px = d.load()
    for y in range(d.height):
        for x in range(d.width):
            r, g, b = px[x, y]
            px[x, y] = (
                min(255, r * gain),
                min(255, g * gain),
                min(255, b * gain),
            )
    return d


def side_by_side(before, after, path):
    """Place before/after horizontally with a divider."""
    h = before.height
    gap = 24
    canvas = Image.new("RGB", (before.width + after.width + gap, h), (30, 28, 25))
    canvas.paste(before, (0, 0))
    canvas.paste(after, (before.width + gap, 0))
    canvas.save(str(path), "JPEG", quality=92, optimize=True, dpi=(150, 150))


def downscale(img, max_h=1600):
    if img.height > max_h:
        w = int(img.width * max_h / img.height)
        return img.resize((w, max_h), Image.LANCZOS)
    return img


def main():
    print("Rendering refined works ...")
    refined = []
    for item in bcp.SERIES:
        img = compose_work_refined(item)
        refined.append(img)
        out = REVIEW_DIR / "refined_{}_{}.jpg".format(item["index"], item["title"])
        img.save(str(out), "JPEG", quality=94, optimize=True, dpi=(300, 300))
        print("  ->", out.name)

    print("Rendering before/after comparisons ...")
    work_paths = [bcp.WORKS_DIR / "{}_{}.jpg".format(it["index"], it["title"]) for it in bcp.SERIES]
    for i, (before_path, after) in enumerate(zip(work_paths, refined), 1):
        before = Image.open(str(before_path)).convert("RGB")
        side_by_side(downscale(before), downscale(after), REVIEW_DIR / "cmp_{:02d}.jpg".format(i))
        # amplified difference map so the change is visible at a glance
        hm = diff_heatmap(downscale(before), downscale(after), gain=4)
        hm.save(str(REVIEW_DIR / "diff_{:02d}.jpg".format(i)), "JPEG", quality=90)
        print("  -> cmp_{:02d}.jpg  +  diff_{:02d}.jpg".format(i, i))

    print("Rendering refined A3 poster (grid) ...")
    # save full-res refined works to temp list for grid
    refined_paths = []
    for item, img in zip(bcp.SERIES, refined):
        p = REVIEW_DIR / "_tmp_refined_{}.jpg".format(item["index"])
        img.save(str(p), "JPEG", quality=95)
        refined_paths.append(p)
    poster = create_a3_poster_grid(refined_paths)
    poster.save(str(REVIEW_DIR / "refined_a3_poster.jpg"), "JPEG", quality=92, optimize=True, dpi=(300, 300))
    print("  -> refined_a3_poster.jpg")

    # poster before/after (downscaled for viewing)
    before_poster = Image.open(str(bcp.A3_PATH)).convert("RGB")
    side_by_side(downscale(before_poster, 1300), downscale(poster, 1300), REVIEW_DIR / "cmp_poster.jpg")
    print("  -> cmp_poster.jpg")

    # cleanup temp
    for p in refined_paths:
        p.unlink()
    print("Done. See:", REVIEW_DIR)


if __name__ == "__main__":
    main()
