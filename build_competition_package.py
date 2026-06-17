#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Build the complete NCDA submission package for the "声入诗境" series."""

from __future__ import print_function

import json
import math
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "assets" / "series_sources"
MARK_PATH = ROOT / "assets" / "images" / "soundscape_mark.png"
SUBMISSION_DIR = ROOT / "submission"
WORKS_DIR = SUBMISSION_DIR / "works"
PROCESS_DIR = SUBMISSION_DIR / "process"
VIDEO_DIR = SUBMISSION_DIR / "video"
A3_PATH = SUBMISSION_DIR / "a3_poster.jpg"
PDF_PATH = PROCESS_DIR / "creation_process.pdf"
MANIFEST_PATH = SUBMISSION_DIR / "submission_manifest.json"

WORK_SIZE = (1440, 2160)
A3_SIZE = (3508, 4961)
PDF_PAGE_SIZE = (1754, 2480)
MAX_JPG_BYTES = 5 * 1024 * 1024

SERIES_TITLE = "声入诗境"
SERIES_SUBTITLE = "古典诗词中不可见声音的 AIGC 视觉转译"
PLATFORM_TITLE = "声入诗境：诗词声音的AIGC视觉转译"
SERIES_STATEMENT = (
    "作品选取鸟鸣、钟声、猿啼、人语回响与夜雨五种声音，"
    "以声波的扩散、回返、叠加和消隐作为构图规则，将听觉经验转译为东方空间。"
)
NARRATION_TEXT = """古典诗词不仅可以被阅读，也可以被聆听。

《声入诗境》选取五首诗中的五种声音：春晓的鸟鸣、枫桥的钟声、三峡的猿啼、空山的人语回响，以及巴山的夜雨。

这些声音没有固定形体，却能够建立空间、推动时间并唤起情绪。因此，作品没有直接描绘声音来源，而是把扩散、回返、断续、叠加和消隐转化为画面的构图规则。

创作首先通过大语言模型拆解诗词中的声音、场景和情绪，再以统一的当代水墨语言生成无文字底图。人工筛选之后，进一步统一色彩、宣纸质感与声音线索，并使用传统竖排和一笔连续水墨印记建立系列视觉系统。

从春晓的湿润微光，到枫桥夜泊的寒钟；从三峡猿声的折返，到鹿柴空山的回响；最后落入巴山夜雨与窗灯之间的等待。

《声入诗境》希望让不可见的声音成为可以进入、可以停留，也可以被看见的东方空间。"""

SERIES = [
    {
        "index": "01",
        "title": "春晓",
        "author": "孟浩然",
        "dynasty": "唐",
        "sound": "鸟鸣",
        "poem": "春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。",
        "source": "01_spring_dawn.png",
        "concept": "雨后庭院由暗至明，鸟鸣化为穿过花枝与水面的同心墨痕。",
        "palette": "暖白 / 雾灰 / 豆青 / 桃粉",
        "prompt": (
            "Jiangnan spring dawn after wind and rain, wet stone, scattered peach petals, "
            "distant birds implied through rhythmic silhouettes and expanding ink rings, "
            "contemporary Chinese ink wash, mineral pigment, xuan paper grain."
        ),
    },
    {
        "index": "02",
        "title": "枫桥夜泊",
        "author": "张继",
        "dynasty": "唐",
        "sound": "钟声",
        "poem": "月落乌啼霜满天，江枫渔火对愁眠。姑苏城外寒山寺，夜半钟声到客船。",
        "source": "02_midnight_bell.png",
        "concept": "夜半钟声不以钟体出现，而以穿越雾、水与客船的金色涟漪呈现。",
        "palette": "墨黑 / 月灰 / 靛青 / 枫锈",
        "prompt": (
            "Sleepless boat at midnight near Hanshan Temple, moon setting, crow, maple branches, "
            "two fishing lights, temple bell expressed as elegant concentric ink ripples through fog."
        ),
    },
    {
        "index": "03",
        "title": "早发白帝城",
        "author": "李白",
        "dynasty": "唐",
        "sound": "猿啼",
        "poem": "朝辞白帝彩云间，千里江陵一日还。两岸猿声啼不住，轻舟已过万重山。",
        "source": "03_gorge_echo.png",
        "concept": "猿啼被转译为峡谷间反复折返的断续墨线，与轻舟形成速度对比。",
        "palette": "晨金 / 石青 / 墨灰 / 雾金",
        "prompt": (
            "Tiny ancient boat moving swiftly through the Three Gorges at dawn, layered cliffs, "
            "hidden gibbons suggested by elongated broken ink echoes traveling between canyon walls."
        ),
    },
    {
        "index": "04",
        "title": "鹿柴",
        "author": "王维",
        "dynasty": "唐",
        "sound": "人语回响",
        "poem": "空山不见人，但闻人语响。返景入深林，复照青苔上。",
        "source": "04_empty_mountain.png",
        "concept": "无人空山中，声音通过层层错位、逐渐消隐的林木轮廓完成回返。",
        "palette": "苔绿 / 墨黑 / 淡金 / 宣纸白",
        "prompt": (
            "Empty deep mountain forest, no visible people, faint human voice returning from unseen "
            "valleys, sunlight touching green moss, fading repeated ink bands and forest silhouettes."
        ),
    },
    {
        "index": "05",
        "title": "夜雨寄北",
        "author": "李商隐",
        "dynasty": "唐",
        "sound": "夜雨",
        "poem": "君问归期未有期，巴山夜雨涨秋池。何当共剪西窗烛，却话巴山夜雨时。",
        "source": "05_night_rain.png",
        "concept": "雨线与池面涟漪构成时间层，窗灯连接此刻的孤独与未来的重逢。",
        "palette": "雨灰 / 墨蓝 / 琥珀 / 枫褐",
        "prompt": (
            "Autumn night rain in Bashan, dark courtyard pond, solitary warm lamp behind paper window, "
            "rain rhythm translated into vertical ink traces and overlapping circles on water."
        ),
    },
]


