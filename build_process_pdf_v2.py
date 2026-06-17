#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rebuild the NCDA creation-process PDF with a polished process-book layout."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

import build_competition_package as bcp


ROOT = bcp.ROOT
SOURCE_DIR = bcp.SOURCE_DIR
SUBMISSION_DIR = bcp.SUBMISSION_DIR
WORKS_DIR = bcp.WORKS_DIR
A3_PATH = bcp.A3_PATH
PDF_PATH = SUBMISSION_DIR / "process" / "creation_process.pdf"
MANIFEST_PATH = SUBMISSION_DIR / "submission_manifest.json"

SERIES = bcp.SERIES
SERIES_TITLE = bcp.SERIES_TITLE
SERIES_SUBTITLE = bcp.SERIES_SUBTITLE
SERIES_STATEMENT = bcp.SERIES_STATEMENT

PDF_W, PDF_H = 1754, 2480
TOTAL_PAGES = 12

CALLIGRAPHY_FONT = bcp.CALLIGRAPHY_FONT
TEXT_FONT = bcp.TEXT_FONT
LATIN_FONT = bcp.LATIN_FONT
KAI_FONT = bcp.font_path(
    "C:/Windows/Fonts/simkai.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    CALLIGRAPHY_FONT,
)
BOLD_FONT = bcp.font_path(
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    TEXT_FONT,
)


# Muted ink-and-paper system with a few earthy accents.
PAPER = (244, 239, 226)
PAPER_DEEP = (236, 228, 209)
PAPER_LIGHT = (250, 247, 238)
INK = (31, 30, 27)
SOFT_INK = (71, 68, 60)
MUTED = (104, 92, 76)
HAIRLINE = (178, 153, 111)
OLIVE = (93, 101, 84)
MOSS = (88, 116, 99)
INDIGO = (62, 76, 92)
AMBER = (159, 127, 76)
RUST = (136, 81, 57)
NIGHT = (42, 48, 55)
WHITE = (255, 255, 255)


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


FONTS = {
    "title": load_font(CALLIGRAPHY_FONT, 190),
    "cover_sub": load_font(BOLD_FONT, 48),
    "h1": load_font(BOLD_FONT, 58),
    "h2": load_font(BOLD_FONT, 42),
    "h3": load_font(BOLD_FONT, 32),
    "body": load_font(TEXT_FONT, 31),
    "body_sm": load_font(TEXT_FONT, 25),
    "caption": load_font(TEXT_FONT, 21),
    "kai": load_font(KAI_FONT, 38),
    "kai_sm": load_font(KAI_FONT, 28),
    "latin": load_font(LATIN_FONT, 24),
    "latin_sm": load_font(LATIN_FONT, 18),
    "prompt": load_font(LATIN_FONT, 20),
}


