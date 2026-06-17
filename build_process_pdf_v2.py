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
    "prompt": load_font(LATIN_FONT, 29),
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
        "作品如何从古典诗词中的声音出发，经过 OpenAI GPT 生成无文字诗境底图、人工筛选、"
        "GPT 辅助 Python + Pillow 代码编辑与程序化排版，最终形成一组可提交的系列视觉作品。"
    )
    draw_wrapped(draw, summary, (112, 340), FONTS["body"], SOFT_INK, 1040, line_gap=17, max_lines=3)

    cards = [
        ("01", "为什么做", "选题、声音机制与诗词选择"),
        ("02", "怎么生成", "OpenAI GPT、Prompt 结构与底图证据"),
        ("03", "如何成品", "GPT 辅助代码编辑、人工校正与提交检查"),
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
        ("AIGC 工作流", "OpenAI GPT、筛选、代码编辑与合规检查", "05"),
        ("Prompt 与代码证据", "底图 Prompt、五张源图与编辑逻辑", "06"),
        ("作品详解", "五件作品逐页说明", "07-11"),
        ("原创声明与人工介入", "GPT 辅助边界、版权与人工判断", "12"),
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

    draw.text((112, 255), "设计过程不是生成，而是可控转译", font=FONTS["h1"], fill=INK)
    draw_wrapped(
        draw,
        "核心竞争力在于把不可见的声音先转成 OpenAI GPT 底图候选。再用 GPT 辅助代码固化后期规则，最后由人工完成审美校正与提交控制。",
        (112, 345),
        FONTS["body"],
        SOFT_INK,
        1380,
        line_gap=16,
        max_lines=3,
    )

    process_cards = [
        (
            "01",
            "OpenAI GPT 生成底图",
            "把诗词里的声音、空间、时间和情绪写成 Prompt，生成无文字诗境底图候选。",
            MOSS,
        ),
        (
            "02",
            "GPT 辅助代码编辑",
            "用 Python + Pillow 把调色、宣纸留白、声音轨迹、竖排诗文和压缩输出转成可迭代代码。",
            AMBER,
        ),
        (
            "03",
            "人工校正与成品控制",
            "人工选择底图、微调参数、检查版式，再输出 1440x2160 系列图、A3 海报和过程 PDF。",
            INDIGO,
        ),
    ]

    card_y = 500
    card_w = 462
    card_h = 840
    card_gap = 53
    for i, (num, title, detail, color) in enumerate(process_cards):
        x = 112 + i * (card_w + card_gap)
        rounded(draw, (x, card_y, x + card_w, card_y + card_h), radius=8, fill=PAPER_LIGHT, outline=(212, 195, 160), width=2)
        draw.rectangle((x, card_y, x + card_w, card_y + 92), fill=color)
        draw.text((x + 28, card_y + 24), num, font=FONTS["latin"], fill=PAPER_LIGHT)
        draw.text((x + 96, card_y + 18), title, font=FONTS["h3"], fill=PAPER_LIGHT)
        draw_wrapped(draw, detail, (x + 30, card_y + 125), FONTS["body_sm"], SOFT_INK, card_w - 60, line_gap=12, max_lines=4)

        if i == 0:
            thumb_items = [SERIES[0], SERIES[2], SERIES[4]]
            for j, item in enumerate(thumb_items):
                img = fit_resize(Image.open(str(source_path(item))).convert("RGB"), (112, 168))
                ix = x + 32 + j * 138
                iy = card_y + 360
                paste_image_with_outline(page, img, (ix, iy), outline=(181, 160, 123), width=2)
                draw.text((ix, iy + 188), item["index"], font=FONTS["latin_sm"], fill=color)
            draw_wrapped(draw, "证据重点：保留无文字底图，避开文字、UI 和真实身份信息。", (x + 32, card_y + 625), FONTS["body_sm"], MUTED, card_w - 64, line_gap=10, max_lines=3)
        elif i == 1:
            code_box = (x + 32, card_y + 330, x + card_w - 32, card_y + 610)
            rounded(draw, code_box, radius=8, fill=(238, 232, 216), outline=(205, 185, 146), width=1)
            code_lines = [
                "img = load(gpt_background)",
                "img = tune_palette(img)",
                "img = add_margin_trace(img)",
                "export_jpg(img, dpi=300)",
            ]
            cy = card_y + 360
            for line in code_lines:
                draw.text((x + 58, cy), line, font=FONTS["latin"], fill=INDIGO)
                cy += 52
            chips = ["调色", "留白", "轨迹", "竖排", "压缩"]
            for j, chip in enumerate(chips):
                cx = x + 34 + (j % 3) * 130
                cy2 = card_y + 655 + (j // 3) * 72
                rounded(draw, (cx, cy2, cx + 108, cy2 + 48), radius=8, fill=(248, 244, 234), outline=(213, 195, 160), width=1)
                draw.text((cx + 24, cy2 + 11), chip, font=FONTS["caption"], fill=INK)
        else:
            thumb_items = [SERIES[0], SERIES[2], SERIES[4]]
            for j, item in enumerate(thumb_items):
                img = fit_resize(Image.open(str(work_path(item))).convert("RGB"), (112, 168))
                ix = x + 32 + j * 138
                iy = card_y + 360
                paste_image_with_outline(page, img, (ix, iy), outline=(142, 119, 82), width=2)
                draw.text((ix, iy + 188), item["index"], font=FONTS["latin_sm"], fill=color)
            draw_wrapped(draw, "控制重点：统一规格、留白、竖排层级、声境印记和文件大小。", (x + 32, card_y + 625), FONTS["body_sm"], MUTED, card_w - 64, line_gap=10, max_lines=3)

    for ax in (112 + card_w + 14, 112 + 2 * (card_w + card_gap) - 47):
        draw.line((ax, card_y + 420, ax + 42, card_y + 420), fill=HAIRLINE, width=4)
        draw.polygon([(ax + 42, card_y + 420), (ax + 24, card_y + 408), (ax + 24, card_y + 432)], fill=HAIRLINE)

    draw.text((112, 1428), "竞争力体现", font=FONTS["h1"], fill=INK)
    strengths = [
        ("可解释", "声音机制 -> Prompt -> 底图 -> 代码参数"),
        ("可追溯", "底图、Prompt、成品与校正动作逐页对应"),
        ("可复用", "后期规则写入可复用代码流程"),
        ("可控", "GPT 给方案，人工定审美和提交规范"),
    ]
    strength_w = 350
    strength_y = 1518
    for i, (title, detail) in enumerate(strengths):
        sx = 112 + i * (strength_w + 38)
        rounded(draw, (sx, strength_y, sx + strength_w, strength_y + 210), radius=8, fill=(248, 244, 234), outline=(213, 195, 160), width=2)
        draw.text((sx + 26, strength_y + 24), f"{i + 1:02d}", font=FONTS["latin_sm"], fill=[MOSS, AMBER, INDIGO, RUST][i])
        draw.text((sx + 26, strength_y + 58), title, font=FONTS["h3"], fill=INK)
        draw_wrapped(draw, detail, (sx + 26, strength_y + 112), FONTS["body_sm"], MUTED, strength_w - 52, line_gap=10, max_lines=3)

    alpha_box(page, (112, 1865, PDF_W - 112, 2148), fill=(234, 225, 204), alpha=215, radius=8, outline=(205, 185, 146))
    draw = ImageDraw.Draw(page)
    draw.text((160, 1912), "人工判断与 GPT 辅助的边界", font=FONTS["h3"], fill=INK)
    note = (
        "OpenAI GPT 负责提供无文字诗境底图候选，GPT 辅助把图像编辑意图转写为 Python + Pillow 代码。"
        "主题策划、诗词选择、候选筛选、参数取舍、审美校正和提交编排均由人工完成。"
    )
    draw_wrapped(draw, note, (160, 1978), FONTS["body_sm"], SOFT_INK, PDF_W - 320, line_gap=12, max_lines=4)
    draw_footer(page, 5)
    return page


def make_prompt_evidence() -> Image.Image:
    page = page_base()
    draw_header(page, "04", "Prompt 与代码编辑证据", 6)
    draw = ImageDraw.Draw(page)

    draw.text((112, 255), "Prompt 控制底图，代码控制成品", font=FONTS["h1"], fill=INK)
    layers = [
        ("场景氛围", "时间、天气、光线与情绪基调"),
        ("核心物象", "扁舟、江枫、林木、窗灯等诗中物"),
        ("声音转译", "涟漪、断线、回声弧、雨痕等机制"),
        ("代码编辑", "调色、留白、轨迹、竖排与压缩"),
    ]
    y = 368
    for i, (title, detail) in enumerate(layers):
        x = 112 + i * 390
        rounded(draw, (x, y, x + 340, y + 190), radius=8, fill=PAPER_LIGHT, outline=(211, 195, 160), width=2)
        draw.text((x + 24, y + 24), f"{i + 1:02d}", font=FONTS["latin"], fill=[MOSS, AMBER, INDIGO, RUST][i])
        draw.text((x + 24, y + 70), title, font=FONTS["h3"], fill=INK)
        draw_wrapped(draw, detail, (x + 24, y + 122), FONTS["body_sm"], MUTED, 290, line_gap=10, max_lines=2)

    draw.text((112, 680), "OpenAI GPT 底图证据", font=FONTS["h1"], fill=INK)
    draw.text((112, 750), "每首诗围绕统一 Prompt 结构生成无文字底图，先筛掉含字、构图混乱或诗意偏差的结果，再保留最稳定版本进入代码编辑阶段。", font=FONTS["body_sm"], fill=MUTED)
    grid_top = 840
    thumb_w, thumb_h = 236, 354
    gap = 70
    for i, item in enumerate(SERIES):
        x = 112 + i * (thumb_w + gap)
        img = fit_resize(Image.open(str(source_path(item))).convert("RGB"), (thumb_w, thumb_h))
        paste_image_with_outline(page, img, (x, grid_top), outline=(181, 160, 123), width=2)
        draw.text((x, grid_top + thumb_h + 28), item["index"], font=FONTS["latin"], fill=AMBER)
        draw.text((x + 48, grid_top + thumb_h + 22), f"{item['title']} / {item['sound']}", font=FONTS["body_sm"], fill=INK)

    style_y = 1378
    draw.text((112, style_y), "底图到成品的代码编辑闭环", font=FONTS["h1"], fill=INK)
    edit_steps = [
        ("01", "统一色调", "压低杂色，统一水墨与矿物色"),
        ("02", "生成留白", "加宣纸侧栏，容纳诗文和印记"),
        ("03", "声音轨迹", "把五种声音转成可控图层"),
        ("04", "输出检查", "控制尺寸、DPI、压缩和匿名信息"),
    ]
    step_w = 350
    step_y = style_y + 95
    for i, (num, title, detail) in enumerate(edit_steps):
        sx = 112 + i * (step_w + 38)
        rounded(draw, (sx, step_y, sx + step_w, step_y + 220), radius=8, fill=PAPER_LIGHT, outline=(210, 195, 163), width=2)
        draw.text((sx + 26, step_y + 24), num, font=FONTS["latin_sm"], fill=[MOSS, AMBER, INDIGO, RUST][i])
        draw.text((sx + 26, step_y + 58), title, font=FONTS["h3"], fill=INK)
        draw_wrapped(draw, detail, (sx + 26, step_y + 112), FONTS["body_sm"], MUTED, step_w - 52, line_gap=10, max_lines=3)

    alpha_box(page, (112, 1710, PDF_W - 112, 1980), fill=(237, 231, 216), alpha=230, radius=8, outline=(207, 190, 154))
    draw = ImageDraw.Draw(page)
    draw.text((156, 1742), "代码编辑逻辑", font=FONTS["h3"], fill=INK)
    code_lines = [
        "base = openai_gpt(prompt)",
        "work = tune_palette(base, palette)",
        "work = add_margin_trace(work)",
        "export(work, dpi=300, max_mb=5)",
    ]
    cy = 1782
    for line in code_lines:
        draw.text((156, cy), line, font=FONTS["latin"], fill=INDIGO)
        cy += 37
    draw.line((760, 1738, 760, 1954), fill=(202, 184, 150), width=2)
    draw.text((808, 1742), "共享风格限定词", font=FONTS["h3"], fill=INK)
    style_terms = ["当代水墨", "矿物色", "宣纸肌理"]
    for i, term in enumerate(style_terms):
        tx = 808 + i * 220
        rounded(draw, (tx, 1792, tx + 190, 1864), radius=8, fill=PAPER_LIGHT, outline=(210, 195, 163), width=1)
        draw.text((tx + 22, 1811), term, font=FONTS["h3"], fill=INDIGO)
    draw_wrapped(draw, "Prompt 稳定画面介质；代码固定色调、留白、声音轨迹和输出规格。", (808, 1884), FONTS["body_sm"], MUTED, 690, line_gap=10, max_lines=2)

    draw.text((112, 2038), "竞争力控制点", font=FONTS["h1"], fill=INK)
    code_tasks = ["底图无文字", "代码可复用", "系列参数统一", "提交规格稳定"]
    for i, item in enumerate(code_tasks):
        x = 112 + i * 390
        rounded(draw, (x, 2124, x + 330, 2220), radius=8, fill=PAPER_LIGHT, outline=(210, 195, 163), width=2)
        draw.text((x + 28, 2156), item, font=FONTS["body_sm"], fill=INK)
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
    draw.text((x + 250, 1090), "OpenAI GPT 底图", font=FONTS["h3"], fill=INK)
    draw_wrapped(draw, "无文字场景素材，后续通过 GPT 辅助编写的 Python + Pillow 逻辑叠加留白、诗文、印记和统一色调。", (x + 250, 1148), FONTS["body_sm"], MUTED, 360, line_gap=10, max_lines=5)
    draw.text((x + 250, 1372), f"色谱：{item['palette']}", font=FONTS["body_sm"], fill=INK)

    prompt_y = 1670
    alpha_box(page, (112, prompt_y, PDF_W - 112, 2240), fill=(238, 232, 216), alpha=232, radius=8, outline=(205, 185, 146))
    draw = ImageDraw.Draw(page)
    draw.text((158, prompt_y + 42), "底图 Prompt", font=FONTS["h3"], fill=INK)
    prompt_end = draw_word_wrapped(draw, item["prompt"], (158, prompt_y + 104), FONTS["prompt"], SOFT_INK, 940, line_gap=15, max_lines=7)
    draw.line((158, prompt_end + 22, 1115, prompt_end + 22), fill=(216, 199, 164), width=1)
    focus_items = [
        ("场景", f"{item['title']}的时间与空间"),
        ("声音", f"{item['sound']}转成墨痕节奏"),
        ("媒介", "当代水墨 / 宣纸肌理"),
        ("规则", "无文字底图，后期留白"),
    ]
    focus_y = max(prompt_end + 54, prompt_y + 330)
    for i, (label, detail) in enumerate(focus_items):
        fx = 158 + (i % 2) * 485
        fy = focus_y + (i // 2) * 86
        rounded(draw, (fx, fy, fx + 445, fy + 62), radius=8, fill=PAPER_LIGHT, outline=(216, 199, 164), width=1)
        draw.text((fx + 22, fy + 16), label, font=FONTS["body_sm"], fill=color)
        draw.text((fx + 118, fy + 16), detail, font=FONTS["body_sm"], fill=MUTED)

    divider_x = 1180
    draw.line((divider_x, prompt_y + 52, divider_x, prompt_y + 512), fill=(202, 184, 150), width=2)
    draw.text((1228, prompt_y + 42), "GPT 代码编辑", font=FONTS["h3"], fill=INK)
    draw.text((1228, prompt_y + 86), "人工校正", font=FONTS["h3"], fill=INK)
    actions = [
        "用 Python + Pillow 统一色温、饱和度与宣纸留白",
        "用代码叠加声音轨迹，保持五张作品的节奏一致",
        "人工校正标题、作者、诗句三级竖排关系",
        "加入声境印记并压缩输出，确认画面没有文字溢出",
    ]
    ay = prompt_y + 156
    for action in actions:
        draw.ellipse((1228, ay + 7, 1244, ay + 23), fill=color)
        ay = draw_wrapped(draw, action, (1264, ay), FONTS["body_sm"], SOFT_INK, 315, line_gap=8, max_lines=3) + 16

    draw_footer(page, page_no)
    return page


def make_disclosure() -> Image.Image:
    page = page_base()
    draw_header(page, "06", "原创声明与人工介入", 12)
    draw = ImageDraw.Draw(page)

    draw.text((112, 255), "AIGC 使用声明", font=FONTS["h1"], fill=INK)
    disclosure = (
        "无文字诗境底图由 OpenAI GPT 辅助生成；后续通过 Python + Pillow 完成调色、"
        "宣纸留白、声音轨迹、竖排诗文、声境印记、系列海报合成、过程编排与压缩输出。"
        "图像编辑与排版代码由 GPT 辅助生成和迭代。主题策划、诗词选择、候选筛选、参数取舍、"
        "审美校正和提交规格检查均由人工完成。所有古诗均属于公有领域；生成图中未使用真实人物身份、商业品牌或第三方赛事标识。"
    )
    draw_wrapped(draw, disclosure, (112, 345), FONTS["body"], SOFT_INK, PDF_W - 224, line_gap=20, max_lines=7)

    draw.text((112, 760), "人工设计介入明细", font=FONTS["h1"], fill=INK)
    interventions = [
        ("系列策展", "确定“声音到构图规则”的主题，并选择五首具有声音内在关系的诗词。"),
        ("视觉系统", "统一色谱、宣纸质感、竖排规范、声境印记和留白比例。"),
        ("代码编辑", "借助 GPT 生成并修改 Python + Pillow 代码，设置调色、纸色叠加、竖排、印记和压缩参数。"),
        ("候选筛选", "在多张 OpenAI GPT 底图中选择最符合诗意和系列一致性的版本。"),
        ("海报设计", "确定主景、标题位置、声音列表、视觉落款和画面节奏。"),
        ("合规检查", "逐项验证尺寸、DPI、文件大小、视频编码和匿名信息。"),
    ]
    card_w = 735
    card_h = 270
    for i, (title, detail) in enumerate(interventions):
        x = 112 + (i % 2) * (card_w + 60)
        y = 838 + (i // 2) * 322
        rounded(draw, (x, y, x + card_w, y + card_h), radius=8, fill=PAPER_LIGHT, outline=(212, 195, 160), width=2)
        draw.text((x + 34, y + 36), title, font=FONTS["h3"], fill=INK)
        draw_wrapped(draw, detail, (x + 34, y + 104), FONTS["body"], MUTED, card_w - 68, line_gap=14, max_lines=3)

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