def ensure_dirs():
    for path in (SUBMISSION_DIR, WORKS_DIR, PROCESS_DIR, VIDEO_DIR):
        path.mkdir(parents=True, exist_ok=True)


def font_path(*candidates):
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return str(path)
    return str(ROOT / "assets" / "fonts" / "MaShanZheng-Regular.ttf")


CALLIGRAPHY_FONT = font_path(ROOT / "assets" / "fonts" / "MaShanZheng-Regular.ttf")
TEXT_FONT = font_path(
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simsun.ttc",
    ROOT / "assets" / "fonts" / "MaShanZheng-Regular.ttf",
)
LATIN_FONT = font_path(
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    TEXT_FONT,
)


def load_font(path, size):
    return ImageFont.truetype(path, size)


def measure_text(draw, text, font):
    if hasattr(draw, "textbbox"):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    if hasattr(font, "getbbox"):
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    return font.getsize(text)


def draw_rect_outline(draw, coords, color, width=1):
    left, top, right, bottom = coords
    for offset in range(width):
        draw.rectangle(
            (left + offset, top + offset, right - offset, bottom - offset),
            outline=color,
        )


def resample_filter():
    return Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS


def cover_resize(image, target_size):
    target_w, target_h = target_size
    ratio = max(target_w / float(image.width), target_h / float(image.height))
    resized = image.resize(
        (int(image.width * ratio), int(image.height * ratio)),
        resample_filter(),
    )
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def fit_resize(image, target_size):
    target_w, target_h = target_size
    ratio = min(target_w / float(image.width), target_h / float(image.height))
    return image.resize(
        (max(1, int(image.width * ratio)), max(1, int(image.height * ratio))),
        resample_filter(),
    )