def measure(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    return bcp.measure_text(draw, text, font)


def fit_resize(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
    return bcp.fit_resize(image, size)


def cover_resize(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
    return bcp.cover_resize(image, size)


def draw_soundscape_mark(
    image: Image.Image,
    xy: Tuple[int, int],
    size: int,
    color: Tuple[int, int, int, int],
    width: int = 3,
) -> None:
    bcp.draw_soundscape_mark(image, xy, size, color, width)


def rounded(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    radius: int = 8,
    fill: Tuple[int, int, int] | None = None,
    outline: Tuple[int, int, int] | None = None,
    width: int = 1,
) -> None:
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    else:
        draw.rectangle(box, fill=fill, outline=outline, width=width)


def alpha_box(
    image: Image.Image,
    box: Tuple[int, int, int, int],
    fill: Tuple[int, int, int],
    alpha: int,
    radius: int = 8,
    outline: Tuple[int, int, int] | None = None,
) -> None:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    if hasattr(odraw, "rounded_rectangle"):
        odraw.rounded_rectangle(box, radius=radius, fill=fill + (alpha,), outline=None)
    else:
        odraw.rectangle(box, fill=fill + (alpha,))
    image.alpha_composite(overlay)
    if outline:
        draw = ImageDraw.Draw(image)
        rounded(draw, box, radius=radius, outline=outline, width=1)


def page_base() -> Image.Image:
    base = Image.new("RGBA", (PDF_W, PDF_H), PAPER + (255,))
    noise = Image.effect_noise((PDF_W, PDF_H), 13).convert("L")
    noise = ImageOps.autocontrast(noise).point(lambda p: max(0, min(30, int((p - 112) * 0.17 + 12))))
    texture = Image.new("RGBA", (PDF_W, PDF_H), (120, 96, 63, 0))
    texture.putalpha(noise)
    return Image.alpha_composite(base, texture)


def save_pages(pages: Sequence[Image.Image], path: Path) -> None:
    os.makedirs(str(path.parent), exist_ok=True)
    rgb_pages = [page.convert("RGB") for page in pages]
    for page in rgb_pages:
        page.encoderinfo = {}
        page.encoderconfig = ()
    rgb_pages[0].save(
        str(path),
        "PDF",
        resolution=150.0,
        save_all=True,
        append_images=rgb_pages[1:],
    )


def draw_header(page: Image.Image, section: str, title: str, page_no: int) -> None:
    draw = ImageDraw.Draw(page)
    x0, x1 = 112, PDF_W - 112
    draw.text((x0, 86), section, font=FONTS["latin"], fill=AMBER)
    draw.text((x0 + 92, 76), title, font=FONTS["h2"], fill=INK)
    page_text = f"{page_no:02d} / {TOTAL_PAGES:02d}"
    pw, _ = measure(draw, page_text, FONTS["latin"])
    draw.text((x1 - pw, 88), page_text, font=FONTS["latin"], fill=MUTED)
    draw.line((x0, 165, x1, 165), fill=HAIRLINE, width=3)


def draw_footer(page: Image.Image, page_no: int) -> None:
    return


def wrap_chars(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int | None = None,
) -> List[str]:
    lines = bcp.wrap_text(draw, text, font, max_width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1].rstrip("，。；、 ") + "..."
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: Tuple[int, int],
    font: ImageFont.ImageFont,
    fill: Tuple[int, int, int],
    max_width: int,
    line_gap: int = 13,
    max_lines: int | None = None,
) -> int:
    x, y = xy
    for line in wrap_chars(draw, text, font, max_width, max_lines):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


def wrap_words(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int | None = None,
) -> List[str]:
    lines: List[str] = []
    current: List[str] = []
    for word in text.replace("\n", " ").split():
        candidate = " ".join(current + [word]) if current else word
        width, _ = measure(draw, candidate, font)
        if width <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .,;") + "..."
    return lines


def draw_word_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: Tuple[int, int],
    font: ImageFont.ImageFont,
    fill: Tuple[int, int, int],
    max_width: int,
    line_gap: int = 9,
    max_lines: int | None = None,
) -> int:
    x, y = xy
    for line in wrap_words(draw, text, font, max_width, max_lines):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


def section_label(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str, color: Tuple[int, int, int] = OLIVE) -> None:
    x, y = xy
    draw.text((x, y), text, font=FONTS["h3"], fill=color)
    draw.line((x, y + 48, x + 130, y + 48), fill=color, width=4)


def small_caps(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str, color: Tuple[int, int, int] = AMBER) -> None:
    draw.text(xy, text.upper(), font=FONTS["latin_sm"], fill=color)


def work_path(item: dict) -> Path:
    return WORKS_DIR / f"{item['index']}_{item['title']}.jpg"


def source_path(item: dict) -> Path:
    return SOURCE_DIR / item["source"]


def paste_image_with_outline(
    page: Image.Image,
    img: Image.Image,
    xy: Tuple[int, int],
    outline: Tuple[int, int, int] = HAIRLINE,
    width: int = 2,
) -> None:
    page.paste(img, xy)
    draw = ImageDraw.Draw(page)
    x, y = xy
    for offset in range(width):
        draw.rectangle(
            (x + offset, y + offset, x + img.width - offset, y + img.height - offset),
            outline=outline,
        )


def make_cover() -> Image.Image:
    page = page_base()
    poster = Image.open(str(A3_PATH)).convert("RGB")
    bg = cover_resize(poster, (PDF_W, PDF_H))
    bg = ImageEnhance.Color(bg).enhance(0.22)
    bg = ImageEnhance.Contrast(bg).enhance(0.83)
    bg = ImageEnhance.Brightness(bg).enhance(1.13).filter(ImageFilter.GaussianBlur(0.4))
    bg_rgba = bg.convert("RGBA")
    wash = Image.new("RGBA", (PDF_W, PDF_H), PAPER + (88,))
    page = Image.alpha_composite(bg_rgba, wash)

    overlay = Image.new("RGBA", (PDF_W, PDF_H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rectangle((0, 0, 730, PDF_H), fill=PAPER + (230,))
    odraw.rectangle((730, 0, 820, PDF_H), fill=PAPER + (92,))
    page = Image.alpha_composite(page, overlay)
    draw = ImageDraw.Draw(page)

    draw.line((96, 96, PDF_W - 96, 96), fill=HAIRLINE, width=3)
    draw.line((96, PDF_H - 96, PDF_W - 96, PDF_H - 96), fill=HAIRLINE, width=3)
    draw.line((96, 96, 96, PDF_H - 96), fill=HAIRLINE, width=3)
    draw.line((PDF_W - 96, 96, PDF_W - 96, PDF_H - 96), fill=HAIRLINE, width=3)
    draw_soundscape_mark(page, (150, 240), 184, OLIVE + (145,), width=4)

    title_y = 560
    for char in SERIES_TITLE:
        cw, _ = measure(draw, char, FONTS["title"])
        draw.text((280 - cw // 2, title_y), char, font=FONTS["title"], fill=INK)
        title_y += 238

    draw.text((142, 1580), SERIES_SUBTITLE, font=FONTS["cover_sub"], fill=SOFT_INK)
    draw.line((142, 1668, 540, 1668), fill=AMBER, width=5)
    draw_wrapped(draw, SERIES_STATEMENT, (142, 1732), FONTS["body"], INK, 435, line_gap=20, max_lines=5)
    return page


def make_contents() -> Image.Image:
    page = page_base()
    draw_header(page, "00", "文档结构", 2)
    draw = ImageDraw.Draw(page)

    draw.text((112, 255), "这份过程册回答三个问题", font=FONTS["h1"], fill=INK)
    summary = (
        "作品如何从古典诗词中的声音出发，经过 AIGC 底图生成、人工筛选、视觉后期与程序化排版，"
        "最终形成一组可提交的系列视觉作品。"
    )
    draw_wrapped(draw, summary, (112, 340), FONTS["body"], SOFT_INK, 1040, line_gap=17, max_lines=3)

    cards = [
        ("01", "为什么做", "选题、声音机制与诗词选择"),
        ("02", "怎么生成", "工具、Prompt 结构与底图证据"),
        ("03", "如何成品", "视觉系统、人工介入与提交检查"),
    ]
    card_y = 530
    card_w = 485
    for i, (num, title, body) in enumerate(cards):
        x = 112 + i * (card_w + 38)
        rounded(draw, (x, card_y, x + card_w, card_y + 260), radius=8, fill=PAPER_LIGHT, outline=(214, 197, 163), width=2)
        draw.text((x + 34, card_y + 32), num, font=FONTS["latin"], fill=AMBER)
        draw.text((x + 34, card_y + 78), title, font=FONTS["h2"], fill=INK)
        draw_wrapped(draw, body, (x + 34, card_y + 150), FONTS["body_sm"], MUTED, card_w - 68, line_gap=14, max_lines=2)

    contents = [
        ("封面", "作品题名与视觉基调", "01"),
        ("文档结构", "阅读路径与核心问题", "02"),
        ("选题与问题意识", "声音如何转译为空间", "03"),
        ("系列视觉系统", "色彩、字体、构图与印记", "04"),
        ("AIGC 工作流", "生成、筛选、后期与合规检查", "05"),
        ("Prompt 与底图证据", "四层结构和五张源图", "06"),
        ("作品详解", "五件作品逐页说明", "07-11"),
        ("原创声明与过程索引", "人工介入、版权与内容对应", "12"),
    ]
    y = 930
    draw.text((112, y), "目录", font=FONTS["h1"], fill=INK)
    y += 92
    for i, (title, desc, page_no) in enumerate(contents):
        x = 112 if i < 4 else 920
        cy = y + (i % 4) * 185
        draw.text((x, cy), f"{i + 1:02d}", font=FONTS["latin"], fill=AMBER)
        draw.text((x + 82, cy - 8), title, font=FONTS["h3"], fill=INK)
        draw_wrapped(draw, desc, (x + 82, cy + 47), FONTS["body_sm"], MUTED, 520, line_gap=8, max_lines=2)
        pw, _ = measure(draw, page_no, FONTS["latin"])
        draw.text((x + 650 - pw, cy + 5), page_no, font=FONTS["latin"], fill=OLIVE)
        draw.line((x + 82, cy + 105, x + 650, cy + 105), fill=(218, 204, 177), width=1)

    draw_soundscape_mark(page, (1320, 1900), 250, OLIVE + (68,), width=4)
    draw_footer(page, 2)
    return page


def make_concept() -> Image.Image:
    page = page_base()
    draw_header(page, "01", "选题与问题意识", 3)
    draw = ImageDraw.Draw(page)

    draw.text((112, 255), "从“声音”进入古诗，而不是复刻画面", font=FONTS["h1"], fill=INK)
    concept = (
        "古诗中的声音往往没有可见形体，却承担空间定位、情绪转折和时间推进。"
        "本系列把声音的扩散、回返、断续、叠加和消隐转化为构图规则，"
        "在传统水墨与当代数字绘景之间建立一套视觉语法。"
    )
    draw_wrapped(draw, concept, (112, 350), FONTS["body"], SOFT_INK, 1240, line_gap=20)

    axis_y = 620
    draw.line((170, axis_y, PDF_W - 170, axis_y), fill=HAIRLINE, width=4)
    nodes = [
        ("诗词文本", "语义与情绪"),
        ("声音机制", "传播方式"),
        ("视觉规则", "点线面结构"),
        ("成品系列", "统一但有差异"),
    ]
    for i, (title, subtitle) in enumerate(nodes):
        x = 170 + i * 470
        draw.ellipse((x - 38, axis_y - 38, x + 38, axis_y + 38), fill=[AMBER, OLIVE, INDIGO, RUST][i])
        draw.text((x - 16, axis_y - 18), str(i + 1), font=FONTS["latin"], fill=PAPER_LIGHT)
        tw, _ = measure(draw, title, FONTS["h3"])
        draw.text((x - tw // 2, axis_y + 80), title, font=FONTS["h3"], fill=INK)
        sw, _ = measure(draw, subtitle, FONTS["caption"])
        draw.text((x - sw // 2, axis_y + 128), subtitle, font=FONTS["caption"], fill=MUTED)

    draw.text((112, 900), "五种声音 / 五种空间机制", font=FONTS["h1"], fill=INK)
    grid_x, grid_y = 112, 1010
    cell_w, cell_h = 730, 205
    colors = [MOSS, AMBER, INDIGO, OLIVE, NIGHT]
    for i, item in enumerate(SERIES):
        x = grid_x + (i % 2) * (cell_w + 70)
        y = grid_y + (i // 2) * (cell_h + 42)
        fill = PAPER_LIGHT if i != 4 else (238, 232, 216)
        rounded(draw, (x, y, x + cell_w, y + cell_h), radius=8, fill=fill, outline=(215, 199, 164), width=2)
        draw.rectangle((x, y, x + 82, y + cell_h), fill=colors[i])
        draw.text((x + 22, y + 24), item["index"], font=FONTS["latin"], fill=PAPER_LIGHT)
        draw.text((x + 112, y + 24), f"{item['title']} / {item['sound']}", font=FONTS["h3"], fill=INK)
        draw_wrapped(draw, item["concept"], (x + 112, y + 82), FONTS["body_sm"], MUTED, cell_w - 150, line_gap=10, max_lines=3)

    statement = (
        "因此，画面中的水纹、雾带、断线、林木轮廓和雨痕并不是装饰，而是每首诗的声音机制。"
        "观者可以先看见空间，再在余白和轨迹中“听见”诗。"
    )
    alpha_box(page, (112, 2040, PDF_W - 112, 2240), fill=(231, 222, 200), alpha=190, radius=8, outline=(205, 185, 146))
    draw = ImageDraw.Draw(page)
    draw_wrapped(draw, statement, (160, 2090), FONTS["body"], INK, PDF_W - 320, line_gap=20, max_lines=3)
    draw_footer(page, 3)
    return page


def make_visual_system() -> Image.Image:
    page = page_base()
    draw_header(page, "02", "系列视觉系统", 4)
    draw = ImageDraw.Draw(page)

    poster = fit_resize(Image.open(str(A3_PATH)).convert("RGB"), (545, 772))
    paste_image_with_outline(page, poster, (112, 285), width=2)
    draw.text((112, 1102), "A3 宣传海报缩略", font=FONTS["caption"], fill=MUTED)

    x = 740
    draw.text((x, 270), "统一视觉不靠重复元素，而靠规则一致", font=FONTS["h1"], fill=INK)
    rules = [
        ("构图", "左侧诗境空间，右侧宣纸留白，形成“看见与听见”的距离。"),
        ("媒介", "当代水墨、矿物色、数字绘景与宣纸纤维共同构成。"),
        ("声音", "以涟漪、断线、回声弧、雨线表达五种传播方式。"),
        ("文字", "保留传统右起竖排，让诗文成为画面的一部分。"),
    ]
    y = 390
    for i, (label, detail) in enumerate(rules):
        draw.text((x, y), f"{i + 1:02d}", font=FONTS["latin"], fill=AMBER)
        draw.text((x + 78, y - 6), label, font=FONTS["h3"], fill=INK)
        draw_wrapped(draw, detail, (x + 78, y + 45), FONTS["body_sm"], MUTED, 760, line_gap=10, max_lines=2)
        y += 158

    draw.text((112, 1280), "色彩系统", font=FONTS["h1"], fill=INK)
    swatches = [
        ((234, 225, 204), "宣纸白"),
        ((71, 72, 68), "墨灰"),
        ((95, 116, 105), "豆青"),
        ((65, 77, 88), "靛青"),
        ((126, 116, 88), "雾金"),
        ((136, 81, 57), "枫褐"),
    ]
    sx = 112
    for color, label in swatches:
        rounded(draw, (sx, 1375, sx + 220, 1585), radius=8, fill=color, outline=(191, 174, 142), width=1)
        draw.text((sx, 1620), label, font=FONTS["body_sm"], fill=INK)
        sx += 255

    draw.text((112, 1772), "声境印记", font=FONTS["h1"], fill=INK)
    draw_soundscape_mark(page, (120, 1870), 190, OLIVE + (205,), width=5)
    mark_text = (
        "印记采用一笔连续水墨造型，融合双耳倾听与展开诗卷的意象。"
        "它作为系列落款出现，不依赖通用声波图标或文字标签。"
    )
    draw_wrapped(draw, mark_text, (380, 1885), FONTS["body"], INK, 520, line_gap=18, max_lines=5)

    draw.text((970, 1772), "字体层级", font=FONTS["h1"], fill=INK)
    draw.text((970, 1878), "声入诗境", font=load_font(CALLIGRAPHY_FONT, 58), fill=INK)
    draw.text((970, 1982), "章节标题 / 信息标题", font=FONTS["h3"], fill=SOFT_INK)
    draw.text((970, 2042), "正文说明用于解释过程、参数与人工判断。", font=FONTS["body_sm"], fill=MUTED)
    draw_footer(page, 4)
    return page


def make_workflow() -> Image.Image:
    page = page_base()
    draw_header(page, "03", "AIGC 工作流与人工介入", 5)
    draw = ImageDraw.Draw(page)

    draw.text((112, 255), "从文本到提交成品的七步链路", font=FONTS["h1"], fill=INK)
    draw_wrapped(
        draw,
        "流程的重点不是“生成一张图”，而是持续把诗词语义、声音机制、画面选择和提交规范对齐。",
        (112, 345),
        FONTS["body"],
        SOFT_INK,
        1260,
        line_gap=16,
        max_lines=2,
    )

    stages = [
        ("01", "文本研究", "提取声音来源、传播方式、时间、空间与情绪。", MOSS),
        ("02", "提示词设计", "限定场景、构图、媒介、色谱与禁用项。", AMBER),
        ("03", "滚图 / 底图生成", "围绕同一 Prompt 多轮生成无文字诗境底图，避免 UI、Logo 与文字。", INDIGO),
        ("04", "人工筛选", "判断诗意准确性、系列一致性和器物合理性。", OLIVE),
        ("05", "视觉后期", "统一色调、宣纸质感、声音轨迹与画面留白。", RUST),
        ("06", "程序排版", "完成竖排、印记、海报合成、PDF 编排与压缩。", NIGHT),
        ("07", "合规检查", "检查尺寸、DPI、文件大小、匿名信息与材料一致性。", AMBER),
    ]

    x0, y0 = 112, 535
    col_w, row_h = 730, 290
    for i, (num, title, detail, color) in enumerate(stages):
        x = x0 + (i % 2) * (col_w + 70)
        y = y0 + (i // 2) * row_h
        rounded(draw, (x, y, x + col_w, y + 220), radius=8, fill=PAPER_LIGHT, outline=(212, 195, 160), width=2)
        draw.rectangle((x, y, x + 100, y + 220), fill=color)
        draw.text((x + 24, y + 28), num, font=FONTS["latin"], fill=PAPER_LIGHT)
        draw.text((x + 138, y + 28), title, font=FONTS["h2"], fill=INK)
        draw_wrapped(draw, detail, (x + 138, y + 98), FONTS["body_sm"], MUTED, col_w - 180, line_gap=12, max_lines=3)
        if i < len(stages) - 1:
            if i % 2 == 0:
                draw.line((x + col_w + 10, y + 110, x + col_w + 54, y + 110), fill=HAIRLINE, width=4)
                draw.polygon([(x + col_w + 54, y + 110), (x + col_w + 38, y + 100), (x + col_w + 38, y + 120)], fill=HAIRLINE)
            else:
                draw.line((x - col_w - 35, y + 220, x - col_w - 35, y + 272), fill=HAIRLINE, width=4)
                draw.polygon([(x - col_w - 35, y + 272), (x - col_w - 45, y + 256), (x - col_w - 25, y + 256)], fill=HAIRLINE)

    alpha_box(page, (112, 2032, PDF_W - 112, 2245), fill=(234, 225, 204), alpha=215, radius=8, outline=(205, 185, 146))
    draw = ImageDraw.Draw(page)
    draw.text((160, 2080), "人工介入的核心判断", font=FONTS["h3"], fill=INK)
    note = "主题策划、诗词选择、候选筛选、构图后期、色彩统一、声音轨迹、声境印记和提交编排均由人工完成。AIGC 只承担无文字底图的素材生成。"
    draw_wrapped(draw, note, (160, 2140), FONTS["body_sm"], SOFT_INK, PDF_W - 320, line_gap=12, max_lines=3)
    draw_footer(page, 5)
    return page


def make_prompt_evidence() -> Image.Image:
    page = page_base()
    draw_header(page, "04", "Prompt 与底图证据", 6)
    draw = ImageDraw.Draw(page)

    draw.text((112, 255), "Prompt 不是一句描述，而是四层控制", font=FONTS["h1"], fill=INK)
    layers = [
        ("场景氛围", "时间、天气、光线与情绪基调"),
        ("核心物象", "扁舟、江枫、林木、窗灯等诗中物"),
        ("声音转译", "涟漪、断线、回声弧、雨痕等机制"),
        ("共享风格", "当代水墨、矿物色、宣纸纹理"),
    ]
    y = 368
    for i, (title, detail) in enumerate(layers):
        x = 112 + i * 390
        rounded(draw, (x, y, x + 340, y + 190), radius=8, fill=PAPER_LIGHT, outline=(211, 195, 160), width=2)
        draw.text((x + 24, y + 24), f"{i + 1:02d}", font=FONTS["latin"], fill=[MOSS, AMBER, INDIGO, RUST][i])
        draw.text((x + 24, y + 70), title, font=FONTS["h3"], fill=INK)
        draw_wrapped(draw, detail, (x + 24, y + 122), FONTS["caption"], MUTED, 290, line_gap=8, max_lines=2)

    draw.text((112, 680), "滚图逻辑与底图证据", font=FONTS["h1"], fill=INK)
    draw.text((112, 750), "每首诗围绕同一四层 Prompt 进行多轮生成，先筛掉含字、构图混乱或诗意偏差的结果，再保留最稳定的无文字底图进入后期。", font=FONTS["body_sm"], fill=MUTED)
    grid_top = 840
    thumb_w, thumb_h = 236, 354
    gap = 70
    for i, item in enumerate(SERIES):
        x = 112 + i * (thumb_w + gap)
        img = fit_resize(Image.open(str(source_path(item))).convert("RGB"), (thumb_w, thumb_h))
        paste_image_with_outline(page, img, (x, grid_top), outline=(181, 160, 123), width=2)
        draw.text((x, grid_top + thumb_h + 28), item["index"], font=FONTS["latin"], fill=AMBER)
        draw.text((x + 48, grid_top + thumb_h + 22), f"{item['title']} / {item['sound']}", font=FONTS["body_sm"], fill=INK)

    style_y = 1398
    draw.text((112, style_y), "共享风格限定词", font=FONTS["h1"], fill=INK)
    alpha_box(page, (112, style_y + 88, PDF_W - 112, style_y + 255), fill=(237, 231, 216), alpha=230, radius=8, outline=(207, 190, 154))
    draw = ImageDraw.Draw(page)
    prompt_suffix = "contemporary Chinese ink wash, mineral pigment, xuan paper grain"
    draw_word_wrapped(draw, prompt_suffix, (156, style_y + 138), FONTS["prompt"], INDIGO, PDF_W - 312, line_gap=10, max_lines=2)
    explain = (
        "该后缀用于稳定系列介质：宣纸颗粒提供传统触感，矿物色控制色彩厚度，"
        "当代水墨避免过度写实或动漫化。"
    )
    draw_wrapped(draw, explain, (112, style_y + 330), FONTS["body"], SOFT_INK, PDF_W - 224, line_gap=18, max_lines=3)

    draw.text((112, 1960), "负向控制", font=FONTS["h1"], fill=INK)
    negatives = ["不生成文字", "不出现 UI 元素", "不使用商业标识", "不出现真实人物身份"]
    for i, item in enumerate(negatives):
        x = 112 + i * 390
        rounded(draw, (x, 2052, x + 330, 2148), radius=8, fill=PAPER_LIGHT, outline=(210, 195, 163), width=2)
        draw.text((x + 28, 2084), item, font=FONTS["body_sm"], fill=INK)
    draw_footer(page, 6)
    return page


def make_work_page(item: dict, page_no: int) -> Image.Image:
    page = page_base()
    draw_header(page, "05", "作品详解", page_no)
    draw = ImageDraw.Draw(page)

    palette_colors = {
        "01": MOSS,
        "02": AMBER,
        "03": INDIGO,
        "04": OLIVE,
        "05": NIGHT,
    }
    color = palette_colors.get(item["index"], OLIVE)

    final_img = fit_resize(Image.open(str(work_path(item))).convert("RGB"), (820, 1230))
    paste_image_with_outline(page, final_img, (112, 282), outline=(142, 119, 82), width=3)
    draw.text((112, 1548), "最终排版成品", font=FONTS["caption"], fill=MUTED)

    x = 1010
    draw.text((x, 282), item["index"], font=FONTS["latin"], fill=color)
    draw.text((x + 75, 258), f"{item['title']} / {item['sound']}", font=FONTS["h1"], fill=INK)
    draw.text((x + 78, 350), f"〔{item['dynasty']}〕{item['author']}", font=FONTS["body_sm"], fill=MUTED)
    draw_wrapped(draw, item["poem"], (x, 430), FONTS["kai"], INK, 610, line_gap=16, max_lines=4)

    section_label(draw, (x, 720), "声音转译逻辑", color)
    draw_wrapped(draw, item["concept"], (x, 795), FONTS["body"], SOFT_INK, 620, line_gap=17, max_lines=4)

    source = fit_resize(Image.open(str(source_path(item))).convert("RGB"), (210, 315))
    paste_image_with_outline(page, source, (x, 1090), outline=(181, 160, 123), width=2)
    draw.text((x + 250, 1090), "AIGC 原始底图", font=FONTS["h3"], fill=INK)
    draw_wrapped(draw, "无文字场景素材，后续叠加宣纸留白、竖排诗文、声境印记和统一色调。", (x + 250, 1148), FONTS["body_sm"], MUTED, 360, line_gap=10, max_lines=5)
    draw.text((x + 250, 1372), f"色谱：{item['palette']}", font=FONTS["body_sm"], fill=INK)

    prompt_y = 1670
    alpha_box(page, (112, prompt_y, PDF_W - 112, 2240), fill=(238, 232, 216), alpha=232, radius=8, outline=(205, 185, 146))
    draw = ImageDraw.Draw(page)
    draw.text((158, prompt_y + 42), "完整 Prompt", font=FONTS["h3"], fill=INK)
    draw_word_wrapped(draw, item["prompt"], (158, prompt_y + 102), FONTS["prompt"], SOFT_INK, 860, line_gap=11, max_lines=7)

    draw.line((1100, prompt_y + 52, 1100, prompt_y + 512), fill=(202, 184, 150), width=2)
    draw.text((1150, prompt_y + 42), "人工排版动作", font=FONTS["h3"], fill=INK)
    actions = [
        "筛选最贴合诗意与系列气质的底图版本",
        "统一色温、饱和度与宣纸右侧留白",
        "设置标题、作者、诗句三级竖排关系",
        "加入声境印记与声音轨迹，控制画面节奏",
    ]
    ay = prompt_y + 110
    for action in actions:
        draw.ellipse((1154, ay + 7, 1170, ay + 23), fill=color)
        ay = draw_wrapped(draw, action, (1190, ay), FONTS["body_sm"], SOFT_INK, 420, line_gap=8, max_lines=2) + 16

    draw_footer(page, page_no)
    return page


def make_disclosure() -> Image.Image:
    page = page_base()
    draw_header(page, "06", "原创声明与过程索引", 12)
    draw = ImageDraw.Draw(page)

    draw.text((112, 255), "AIGC 使用声明", font=FONTS["h1"], fill=INK)
    disclosure = (
        "底图由 GLM-5.2（智谱 AI 大模型）辅助生成无文字场景底图；主题策划、诗词选择、"
        "提示词设计、候选筛选、构图、色彩统一、字体选择、声音轨迹、声境印记设计、"
        "系列海报合成、过程编排和提交规格检查均由人工完成。所有古诗均属于公有领域；"
        "生成图中未使用真实人物身份、商业品牌或第三方赛事标识。"
    )
    draw_wrapped(draw, disclosure, (112, 345), FONTS["body"], SOFT_INK, PDF_W - 224, line_gap=20, max_lines=7)

    draw.text((112, 760), "人工设计介入明细", font=FONTS["h1"], fill=INK)
    interventions = [
        ("系列策展", "确定“声音到构图规则”的主题，并选择五首具有声音内在关系的诗词。"),
        ("视觉系统", "统一色谱、宣纸质感、竖排规范、声境印记和留白比例。"),
        ("后期算法", "设置调色、压红、纸色叠加、竖排、印记和压缩参数。"),
        ("候选筛选", "在多张 AIGC 底图中选择最符合诗意和系列一致性的版本。"),
        ("海报设计", "确定主景、标题位置、声音列表、视觉落款和画面节奏。"),
        ("合规检查", "逐项验证尺寸、DPI、文件大小、视频编码和匿名信息。"),
    ]
    card_w = 735
    for i, (title, detail) in enumerate(interventions):
        x = 112 + (i % 2) * (card_w + 60)
        y = 858 + (i // 2) * 238
        rounded(draw, (x, y, x + card_w, y + 180), radius=8, fill=PAPER_LIGHT, outline=(212, 195, 160), width=2)
        draw.text((x + 32, y + 24), title, font=FONTS["h3"], fill=INK)
        draw_wrapped(draw, detail, (x + 32, y + 78), FONTS["body_sm"], MUTED, card_w - 64, line_gap=10, max_lines=3)

    draw.text((112, 1668), "过程说明内容索引", font=FONTS["h1"], fill=INK)
    index_items = [
        ("创意说明", "第 03 页说明选题来源、声音机制和文化转译方向。"),
        ("工具组合", "第 05 页说明 AIGC、人工筛选、视觉后期与程序排版链路。"),
        ("滚图逻辑", "第 06 页说明多轮生成、筛选条件与底图证据。"),
        ("提示词", "第 06-11 页保留结构化 Prompt 与五件作品的完整 Prompt。"),
    ]
    y = 1765
    for i, (title, detail) in enumerate(index_items):
        x = 112 + (i % 2) * (735 + 60)
        cy = y + (i // 2) * 170
        rounded(draw, (x, cy, x + 735, cy + 128), radius=8, fill=(239, 233, 218), outline=(213, 195, 160), width=1)
        draw.text((x + 30, cy + 22), title, font=FONTS["h3"], fill=INK)
        draw_wrapped(draw, detail, (x + 30, cy + 72), FONTS["caption"], MUTED, 660, line_gap=7, max_lines=2)

    closing = (
        "本页作为创作过程的收束，强调 AIGC 素材生成与人工设计判断之间的边界："
        "技术提供候选图像，最终的主题、形式、节奏与提交表达由人工完成。"
    )
    draw_wrapped(draw, closing, (112, 2138), FONTS["body_sm"], SOFT_INK, PDF_W - 224, line_gap=12, max_lines=3)

    draw_footer(page, 12)
    return page


def update_manifest(pdf_path: Path) -> None:
    if not MANIFEST_PATH.exists():
        return
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    rel = str(pdf_path.relative_to(ROOT)).replace("\\", "/")
    found = False
    for item in data.get("deliverables", []):
        if item.get("path") == rel:
            item["bytes"] = pdf_path.stat().st_size
            found = True
            break
    if not found:
        data.setdefault("deliverables", []).append({"path": rel, "bytes": pdf_path.stat().st_size})
    data["generated_at"] = datetime.now().isoformat(timespec="seconds")
    MANIFEST_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_pdf() -> Path:
    pages: List[Image.Image] = [
        make_cover(),
        make_contents(),
        make_concept(),
        make_visual_system(),
        make_workflow(),
        make_prompt_evidence(),
    ]
    for offset, item in enumerate(SERIES, start=7):
        pages.append(make_work_page(item, offset))
    pages.append(make_disclosure())
    save_pages(pages, PDF_PATH)
    update_manifest(PDF_PATH)
    print(f"PDF written to: {PDF_PATH}")
    return PDF_PATH


if __name__ == "__main__":
    build_pdf()