def draw_vertical(draw, text, x, y, font, fill, gap=8):
    current_y = y
    for char in text:
        if char in "，。！？；：":
            current_y += max(5, font.size // 3)
            continue
        char_w, _ = measure_text(draw, char, font)
        draw.text((x - char_w // 2, current_y), char, font=font, fill=fill)
        current_y += font.size + gap
    return current_y


def draw_vertical_clauses(draw, poem, start_x, start_y, font, fill, col_gap):
    clauses = []
    current = ""
    for char in poem:
        if char in "，。！？；":
            if current:
                clauses.append(current)
                current = ""
        else:
            current += char
    if current:
        clauses.append(current)
    x = start_x
    for clause in clauses:
        draw_vertical(draw, clause, x, start_y, font, fill, gap=7)
        x -= col_gap


def draw_soundscape_mark(image, xy, size, color, width=3):
    """Place the generated one-stroke listening-and-poetry emblem."""
    rgba = color if len(color) == 4 else color + (255,)
    source = Image.open(str(MARK_PATH)).convert("RGBA")
    alpha = source.split()[3]
    bounds = alpha.getbbox()
    if bounds:
        source = source.crop(bounds)
        alpha = source.split()[3]
    width_px = max(1, int(size * source.width / float(source.height)))
    resampling = getattr(Image, "Resampling", Image)
    alpha = alpha.resize((width_px, size), resampling.LANCZOS)
    opacity = rgba[3] / 255.0
    alpha = alpha.point(lambda value: int(value * opacity))
    mark = Image.new("RGBA", (width_px, size), rgba[:3] + (0,))
    mark.putalpha(alpha)
    destination = (int(xy[0]), int(xy[1]))
    if image.mode == "RGBA":
        image.alpha_composite(mark, dest=destination)
    else:
        image.paste(mark, destination, mark)


def mute_warm_reds(image, strength=0.55):
    """Quiet red foliage so it cannot read as a graphic accent."""
    image = image.convert("RGB")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue = pixels[x, y]
            if red > green * 1.12 and red > blue * 1.08 and red > 70:
                target = int((green + blue) / 2.0)
                red = int(red * (1.0 - strength) + target * strength)
                green = int(green * (1.0 - strength * 0.22) + target * strength * 0.22)
                pixels[x, y] = (red, green, blue)
    return image


def blend_ink_fragment(canvas, source, polygon, opacity=96, blur_radius=150):
    """Blend a secondary scene through a soft irregular ink-wash mask."""
    fragment = cover_resize(source.convert("RGB"), canvas.size)
    fragment = ImageEnhance.Contrast(fragment).enhance(0.92)
    fragment = ImageEnhance.Color(fragment).enhance(0.42)
    fragment = ImageEnhance.Brightness(fragment).enhance(1.02)
    fragment = mute_warm_reds(fragment, strength=0.72).convert("RGBA")

    mask = Image.new("L", canvas.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.polygon(polygon, fill=opacity)
    mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))
    return Image.composite(fragment, canvas.convert("RGBA"), mask)


def add_right_paper_wash(image):
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pixels = overlay.load()
    start = int(image.width * 0.56)
    for x in range(start, image.width):
        progress = (x - start) / float(max(1, image.width - start))
        alpha = int(18 + 185 * (progress ** 0.72))
        for y in range(image.height):
            pixels[x, y] = (245, 239, 224, alpha)
    return Image.alpha_composite(image.convert("RGBA"), overlay)


def save_jpeg_under_limit(image, path, max_bytes=MAX_JPG_BYTES):
    image = image.convert("RGB")
    for quality in (94, 91, 88, 85, 82, 78, 74, 70):
        image.save(str(path), "JPEG", quality=quality, optimize=True, dpi=(300, 300))
        if path.stat().st_size <= max_bytes:
            return
    raise RuntimeError("Image exceeds size limit: {}".format(path))


def compose_work(item):
    source_path = SOURCE_DIR / item["source"]
    if not source_path.exists():
        raise FileNotFoundError(str(source_path))

    base = cover_resize(Image.open(str(source_path)).convert("RGB"), WORK_SIZE)
    base = ImageEnhance.Contrast(base).enhance(1.04)
    base = ImageEnhance.Color(base).enhance(0.84)
    base = mute_warm_reds(base, strength=0.62)
    canvas = add_right_paper_wash(base)
    draw = ImageDraw.Draw(canvas)

    title_font = load_font(CALLIGRAPHY_FONT, 88)
    body_font = load_font(CALLIGRAPHY_FONT, 47)
    meta_font = load_font(TEXT_FONT, 28)

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
    title_end = draw_vertical(draw, item["title"], title_x, 170, title_font, ink, gap=14)
    author = "〔{}〕{}".format(item["dynasty"], item["author"])
    draw_vertical(draw, author, 1178, title_end + 64, meta_font, muted, gap=8)
    draw_soundscape_mark(
        canvas,
        (1102, 184),
        78,
        mark_colors.get(item["sound"], (88, 91, 80, 145)),
        width=2,
    )

    draw_vertical_clauses(
        draw,
        item["poem"],
        start_x=1055,
        start_y=360,
        font=body_font,
        fill=ink,
        col_gap=72,
    )

    output = WORKS_DIR / "{}_{}.jpg".format(item["index"], item["title"])
    save_jpeg_under_limit(canvas, output)
    return output


def wrap_text(draw, text, font, max_width):
    lines = []
    current = ""
    for char in text:
        candidate = current + char
        text_width, _ = measure_text(draw, candidate, font)
        if text_width <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, text, xy, font, fill, max_width, line_gap=18, max_lines=None):
    x, y = xy
    lines = wrap_text(draw, text, font, max_width)
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


def create_a3_poster(work_paths):
    sources = [
        Image.open(str(SOURCE_DIR / item["source"])).convert("RGB")
        for item in SERIES
    ]
    canvas = cover_resize(sources[2], A3_SIZE).convert("RGBA")
    canvas = blend_ink_fragment(
        canvas,
        sources[0],
        [(0, 0), (1380, 0), (2050, 720), (1630, 1320), (560, 1260), (0, 920)],
        opacity=88,
        blur_radius=165,
    )
    canvas = blend_ink_fragment(
        canvas,
        sources[1],
        [(0, 1080), (780, 930), (1940, 1430), (2150, 2050), (1180, 2260), (0, 1950)],
        opacity=82,
        blur_radius=170,
    )
    canvas = blend_ink_fragment(
        canvas,
        sources[3],
        [(0, 2250), (840, 2100), (2050, 2630), (2180, 3430), (980, 3630), (0, 3260)],
        opacity=90,
        blur_radius=175,
    )
    canvas = blend_ink_fragment(
        canvas,
        sources[4],
        [(0, 3440), (980, 3300), (2180, 3820), (2350, 4961), (0, 4961)],
        opacity=92,
        blur_radius=180,
    )
    canvas = ImageEnhance.Contrast(canvas).enhance(0.94)
    canvas = ImageEnhance.Color(canvas).enhance(0.48)
    canvas = ImageEnhance.Brightness(canvas).enhance(0.96)
    canvas = mute_warm_reds(canvas, strength=0.72)
    canvas = canvas.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    ink = (28, 26, 23, 255)
    muted = (82, 68, 52, 240)
    title_font = load_font(CALLIGRAPHY_FONT, 245)
    subtitle_font = load_font(TEXT_FONT, 62)
    label_font = load_font(TEXT_FONT, 42)

    draw_vertical(draw, SERIES_TITLE, 2970, 620, title_font, ink, gap=22)
    draw_vertical(
        draw,
        "让不可见的声音穿过五重诗境",
        2665,
        690,
        subtitle_font,
        muted,
        gap=12,
    )
    sounds = ["鸟鸣", "钟声", "猿啼", "人语回响", "夜雨"]
    for index, sound in enumerate(sounds):
        draw_vertical(
            draw,
            sound,
            3020 - index * 155,
            2900,
            label_font,
            ink if index in (0, 4) else muted,
            gap=9,
        )
    draw_soundscape_mark(
        canvas,
        (2940, 4095),
        205,
        (75, 84, 79, 72),
        width=3,
    )

    save_jpeg_under_limit(canvas, A3_PATH)
    return A3_PATH


def pdf_page():
    return Image.new("RGB", PDF_PAGE_SIZE, (244, 239, 226))


def page_header(draw, page_no, title):
    ink = (32, 29, 25)
    muted = (105, 88, 66)
    title_font = load_font(TEXT_FONT, 65)
    small_font = load_font(LATIN_FONT, 24)
    draw.text((120, 100), title, font=title_font, fill=ink)
    draw.text((1450, 118), "{:02d} / 08".format(page_no), font=small_font, fill=muted)
    draw.line((120, 200, 1634, 200), fill=(162, 132, 91), width=3)


def create_process_pdf(work_paths):
    from build_process_pdf_v2 import build_pdf

    return build_pdf()

    pages = []
    ink = (32, 29, 25)
    muted = (92, 78, 61)
    accent = (104, 105, 88)
    title_font = load_font(CALLIGRAPHY_FONT, 165)
    heading_font = load_font(TEXT_FONT, 54)
    body_font = load_font(TEXT_FONT, 34)
    small_font = load_font(TEXT_FONT, 27)
    latin_font = load_font(LATIN_FONT, 24)

    # 1. Cover
    page = pdf_page()
    draw = ImageDraw.Draw(page)
    cover = fit_resize(Image.open(str(A3_PATH)).convert("RGB"), (920, 1300))
    page.paste(cover, (714, 105))
    draw_rect_outline(
        draw,
        (714, 105, 714 + cover.width, 105 + cover.height),
        (117, 94, 66),
        width=3,
    )
    draw_soundscape_mark(page, (130, 170), 250, accent + (220,), width=5)
    draw.text((120, 620), SERIES_TITLE, font=title_font, fill=ink)
    draw.text((130, 830), SERIES_SUBTITLE, font=heading_font, fill=muted)
    draw_wrapped(draw, SERIES_STATEMENT, (130, 990), body_font, ink, 520, line_gap=22, max_lines=8)
    draw.text((130, 2225), "AIGC-图片类 · 创作过程说明", font=small_font, fill=accent)
    pages.append(page)

    # 2. Concept
    page = pdf_page()
    draw = ImageDraw.Draw(page)
    page_header(draw, 2, "01  选题与问题意识")
    draw.text((120, 280), "为什么从“声音”进入古诗？", font=heading_font, fill=ink)
    concept = (
        "古诗中的声音往往没有可见形体，却承担着空间定位、情绪转折和时间推进。"
        "本系列不复刻诗句表面场景，而把声音的扩散、回返、断续、叠加和消隐转化为构图规则，"
        "建立听觉与东方山水空间之间的视觉语法。"
    )
    y = draw_wrapped(draw, concept, (120, 390), body_font, ink, 1480, line_gap=26)
    draw.text((120, y + 85), "五种声音 / 五种空间机制", font=heading_font, fill=ink)
    y += 190
    for item in SERIES:
        draw.rectangle((120, y, 260, y + 68), fill=accent)
        draw.text((148, y + 12), item["sound"], font=small_font, fill=(248, 241, 225))
        draw.text((310, y + 10), "{} · {}".format(item["title"], item["concept"]), font=small_font, fill=ink)
        y += 115
    pages.append(page)

    # 3. Visual system
    page = pdf_page()
    draw = ImageDraw.Draw(page)
    page_header(draw, 3, "02  系列视觉系统")
    draw.text((120, 285), "统一规则", font=heading_font, fill=ink)
    rules = [
        "构图：左侧具象空间承载诗境，右侧宣纸留白承载诗文与余韵。",
        "媒介：当代水墨、矿物色、数字绘景与宣纸纤维共同构成。",
        "声音：以涟漪、断线、回声弧与雨线表达五种不同传播方式。",
        "文字：传统右起竖排；标题、作者、诗句形成三级信息层。",
        "色彩：每张保留独立情绪色，以灰青、雾金和墨色形成自然识别。",
    ]
    y = 390
    for number, rule in enumerate(rules, 1):
        draw.text((135, y), "{:02d}".format(number), font=latin_font, fill=accent)
        y = draw_wrapped(draw, rule, (230, y), body_font, ink, 1360, line_gap=18, max_lines=2) + 35
    draw.text((120, y + 40), "色谱", font=heading_font, fill=ink)
    swatches = [
        ((234, 225, 204), "宣纸白"),
        ((71, 72, 68), "墨灰"),
        ((95, 116, 105), "豆青"),
        ((65, 77, 88), "靛青"),
        ((126, 116, 88), "雾金"),
    ]
    x = 120
    for color, label in swatches:
        draw.rectangle((x, y + 155, x + 245, y + 340), fill=color)
        draw.text((x, y + 360), label, font=small_font, fill=ink)
        x += 300
    draw.text((120, y + 470), "声境印记与版式减法", font=heading_font, fill=ink)
    draw_soundscape_mark(page, (125, y + 580), 210, accent + (220,), width=5)
    draw_wrapped(
        draw,
        "印记采用一笔连续水墨造型，通过负空间同时暗示倾听与展开的诗卷，不使用文字、"
        "花瓣、声波或几何边框。新版删除左上角序号、右下角标签和说明线，只保留诗文、留白与印记，"
        "让视觉重心回到诗境本身。",
        (390, y + 585),
        body_font,
        ink,
        1190,
        line_gap=22,
        max_lines=5,
    )
    draw.text((390, y + 810), "删减前：序号 + 系列名 + 声音标签 + 编号说明", font=small_font, fill=muted)
    draw.text((390, y + 875), "删减后：诗文 + 声音轨迹 + 声境印记", font=small_font, fill=accent)
    draw.text((120, y + 1010), "海报构思", font=heading_font, fill=ink)
    draw_wrapped(
        draw,
        "海报以峡江作为唯一主景，不再拼接多幅画面，也不额外叠加声波线。"
        "标题与核心文案改为右侧竖排，五种声音在下方形成疏密节奏；声境印记"
        "以一笔连续水墨印记作为视觉落款，避免花瓣、文字、音量键或通用声波图标。",
        (120, y + 1110),
        body_font,
        ink,
        1480,
        line_gap=22,
        max_lines=5,
    )
    pages.append(page)

    # 4. Workflow
    page = pdf_page()
    draw = ImageDraw.Draw(page)
    page_header(draw, 4, "03  AIGC 工作流与人工介入")
    stages = [
        ("1", "文本研究", "提取声音来源、传播方式、时间、空间与情绪。"),
        ("2", "提示词设计", "限定时代、场景、构图、色谱、媒介和禁用项。"),
        ("3", "图像生成", "使用 OpenAI 图像生成能力制作无文字场景底图。"),
        ("4", "人工筛选", "检查诗意准确性、系列一致性、建筑与器物合理性。"),
        ("5", "视觉后期", "统一色调、对比度、宣纸质感与声音视觉线索。"),
        ("6", "程序排版", "使用 Codex、Python/Pillow 完成竖排、印记、海报和压缩。"),
        ("7", "提交检查", "检查5张套图、A3、PDF、视频、匿名信息和文件大小。"),
    ]
    y = 305
    for number, name, detail in stages:
        draw.ellipse((125, y, 220, y + 95), fill=accent)
        draw.text((157, y + 22), number, font=small_font, fill=(248, 241, 225))
        draw.text((270, y), name, font=heading_font, fill=ink)
        draw_wrapped(draw, detail, (270, y + 72), body_font, muted, 1290, line_gap=15, max_lines=2)
        if number != "7":
            draw.line((172, y + 100, 172, y + 230), fill=(166, 137, 96), width=4)
        y += 285
    pages.append(page)

    # 5-7. Work details
    groups = [(0, 2), (2, 4), (4, 5)]
    for page_no, (start, end) in enumerate(groups, 5):
        page = pdf_page()
        draw = ImageDraw.Draw(page)
        page_header(draw, page_no, "04  作品与提示词证据")
        y = 270
        for idx in range(start, end):
            item = SERIES[idx]
            thumb = fit_resize(Image.open(str(work_paths[idx])).convert("RGB"), (560, 820))
            page.paste(thumb, (120, y))
            draw_rect_outline(
                draw,
                (120, y, 120 + thumb.width, y + thumb.height),
                (118, 94, 67),
                width=2,
            )
            text_x = 730
            draw.text((text_x, y), "{}  {} / {}".format(item["index"], item["title"], item["sound"]), font=heading_font, fill=ink)
            draw.text((text_x, y + 85), item["poem"], font=small_font, fill=muted)
            draw_wrapped(draw, "转译逻辑：{}".format(item["concept"]), (text_x, y + 145), body_font, ink, 850, line_gap=18, max_lines=4)
            prompt_y = y + 340
            draw.text((text_x, prompt_y), "Prompt excerpt", font=latin_font, fill=accent)
            draw_wrapped(draw, item["prompt"], (text_x, prompt_y + 50), latin_font, muted, 850, line_gap=14, max_lines=8)
            draw.text((text_x, y + 690), "色谱：{}".format(item["palette"]), font=small_font, fill=ink)
            y += 1020
        pages.append(page)

    # 8. Deliverables and disclosure
    page = pdf_page()
    draw = ImageDraw.Draw(page)
    page_header(draw, 8, "05  原创说明与交付清单")
    draw.text((120, 290), "人工设计介入", font=heading_font, fill=ink)
    disclosure = (
        "底图由 OpenAI 图像生成能力辅助完成；主题策划、诗词选择、候选筛选、构图、"
        "色彩、字体、声音轨迹、声境印记、系列海报、过程编排和提交规格均由人工完成。"
        "所有古诗均属于公有领域；生成图中未使用真实人物身份、商业品牌或第三方赛事标识。"
    )
    y = draw_wrapped(draw, disclosure, (120, 400), body_font, ink, 1490, line_gap=24)
    draw.text((120, y + 80), "提交文件", font=heading_font, fill=ink)
    checklist = [
        "5张成系列 JPG 作品，每张不超过 5MB",
        "1张 A3 竖版 300dpi 宣传海报",
        "1份创作过程 PDF",
        "1段不超过3分钟的 MP4 宣讲视频",
        "平台作品名称、设计说明、作品寓意",
        "提示词、生成源图、参数与构建清单备份",
    ]
    y += 205
    for item in checklist:
        draw_rect_outline(draw, (130, y + 4, 165, y + 39), accent, width=3)
        draw.text((205, y), item, font=body_font, fill=ink)
        y += 105
    draw.text((120, 2240), "生成日期：{}".format(datetime.now().strftime("%Y-%m-%d")), font=small_font, fill=muted)
    pages.append(page)

    # Pillow 5.x does not initialize encoder state for appended PDF pages.
    for pdf_image in pages:
        pdf_image.encoderinfo = {}
        pdf_image.encoderconfig = ()
    pages[0].save(
        str(PDF_PATH),
        "PDF",
        resolution=150.0,
        save_all=True,
        append_images=pages[1:],
    )
    return PDF_PATH


def create_platform_copy():
    path = SUBMISSION_DIR / "PLATFORM_COPY.md"
    text = f"""# NCDA 平台投稿文案

## 作品名称

{PLATFORM_TITLE}

## 设计说明

《声入诗境》选取《春晓》《枫桥夜泊》《早发白帝城》《鹿柴》《夜雨寄北》五首诗，
把鸟鸣、钟声、猿啼、人语回响与夜雨的扩散、回返、断续、叠加和消隐转化为构图。
底图由 OpenAI 图像生成能力辅助完成，主题策划、诗词筛选、构图、色彩、字体、
声音轨迹、原创“声境印记”、海报和提交编排均由人工完成，形成从清晨到深夜、
从庭院到山水的东方听觉空间。

## 作品寓意

声音看不见，却能建立空间、唤起记忆并连接不同时间。《声入诗境》尝试让古诗不再
只是被阅读的文字，而成为可以被“看见”的听觉场域。五张作品从清晨到深夜、从近景
庭院到万重山水，呈现中国古典诗词中含蓄而持久的情感回声。

## AIGC 使用说明

- 图像生成：OpenAI 图像生成能力辅助制作无文字诗境底图。
- 人工介入：主题策划、诗词筛选、提示词迭代、候选筛选、构图、调色、字体、
  声音轨迹、声境印记、宣传海报和提交编排。

## 网站字段

- 参赛组别：学生-本科
- 毕业设计作品：否
- 标签：AIGC；古典诗词；视觉转译
- 使用工具：OpenAI图像生成；Codex；Python；Pillow；FFmpeg
- 内容地域：可留空
- 是否获奖/发表：按实际情况填写；如无则填写“无”
- 创作时长：按实际投入总小时数填写

## 匿名检查

提交前不得在作品图、宣传海报、过程 PDF 和宣讲视频中加入作者、学校或指导教师信息。
"""
    path.write_text(text, encoding="utf-8")
    return path


def create_video_script():
    path = VIDEO_DIR / "narration_script.md"
    text = "# 《声入诗境》宣讲词\n\n" + NARRATION_TEXT + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def probe_duration(path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return float(result.stdout.strip())


def synthesize_narration(segment_dir):
    powershell = shutil.which("powershell")
    if not powershell:
        return None

    text_path = segment_dir / "narration.txt"
    audio_path = segment_dir / "narration.wav"
    text_path.write_text(NARRATION_TEXT, encoding="utf-8")

    def ps_quote(value):
        return "'" + str(value).replace("'", "''") + "'"

    command = (
        "$voice = New-Object -ComObject SAPI.SpVoice; "
        "$token = $voice.GetVoices() | Where-Object {{ $_.GetDescription() -like '*Huihui*' }} "
        "| Select-Object -First 1; "
        "if ($token) {{ $voice.Voice = $token }}; "
        "$stream = New-Object -ComObject SAPI.SpFileStream; "
        "$stream.Open({audio}, 3, $false); "
        "$voice.AudioOutputStream = $stream; "
        "$voice.Rate = -1; $voice.Volume = 100; "
        "$text = Get-Content -Raw -Encoding UTF8 {text}; "
        "[void]$voice.Speak($text); "
        "$stream.Close()"
    ).format(audio=ps_quote(audio_path), text=ps_quote(text_path))

    try:
        subprocess.check_call([powershell, "-NoProfile", "-Command", command])
    except (OSError, subprocess.CalledProcessError):
        return None
    return audio_path if audio_path.exists() and audio_path.stat().st_size else None


def create_video(work_paths):
    video_path = VIDEO_DIR / "声入诗境_宣讲视频.mp4"
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None

    segment_dir = VIDEO_DIR / "_segments"
    if segment_dir.exists():
        shutil.rmtree(str(segment_dir))
    segment_dir.mkdir(exist_ok=True)
    slide_dir = segment_dir / "slides"
    slide_dir.mkdir(exist_ok=True)
    narration_path = synthesize_narration(segment_dir)
    narration_duration = probe_duration(narration_path) if narration_path else None

    slides = []

    def make_slide(index, work_path=None, item=None, ending=False):
        size = (1920, 1080)
        if work_path:
            source = Image.open(str(work_path)).convert("RGB")
            background = cover_resize(source, size).filter(ImageFilter.GaussianBlur(28))
            background = ImageEnhance.Brightness(background).enhance(0.38)
            slide = background
            work = fit_resize(source, (610, 930))
            work_x = 1150
            work_y = (size[1] - work.height) // 2
            slide.paste(work, (work_x, work_y))
            draw = ImageDraw.Draw(slide)
            draw_rect_outline(
                draw,
                (work_x, work_y, work_x + work.width, work_y + work.height),
                (211, 196, 168),
                width=2,
            )
            title_font = load_font(CALLIGRAPHY_FONT, 112)
            subtitle_font = load_font(TEXT_FONT, 44)
            body_font = load_font(TEXT_FONT, 34)
            number_font = load_font(LATIN_FONT, 28)
            draw.text((130, 135), "{}/05".format(item["index"]), font=number_font, fill=(205, 184, 147))
            draw.text((130, 210), item["title"], font=title_font, fill=(244, 237, 222))
            draw.text(
                (138, 355),
                "〔{}〕{}  /  {}".format(item["dynasty"], item["author"], item["sound"]),
                font=subtitle_font,
                fill=(210, 195, 168),
            )
            draw_wrapped(
                draw,
                item["concept"],
                (138, 470),
                body_font,
                (235, 226, 208),
                820,
                line_gap=24,
                max_lines=5,
            )
            draw.line((138, 815, 880, 815), fill=(169, 126, 84), width=3)
            draw.text((138, 850), SERIES_SUBTITLE, font=body_font, fill=(205, 190, 164))
        else:
            slide = Image.new("RGB", size, (27, 24, 21))
            draw = ImageDraw.Draw(slide)
            title_font = load_font(CALLIGRAPHY_FONT, 185)
            subtitle_font = load_font(TEXT_FONT, 52)
            small_font = load_font(TEXT_FONT, 34)
            accent = (111, 111, 92)
            if ending:
                draw.text((555, 310), "让声音被看见", font=title_font, fill=(239, 231, 214))
                draw.text((700, 570), SERIES_TITLE, font=subtitle_font, fill=(196, 173, 139))
            else:
                draw.text((600, 260), SERIES_TITLE, font=title_font, fill=(239, 231, 214))
                draw.text((475, 510), SERIES_SUBTITLE, font=subtitle_font, fill=(196, 173, 139))
                draw.text(
                    (650, 680),
                    "鸟鸣 · 钟声 · 猿啼 · 人语回响 · 夜雨",
                    font=small_font,
                    fill=(224, 211, 187),
                )
            draw_soundscape_mark(slide, (900, 775), 125, accent + (230,), width=4)
        slide_path = slide_dir / "slide_{:02d}.jpg".format(index)
        slide.save(str(slide_path), "JPEG", quality=94, optimize=True)
        return slide_path

    opening_duration = 6
    ending_duration = 6
    if narration_duration:
        total_duration = max(50, int(math.ceil(narration_duration)) + 3)
        work_duration = (total_duration - opening_duration - ending_duration) / 5.0
    else:
        work_duration = 8

    slides.append((make_slide(0), opening_duration))
    for idx, (path, item) in enumerate(zip(work_paths, SERIES), 1):
        slides.append((make_slide(idx, work_path=path, item=item), work_duration))
    slides.append((make_slide(6, ending=True), ending_duration))

    segment_paths = []
    for idx, (slide_path, duration) in enumerate(slides):
        segment = segment_dir / "segment_{:02d}.mp4".format(idx + 1)
        fade_out_start = max(0, duration - 0.7)
        command = [
            ffmpeg,
            "-y",
            "-loop",
            "1",
            "-i",
            str(slide_path),
            "-t",
            str(duration),
            "-vf",
            "fade=t=in:st=0:d=0.7,fade=t=out:st={}:d=0.7,format=yuv420p".format(
                fade_out_start
            ),
            "-r",
            "25",
            "-an",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-movflags",
            "+faststart",
            str(segment),
        ]
        subprocess.check_call(command)
        segment_paths.append(segment)

    concat_file = segment_dir / "concat.txt"
    concat_file.write_text(
        "\n".join("file '{}'".format(str(path).replace("\\", "/")) for path in segment_paths),
        encoding="utf-8",
    )
    slideshow_path = segment_dir / "slideshow.mp4"
    subprocess.check_call(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(slideshow_path),
        ],
    )
    if narration_path:
        total_duration = probe_duration(slideshow_path)
        subprocess.check_call(
            [
                ffmpeg,
                "-y",
                "-i",
                str(slideshow_path),
                "-i",
                str(narration_path),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-af",
                "apad",
                "-t",
                "{:.3f}".format(total_duration),
                "-movflags",
                "+faststart",
                str(video_path),
            ],
        )
    else:
        shutil.move(str(slideshow_path), str(video_path))
    shutil.rmtree(str(segment_dir))
    return video_path


def file_record(path):
    image_info = {}
    if path.suffix.lower() in (".jpg", ".jpeg", ".png"):
        with Image.open(str(path)) as image:
            image_info = {
                "width": image.width,
                "height": image.height,
                "dpi": list(image.info.get("dpi", ())),
            }
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        **image_info
    }


def write_manifest(paths):
    manifest = {
        "title": PLATFORM_TITLE,
        "category": "NCDA 1-L1 AIGC-图片类",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "deliverables": [file_record(Path(path)) for path in paths if path],
        "series": SERIES,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return MANIFEST_PATH


def main():
    ensure_dirs()
    work_paths = [compose_work(item) for item in SERIES]
    a3_path = create_a3_poster(work_paths)
    pdf_path = create_process_pdf(work_paths)
    copy_path = create_platform_copy()
    script_path = create_video_script()
    video_path = create_video(work_paths)
    manifest_path = write_manifest(
        work_paths + [a3_path, pdf_path, copy_path, script_path, video_path]
    )

    print("NCDA submission package built:")
    for path in work_paths + [a3_path, pdf_path, copy_path, script_path, video_path, manifest_path]:
        if path:
            print("- {}".format(path.relative_to(ROOT)))
    if not video_path:
        print("- Video skipped: ffmpeg is not installed.")


if __name__ == "__main__":
    main()
