#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目名称：古诗词视觉化意境生成器 (Poetry-to-Art Pipeline)
适用于：未来设计师·全国高校数字艺术设计大赛 (NCDA) - 人工智能与前沿设计赛道
运行环境限制：轻量级终端 (如 Termux)，无本地 GPU，全部采用云端 API (RESTful)，支持本地网络代理。

设计特点：
1. PoetryParser: 解析古典诗词，通过大语言模型提取意象并生成英文 Prompt。
2. ArtGenerator: 通过文生图 API (Hugging Face / SiliconFlow) 生成意境底图。
3. VisualPosterizer: 使用 Pillow 库进行排版，支持：
   - 自动下载 Google 字体 (Ma Shan Zheng) 或自动检索系统内置字体。
   - 传统右起竖排排版 (从右往左，从上往下)。
   - 自适应字号算法，确保诗词自动缩放适配，不超出画卷。
   - 挂轴 (Hanging Scroll) 古风视觉样式设计，带有挂绳、上下轴头。
   - 自动在作者落款处生成红色的“印章”。
   - 智能边框和半透明古典纸张效果。
4. Pipeline: 面向对象封装，具备完备的异常捕获与代理配置。
"""

import os
import sys
import re
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from PIL import Image, ImageDraw, ImageFont, ImageChops

# 加载环境变量（如 API_KEY 和 代理配置）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("PoetryToArt")


NCDA_A3_SIZE = (3508, 4961)  # 297mm x 420mm at 300dpi


def _slug_index(index: int) -> str:
    return f"{index:02d}"


def _save_ncda_jpeg(img: Image.Image, output_path: str, max_mb: int = 5) -> str:
    """Save a JPG under NCDA's 5MB limit when possible."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    rgb_img = img.convert("RGB")
    for quality in (92, 88, 84, 80, 76, 72, 68):
        rgb_img.save(output_path, "JPEG", quality=quality, dpi=(300, 300), optimize=True)
        if os.path.getsize(output_path) <= max_mb * 1024 * 1024:
            return output_path
    logger.warning(f"[!] 文件仍超过 {max_mb}MB，请提交前检查: {output_path}")
    return output_path


def load_poetry_series(poetry_file: str) -> List[str]:
    """Read poems separated by blank lines or one poem per line."""
    with open(poetry_file, "r", encoding="utf-8") as f:
        raw = f.read().strip()
    if not raw:
        return []
    blocks = [block.strip() for block in re.split(r"\n\s*\n", raw) if block.strip()]
    if len(blocks) == 1:
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        return lines if len(lines) > 1 else blocks
    return blocks


def write_process_report(series_results: List[Dict[str, Any]], output_dir: str) -> str:
    """Create a Markdown process report for the NCDA process PDF."""
    report_path = os.path.join(output_dir, "process_report.md")
    lines = [
        "# 《诗境再造》AIGC 创作过程报告",
        "",
        "## 作品定位",
        "",
        "本作品以中国古典诗词为文化输入，通过大语言模型完成意象解析、风格归纳与英文提示词生成，再调用文生图模型生成视觉底图，最后使用程序化排版生成具有传统审美的系列海报。",
        "",
        "## 工具组合",
        "",
        "- LLM：诗词语义解析、意象提取、提示词生成",
        "- Text-to-Image API：生成古典诗境底图",
        "- Python + Pillow：竖排文字、挂轴版式、印章、A3 宣传海报合成",
        "",
        "## 滚图逻辑",
        "",
        "每首诗先提取标题、作者、朝代、情绪、英文画面提示词；随后追加统一系列风格词，确保作品在传统水墨、诗性氛围、东方留白方面保持一致；最终输出作品图、A3 宣传海报、JSON 过程记录。",
        "",
        "## 系列作品明细",
        "",
    ]
    for idx, item in enumerate(series_results, 1):
        metadata = item.get("metadata", {})
        lines.extend([
            f"### {idx}. {metadata.get('title', '未命名')}",
            "",
            f"- 原诗：{item.get('poetry_text', '')}",
            f"- 作者：{metadata.get('dynasty', '')} {metadata.get('author', '')}".strip(),
            f"- 意境：{metadata.get('mood', '')}",
            f"- 作品图：{item.get('work_path', '')}",
            f"- A3 宣传海报：{item.get('a3_path', '')}",
            "",
            "提示词：",
            "",
            "```text",
            item.get("full_prompt", ""),
            "```",
            "",
        ])
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return report_path


class PoetryParser:
    """诗词解析引擎：将古典诗词解析为中英文对照的结构化元数据以及文生图 Prompt"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", 
                 model: str = "gpt-3.5-turbo", proxy: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.proxy = proxy

    def parse(self, poetry_text: str) -> Dict[str, Any]:
        """
        调用 LLM API 将古诗词解析为结构化 JSON
        """
        if not self.api_key:
            raise ValueError("[Error] LLM_API_KEY 未配置，请在环境变量或 .env 中配置。")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = (
            "You are a Chinese classical literature expert and a professional AI artist. "
            "Your task is to analyze the input Chinese classical poetry and output a JSON object "
            "containing details for creating an artistic visualization. "
            "The output JSON MUST follow this format exactly:\n"
            "{\n"
            '  "title": "诗词标题",\n'
            '  "author": "作者姓名",\n'
            '  "dynasty": "朝代(如 唐/宋/清等)",\n'
            '  "translation": "英文翻译或大意 (1-2句)",\n'
            '  "image_prompt": "Highly detailed English prompt for a Text-to-Image model. Describe the scenes, landscape, subjects, colors, lighting, atmospheric perspective, and an artistic style such as \'Chinese ink wash painting\' (国画山水), \'traditional Chinese watercolor\', or \'moody digital landscape painting\'. Focus on visual and concrete details, avoiding abstract words.",\n'
            '  "mood": "视觉意境特征 (如 孤寂, 壮阔, 幽静, 喜悦)"\n'
            "}\n"
            "Do NOT return any explanation, introduction or markdown code blocks outside the JSON block. "
            "Return ONLY valid raw JSON."
        )
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请解析以下诗词：\n{poetry_text}"}
            ],
            "temperature": 0.3
        }
        
        # 提取 JSON 对象的正则表达式，防止 LLM 输出包裹在 markdown 语法中
        json_regex = re.compile(r"\{.*\}", re.DOTALL)
        
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        
        logger.info(f"[*] 正在调用 LLM ({self.model}) 进行诗词意境深度解析...")
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                proxies=proxies,
                timeout=30
            )
            response.raise_for_status()
            res_json = response.json()
            raw_content = res_json["choices"][0]["message"]["content"].strip()
            
            # 清洗 LLM 输出
            match = json_regex.search(raw_content)
            if match:
                parsed_metadata = json.loads(match.group(0))
            else:
                parsed_metadata = json.loads(raw_content)
                
            logger.info("[+] 诗词解析成功！")
            logger.info(f"    标题: {parsed_metadata.get('title')} | 作者: {parsed_metadata.get('author')}")
            logger.info(f"    生成英文画图提示词: {parsed_metadata.get('image_prompt')[:60]}...")
            return parsed_metadata
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"[Error] 调用大模型 API 网络请求失败: {e}")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            raise ValueError(f"[Error] 解析大模型返回的数据时出错 (可能是未输出标准 JSON): {e}\n原始数据: {raw_content if 'raw_content' in locals() else 'None'}")


class ArtGenerator:
    """图像生成引擎：调用云端文生图模型生成艺术底画"""
    
    def __init__(self, api_key: str, provider: str = "siliconflow", 
                 model: str = "black-forest-labs/FLUX.1-schnell", proxy: Optional[str] = None):
        self.api_key = api_key
        self.provider = provider.lower()
        self.model = model
        self.proxy = proxy

    def generate(self, prompt: str, output_path: str) -> str:
        """
        根据提示词，调用云端 API 并将返回的图像保存到本地
        """
        if not self.api_key:
            raise ValueError("[Error] T2I_API_KEY 未配置，请在环境变量或 .env 中配置。")
            
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        logger.info(f"[*] 正在调用文生图 API ({self.provider} / {self.model}) 生成艺术底图...")
        
        if self.provider == "huggingface":
            # Hugging Face Inference API (直接返回二进制图片流)
            url = f"https://api-inference.huggingface.co/models/{self.model}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {"inputs": prompt, "options": {"wait_for_model": True}}
            
            try:
                response = requests.post(url, headers=headers, json=payload, proxies=proxies, timeout=90)
                response.raise_for_status()
                
                # 保存图像
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(response.content)
                logger.info(f"[+] 图像保存成功，存至: {output_path}")
                return output_path
            except requests.exceptions.RequestException as e:
                # 异常细分，提示 Hugging Face 常见的模型加载中 (503) 错误
                if e.response is not None and e.response.status_code == 503:
                    raise RuntimeError(f"[Error] HuggingFace 模型正在加载中，请稍后重试: {e.response.text}")
                raise RuntimeError(f"[Error] HuggingFace 生成图像网络错误: {e}")
                
        elif self.provider == "siliconflow":
            # SiliconFlow API (返回包含图片 URL 的 JSON)
            url = "https://api.siliconflow.cn/v1/images/generations"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "prompt": prompt,
                "image_size": "1024x1024",
                "batch_size": 1
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, proxies=proxies, timeout=60)
                response.raise_for_status()
                res_data = response.json()
                
                # 提取图片 URL
                image_url = res_data["images"][0]["url"]
                logger.info(f"[*] 成功获取图片链接，正在下载: {image_url[:50]}...")
                
                # 下载图片流
                img_res = requests.get(image_url, proxies=proxies, timeout=30)
                img_res.raise_for_status()
                
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(img_res.content)
                logger.info(f"[+] 图像保存成功，存至: {output_path}")
                return output_path
                
            except (requests.exceptions.RequestException, KeyError, IndexError) as e:
                raise RuntimeError(f"[Error] SiliconFlow 生成/下载图像网络错误: {e}")
        else:
            raise ValueError(f"[Error] 不支持的文生图平台类型: {self.provider}，目前仅支持 huggingface 和 siliconflow")


class VisualPosterizer:
    """视觉后处理引擎：使用 Pillow (PIL) 库进行古风挂轴排版、滤镜混合以及印章渲染"""
    
    def __init__(self, font_path: Optional[str] = None, proxy: Optional[str] = None):
        self.proxy = proxy
        self.font_path = font_path

    def _draw_rect_with_width(self, draw, coords, outline_color, fill_color=None, width=1):
        """
        兼容旧版本 Pillow 的带边框宽度矩形绘制函数
        """
        left, top, right, bottom = coords
        if fill_color is not None:
            draw.rectangle([left, top, right, bottom], fill=fill_color)
        if outline_color is not None:
            for w in range(width):
                draw.rectangle([left + w, top + w, right - w, bottom - w], outline=outline_color)

    def _get_active_font(self) -> str:
        """
        获取中文字体文件路径。如果未指定或不存在，则自动下载 Google 艺术中文字体 'Ma Shan Zheng'
        """
        if self.font_path and os.path.exists(self.font_path):
            return self.font_path
            
        base_dir = os.path.dirname(os.path.abspath(__file__))
        download_dir = os.path.join(base_dir, "assets", "fonts")
        download_path = os.path.join(download_dir, "MaShanZheng-Regular.ttf")
        
        if os.path.exists(download_path):
            return download_path
            
        # 自动下载流程
        os.makedirs(download_dir, exist_ok=True)
        # 提供多个可选的 CDN 下载链接，确保国内和海外网络均畅通
        font_urls = [
            "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/mashanzheng/MaShanZheng-Regular.ttf",
            "https://raw.githubusercontent.com/google/fonts/main/ofl/mashanzheng/MaShanZheng-Regular.ttf",
            "https://fonts.gstatic.com/s/mashanzheng/v17/Wwk-HQ-4S1dEOP09sU662sQ5Uv1F.ttf"
        ]
        
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        
        for url in font_urls:
            logger.info(f"[*] 正在尝试下载 Google 艺术中文字体 (Ma Shan Zheng) 链接: {url}")
            try:
                res = requests.get(url, proxies=proxies, timeout=30)
                res.raise_for_status()
                with open(download_path, "wb") as f:
                    f.write(res.content)
                logger.info(f"[+] 字体成功保存至: {download_path}")
                return download_path
            except Exception as e:
                logger.warning(f"[!] 链接 {url} 下载失败: {e}，尝试下一个备份链接...")
                
        logger.warning("[!] 所有字体下载通道均失败，正在寻找系统备选字体...")
            
        # 本地常见系统字体兜底扫描
        fallbacks = [
            # Windows 常见字体
            "C:\\Windows\\Fonts\\simkai.ttf",   # 楷体
            "C:\\Windows\\Fonts\\msyh.ttc",    # 微软雅黑
            "C:\\Windows\\Fonts\\simsun.ttc",   # 宋体
            # Android / Termux 常见字体
            "/system/fonts/NotoSansCJK-Regular.ttc",
            "/system/fonts/DroidSansFallback.ttf",
            # Linux 常见字体
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.otf",
        ]
        
        for path in fallbacks:
            if os.path.exists(path):
                logger.info(f"[+] 成功启用系统本地备选字体: {path}")
                return path
                
        logger.error("[!] 未能发现任何有效中文字体文件。程序将使用内置的 PIL 默认字体进行渲染，渲染汉字将无法正常显示（出现乱码）。")
        return ""

    def _split_into_verses(self, poetry_text: str) -> List[str]:
        """
        将整段诗词内容按标点符号或换行符拆分成独立的诗句
        """
        # 使用正则表达式匹配常见的中文及英文标点符号进行切分
        delimiters = r"[，。？！；、“”：《》\s,;\.\?!\n\r]"
        parts = re.split(delimiters, poetry_text)
        # 过滤掉空字符串
        verses = [p.strip() for p in parts if p.strip()]
        return verses

    def generate_poster(self, bg_image_path: str, metadata: Dict[str, Any], 
                        poetry_raw_text: str, output_path: str) -> str:
        """
        核心排版算法：在生成的艺术底图上，渲染中文字体，添加挂轴、背景半透明蒙版及印章
        """
        # 1. 加载底图
        if not os.path.exists(bg_image_path):
            raise FileNotFoundError(f"[Error] 底图不存在: {bg_image_path}")
            
        img = Image.open(bg_image_path).convert("RGBA")
        W, H = img.size
        
        # 2. 准备绘制层和获取字体
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        font_file = self._get_active_font()
        
        # 3. 诗句内容整理
        title = metadata.get("title", "无题").strip()
        author = metadata.get("author", "未知").strip()
        dynasty = metadata.get("dynasty", "").strip()
        body_verses = self._split_into_verses(poetry_raw_text)
        
        if not body_verses:
            body_verses = [poetry_raw_text]

        # --------------------------------------------------
        # 4. 挂轴 (Hanging Scroll) 尺寸与定位计算
        # --------------------------------------------------
        # 挂轴底纸尺寸（约占整张画面的 50% 宽，80% 高）
        scroll_w = int(W * 0.50)
        scroll_h = int(H * 0.82)
        
        # 居中放置挂轴
        scroll_left = (W - scroll_w) // 2
        scroll_top = (H - scroll_h) // 2
        scroll_right = scroll_left + scroll_w
        scroll_bottom = scroll_top + scroll_h
        
        # 绘制半透明古风宣纸底色 (淡雅温暖的宣纸黄，带80%不透明度)
        paper_color = (250, 245, 235, 205)
        self._draw_rect_with_width(draw, [scroll_left, scroll_top, scroll_right, scroll_bottom], 
                                  outline_color=None, fill_color=paper_color)
        
        # 绘制轴头 (上下木质卷轴效果)
        roller_color = (54, 38, 27, 255) # 檀木色
        # 上轴
        self._draw_rect_with_width(draw, [scroll_left - 12, scroll_top - 10, scroll_right + 12, scroll_top], 
                                  outline_color=None, fill_color=roller_color)
        # 下轴
        self._draw_rect_with_width(draw, [scroll_left - 15, scroll_bottom, scroll_right + 15, scroll_bottom + 14], 
                                  outline_color=None, fill_color=roller_color)
        
        # 绘制挂绳 (上轴中心往上成三角形挂绳)
        mid_x = (scroll_left + scroll_right) // 2
        hanger_peak_y = scroll_top - 40
        draw.line([(mid_x, hanger_peak_y), (scroll_left + 20, scroll_top - 10)], fill=(90, 70, 50, 255), width=2)
        draw.line([(mid_x, hanger_peak_y), (scroll_right - 20, scroll_top - 10)], fill=(90, 70, 50, 255), width=2)
        
        # 绘制内框花纹线 (古典的红棕色细线双边框 - 使用兼容旧 Pillow 的绘制函数)
        border_color = (139, 69, 19, 150)
        inset = 10
        self._draw_rect_with_width(draw, [scroll_left + inset, scroll_top + inset, scroll_right - inset, scroll_bottom - inset], 
                                  outline_color=border_color, width=1)
        self._draw_rect_with_width(draw, [scroll_left + inset + 4, scroll_top + inset + 4, scroll_right - inset - 4, scroll_bottom - inset - 4], 
                                  outline_color=border_color, width=2)
                       
        # --------------------------------------------------
        # 5. 传统竖排排版计算（从右往左，自适应字号）
        # --------------------------------------------------
        # 文本可用高度与宽度限制
        padding_x = 45
        padding_y = 50
        max_h = scroll_h - padding_y * 2
        
        # 构建所有文本列 (从右向左：标题 -> 作者 -> 空白列 -> 诗句1 -> 诗句2 ...)
        columns = []
        
        # 标题列
        columns.append({"type": "title", "text": title})
        # 作者列
        author_str = f"〔{dynasty}〕{author}" if dynasty else author
        columns.append({"type": "author", "text": author_str})
        # 空白列 (做排版呼吸感)
        columns.append({"type": "spacer", "text": ""})
        # 诗句正文列
        for verse in body_verses:
            columns.append({"type": "body", "text": verse})
            
        num_cols = len(columns)
        
        # 找出正文最长的单句字数，计算基础自适应字号
        max_chars_in_body_line = max(len(col["text"]) for col in columns if col["type"] == "body")
        if max_chars_in_body_line == 0:
            max_chars_in_body_line = 5
            
        # 自适应字号预估公式，保证最长的一句在最大高度内能容纳
        # 字高 + 字间距 (假设间距为字宽的 20%)
        # L_max * F_body * 1.2 <= max_h  => F_body <= max_h / (1.2 * L_max)
        F_body = int(max_h / (1.25 * max_chars_in_body_line - 0.25))
        F_body = min(F_body, 36)  # 上限保护
        F_body = max(F_body, 16)  # 下限保护
        
        # 定义不同列的字高比例
        F_title = int(F_body * 1.35)
        F_author = int(F_body * 0.75)
        
        # 字符垂直间距比例
        S_char_ratio = 0.20 # 字高的20%作为垂直字间距
        
        # 循环验证横向宽度是否超标。如果列数太多导致总宽超过挂轴，则按比例缩小字号
        while True:
            # 每一列的横向宽度等于其字号大小 (因为汉字是方形的)
            col_widths = []
            for col in columns:
                if col["type"] == "title":
                    col_widths.append(F_title)
                elif col["type"] == "author":
                    col_widths.append(F_author)
                elif col["type"] == "spacer":
                    col_widths.append(int(F_body * 0.4))
                else:
                    col_widths.append(F_body)
                    
            # 列与列之间的水平间距
            S_col = int(F_body * 0.65)
            # 计算文字总宽
            total_text_width = sum(col_widths) + (num_cols - 1) * S_col
            
            # 判断横向是否溢出 (留出左右 padding 宽度)
            if total_text_width <= (scroll_w - padding_x * 2) or F_body <= 12:
                break
                
            # 溢出则等比例缩小字号
            F_body = max(12, int(F_body * 0.9))
            F_title = int(F_body * 1.35)
            F_author = int(F_body * 0.75)
            
        # 6. 加载 PIL 字体对象
        try:
            font_title = ImageFont.truetype(font_file, F_title) if font_file else ImageFont.load_default()
            font_author = ImageFont.truetype(font_file, F_author) if font_file else ImageFont.load_default()
            font_body = ImageFont.truetype(font_file, F_body) if font_file else ImageFont.load_default()
        except Exception as e:
            logger.error(f"[!] 实例化字体失败: {e}，将使用系统默认字体")
            font_title = font_author = font_body = ImageFont.load_default()
            
        # 计算整块文字的起始 X 轴（使其在轴纸左右居中）
        x_start_text = scroll_left + (scroll_w - total_text_width) // 2
        # 因为是从右向左书写，所以计算右边界
        x_right_text = x_start_text + total_text_width
        
        # 传统水墨黑字色
        ink_color = (25, 25, 25, 245)
        
        # 7. 开始从右往左绘制各列
        current_x = x_right_text
        for i, col in enumerate(columns):
            text = col["text"]
            col_type = col["type"]
            
            # 计算当前列的定位 X 坐标 (当前列的右端对齐)
            if col_type == "title":
                col_w = F_title
                font = font_title
                s_char = int(F_title * S_char_ratio)
            elif col_type == "author":
                col_w = F_author
                font = font_author
                s_char = int(F_author * S_char_ratio)
            elif col_type == "spacer":
                col_w = int(F_body * 0.4)
                current_x -= (col_w + S_col)
                continue
            else:
                col_w = F_body
                font = font_body
                s_char = int(F_body * S_char_ratio)
                
            # 绘制竖排汉字
            col_x = current_x - col_w # 当前列左侧起点
            
            # 计算 Y 轴起点 (标题和正文顶端对齐，作者向下错落)
            if col_type == "author":
                # 作者写在标题后面，向下平移一段距离，通常为标题高度再加两个字宽
                title_len = len(title)
                title_h = title_len * F_title + (title_len - 1) * int(F_title * S_char_ratio)
                y_start = scroll_top + padding_y + title_h + 35
            else:
                y_start = scroll_top + padding_y
                
            current_y = y_start
            for char in text:
                draw.text((col_x, current_y), char, font=font, fill=ink_color)
                current_y += (col_w + s_char) # 累加字高和字间距
                
            # --------------------------------------------------
            # 8. 落款红色“印章”绘制 (绘制在作者名字最后一字下方)
            # --------------------------------------------------
            if col_type == "author" and len(text) > 0:
                seal_size = int(F_author * 1.3) # 印章尺寸比作者字号略大
                seal_x = int(col_x + (F_author - seal_size) / 2) # 居中对齐作者列
                seal_y = int(current_y + 12) # 在名字下方留出一些间距
                
                # 绘制朱砂红印框和底色
                seal_color = (180, 20, 20, 255)
                draw.rectangle([seal_x, seal_y, seal_x + seal_size, seal_y + seal_size], fill=seal_color)
                
                # 绘制印章白字 (取作者姓名最后一个字或者“印”)
                seal_char = "印"
                if len(author) >= 1:
                    # 尝试用作者名字的最后一个字作为印章字
                    seal_char = author[-1]
                    
                # 印章文字大小
                f_seal_size = int(seal_size * 0.70)
                try:
                    font_seal = ImageFont.truetype(font_file, f_seal_size) if font_file else ImageFont.load_default()
                except Exception:
                    font_seal = ImageFont.load_default()
                    
                # 居中绘制白字
                # 兼容不同版本 Pillow 的文字大小计算
                if hasattr(font_seal, "getbbox"):
                    bbox = font_seal.getbbox(seal_char)
                    char_w = bbox[2] - bbox[0] if bbox else f_seal_size
                    char_h = bbox[3] - bbox[1] if bbox else f_seal_size
                    offset_y = bbox[1] if bbox else 0
                else:
                    char_w, char_h = font_seal.getsize(seal_char)
                    offset_y = 0
                
                tx = seal_x + (seal_size - char_w) // 2
                ty = seal_y + (seal_size - char_h) // 2 - offset_y
                
                draw.text((tx, ty), seal_char, font=font_seal, fill=(255, 255, 255, 255))
                
            # 更新下一列的 X 坐标
            current_x -= (col_w + S_col)
            
        # 9. 画面整体质感微调 (外边框与微弱暗角)
        # 绘制极细的金色海报边框
        poster_border_color = (180, 150, 100, 120)
        self._draw_rect_with_width(draw, [30, 30, W - 30, H - 30], outline_color=poster_border_color, width=2)
        
        # 10. 将蒙版图层叠加到原底图上
        final_img = Image.alpha_composite(img, overlay)
        
        # 保存为 NCDA 友好的 300dpi JPG，并尽量控制在 5MB 内
        _save_ncda_jpeg(final_img, output_path)
        
        logger.info(f"[+] 挂轴诗词海报渲染成功！保存路径: {output_path}")
        return output_path

    def generate_a3_promo(self, work_image_path: str, metadata: Dict[str, Any],
                          poetry_raw_text: str, output_path: str) -> str:
        """
        生成 NCDA 宣传海报：A3 竖版、300dpi、JPG、尽量不超过 5MB。
        """
        if not os.path.exists(work_image_path):
            raise FileNotFoundError(f"[Error] 作品图不存在: {work_image_path}")

        W, H = NCDA_A3_SIZE
        canvas = Image.new("RGBA", (W, H), (246, 241, 229, 255))
        draw = ImageDraw.Draw(canvas)
        font_file = self._get_active_font()

        try:
            font_title = ImageFont.truetype(font_file, 180) if font_file else ImageFont.load_default()
            font_subtitle = ImageFont.truetype(font_file, 74) if font_file else ImageFont.load_default()
            font_body = ImageFont.truetype(font_file, 58) if font_file else ImageFont.load_default()
            font_small = ImageFont.truetype(font_file, 44) if font_file else ImageFont.load_default()
        except Exception:
            font_title = font_subtitle = font_body = font_small = ImageFont.load_default()

        # 顶部作品图区域
        work = Image.open(work_image_path).convert("RGBA")
        target_w = W - 520
        target_h = int(H * 0.58)
        work.thumbnail((target_w, target_h), Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS)
        work_x = (W - work.width) // 2
        work_y = 300
        shadow = Image.new("RGBA", (work.width + 36, work.height + 36), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rectangle([18, 18, work.width + 18, work.height + 18], fill=(80, 60, 40, 45))
        canvas.alpha_composite(shadow, (work_x - 18, work_y - 18))
        canvas.alpha_composite(work, (work_x, work_y))

        title = metadata.get("title", "诗境再造").strip() or "诗境再造"
        author = metadata.get("author", "佚名").strip() or "佚名"
        dynasty = metadata.get("dynasty", "").strip()
        mood = metadata.get("mood", "古典诗意").strip() or "古典诗意"
        author_line = f"〔{dynasty}〕{author}" if dynasty else author

        text_top = work_y + work.height + 260
        ink = (35, 32, 28, 255)
        muted = (93, 76, 58, 255)
        red = (156, 32, 28, 255)

        draw.text((260, text_top), title, font=font_title, fill=ink)
        draw.text((270, text_top + 230), f"{author_line} | {mood}", font=font_subtitle, fill=muted)

        statement = (
            "以大语言模型解析古典诗词意象，结合文生图模型生成诗境底图，"
            "再通过程序化竖排、挂轴、印章与宣纸肌理完成视觉转译。"
        )
        wrapped = self._wrap_text(statement, font_body, W - 540)
        y = text_top + 410
        for line in wrapped[:4]:
            draw.text((270, y), line, font=font_body, fill=ink)
            y += 86

        # 底部技术链路，不包含作者、学校等匿名评审禁用信息
        tech = "LLM 意象解析 / Prompt 滚图逻辑 / AIGC 图像生成 / Python 程序化排版"
        draw.line([(270, H - 520), (W - 270, H - 520)], fill=(180, 150, 100, 180), width=4)
        draw.text((270, H - 420), tech, font=font_small, fill=muted)
        self._draw_rect_with_width(draw, [W - 520, H - 500, W - 310, H - 290], outline_color=red, width=8)
        draw.text((W - 475, H - 452), "诗境", font=font_small, fill=red)
        draw.text((W - 475, H - 382), "再造", font=font_small, fill=red)

        _save_ncda_jpeg(canvas, output_path)
        logger.info(f"[+] A3 宣传海报生成成功！保存路径: {output_path}")
        return output_path

    def _wrap_text(self, text: str, font, max_width: int) -> List[str]:
        lines = []
        current = ""
        dummy = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy)
        for char in text:
            candidate = current + char
            if hasattr(draw, "textbbox"):
                bbox = draw.textbbox((0, 0), candidate, font=font)
                width = bbox[2] - bbox[0]
            elif hasattr(font, "getbbox"):
                bbox = font.getbbox(candidate)
                width = bbox[2] - bbox[0]
            else:
                width = font.getsize(candidate)[0]
            if width <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = char
        if current:
            lines.append(current)
        return lines


class PoetryArtPipeline:
    """流水线管理器：整合解析引擎、底画生成和海报排版"""
    
    def __init__(self, parser_config: Dict[str, Any], generator_config: Dict[str, Any], 
                 posterizer_config: Dict[str, Any], proxy_config: Optional[str] = None):
        
        # 统一处理代理
        self.proxy = proxy_config
        
        # 实例化引擎
        self.parser = PoetryParser(
            api_key=parser_config.get("api_key", ""),
            base_url=parser_config.get("base_url", "https://api.openai.com/v1"),
            model=parser_config.get("model", "gpt-3.5-turbo"),
            proxy=self.proxy
        )
        
        self.generator = ArtGenerator(
            api_key=generator_config.get("api_key", ""),
            provider=generator_config.get("provider", "siliconflow"),
            model=generator_config.get("model", "black-forest-labs/FLUX.1-schnell"),
            proxy=self.proxy
        )
        
        self.posterizer = VisualPosterizer(
            font_path=posterizer_config.get("font_path"),
            proxy=self.proxy
        )

    def run(self, poetry_text: str, output_poster_path: str,
            temp_bg_path: str = "assets/images/temp_bg.png",
            a3_output_path: Optional[str] = None,
            process_json_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        运行完整管线
        """
        logger.info("=" * 60)
        logger.info("开始古诗词视觉化意境生成 (Poetry-to-Art Pipeline)")
        logger.info(f"诗词原文: {poetry_text.strip()}")
        logger.info("=" * 60)
        
        try:
            # 步骤 1：解析诗词
            metadata = self.parser.parse(poetry_text)
            
            # 步骤 2：生成艺术背景图
            # 增加一些增强中国风水墨感的辅助修饰词
            style_suffix = (
                ", high quality, traditional Chinese painting, masterwork, elegant and poetic atmosphere, "
                "coherent visual series, refined Chinese aesthetics, subtle paper texture, balanced negative space"
            )
            full_prompt = metadata.get("image_prompt", "") + style_suffix
            
            self.generator.generate(full_prompt, temp_bg_path)
            
            # 步骤 3：海报排版与输出
            work_path = self.posterizer.generate_poster(
                bg_image_path=temp_bg_path,
                metadata=metadata,
                poetry_raw_text=poetry_text,
                output_path=output_poster_path
            )

            a3_path = None
            if a3_output_path:
                a3_path = self.posterizer.generate_a3_promo(
                    work_image_path=work_path,
                    metadata=metadata,
                    poetry_raw_text=poetry_text,
                    output_path=a3_output_path
                )

            result = {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "poetry_text": poetry_text,
                "metadata": metadata,
                "full_prompt": full_prompt,
                "work_path": os.path.abspath(work_path),
                "a3_path": os.path.abspath(a3_path) if a3_path else "",
                "temp_bg_path": os.path.abspath(temp_bg_path),
                "provider": self.generator.provider,
                "t2i_model": self.generator.model,
                "llm_model": self.parser.model,
            }

            if process_json_path:
                os.makedirs(os.path.dirname(os.path.abspath(process_json_path)), exist_ok=True)
                with open(process_json_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info("=" * 60)
            logger.info(f"[SUCCESS] 恭喜！古诗词海报生成成功！")
            logger.info(f"[SUCCESS] 最终文件路径: {os.path.abspath(output_poster_path)}")
            logger.info("=" * 60)
            return result
            
        except Exception as e:
            logger.error(f"[FAILURE] 流水线执行失败: {e}", exc_info=True)
            return None

    def run_series(self, poems: List[str], output_dir: str, make_a3: bool = True) -> List[Dict[str, Any]]:
        """
        生成 NCDA AIGC 图片类所需的系列作品和过程材料。
        """
        os.makedirs(output_dir, exist_ok=True)
        work_dir = os.path.join(output_dir, "works")
        bg_dir = os.path.join(output_dir, "backgrounds")
        a3_dir = os.path.join(output_dir, "a3_posters")
        process_dir = os.path.join(output_dir, "process")
        for path in (work_dir, bg_dir, a3_dir, process_dir):
            os.makedirs(path, exist_ok=True)

        if len(poems) < 5:
            logger.warning("[!] NCDA AIGC 图片类通常要求 5 张或以上成系列套图，当前输入少于 5 首。")

        results = []
        for index, poem in enumerate(poems, 1):
            prefix = _slug_index(index)
            work_path = os.path.join(work_dir, f"{prefix}_work.jpg")
            bg_path = os.path.join(bg_dir, f"{prefix}_bg.png")
            a3_path = os.path.join(a3_dir, f"{prefix}_a3.jpg") if make_a3 else None
            process_path = os.path.join(process_dir, f"{prefix}_process.json")
            logger.info(f"[*] 正在生成系列作品 {prefix}/{len(poems)}")
            result = self.run(
                poetry_text=poem,
                output_poster_path=work_path,
                temp_bg_path=bg_path,
                a3_output_path=a3_path,
                process_json_path=process_path
            )
            if result:
                results.append(result)

        summary_path = os.path.join(process_dir, "series_process_log.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        report_path = write_process_report(results, output_dir)
        logger.info(f"[+] 系列过程日志: {summary_path}")
        logger.info(f"[+] 创作过程报告草稿: {report_path}")
        return results


def main():
    parser = argparse.ArgumentParser(description="古诗词视觉化意境生成器 (Poetry-to-Art Pipeline) - NCDA 前沿赛道")
    parser.add_argument("--poetry", type=str, default=None, help="要解析的古典诗词文本")
    parser.add_argument("--poetry_file", type=str, default=None, help="批量诗词文本文件。空行分隔多首诗，或一行一首。")
    parser.add_argument("--output", type=str, default="poetry_poster.jpg", help="输出的高清诗词海报路径")
    parser.add_argument("--series_output", type=str, default="outputs/ncda_series", help="批量系列作品输出目录")
    parser.add_argument("--make_a3", action="store_true", help="为单张作品额外生成 NCDA A3 竖版宣传海报")
    parser.add_argument("--a3_output", type=str, default="poetry_poster_a3.jpg", help="单张作品的 A3 宣传海报路径")
    parser.add_argument("--font", type=str, default=None, help="自定义中文字体文件路径 (.ttf/.otf)")
    
    # 允许命令行临时覆盖代理或API Key
    parser.add_argument("--proxy", type=str, default=None, help="手动指定代理，例如 http://127.0.0.1:7890")
    parser.add_argument("--provider", type=str, default=None, help="图片生成平台 (siliconflow / huggingface)")
    parser.add_argument("--t2i_model", type=str, default=None, help="文生图模型名称")
    
    args = parser.parse_args()

    if not args.poetry and not args.poetry_file:
        parser.error("请提供 --poetry 或 --poetry_file。NCDA 系列作品建议使用 --poetry_file。")
    
    # 优先级：命令行参数 > .env 环境变量
    proxy = args.proxy or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("proxy")
    if proxy and not proxy.startswith("http"):
        proxy = f"http://{proxy}" # 确保前缀完整
        
    llm_api_key = os.getenv("LLM_API_KEY")
    llm_base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    
    t2i_provider = args.provider or os.getenv("T2I_PROVIDER", "siliconflow")
    t2i_api_key = os.getenv("T2I_API_KEY")
    
    # 设定文生图的默认模型
    default_model = "black-forest-labs/FLUX.1-schnell"
    t2i_model = args.t2i_model or os.getenv("T2I_MODEL", default_model)
    
    # 验证 API Key
    if not llm_api_key:
        logger.error("[!] 未检测到 LLM_API_KEY。请在当前目录的 .env 文件中设置。")
        sys.exit(1)
    if not t2i_api_key:
        logger.error("[!] 未检测到 T2I_API_KEY。请在当前目录的 .env 文件中设置。")
        sys.exit(1)

    # 封装配置字典
    parser_config = {
        "api_key": llm_api_key,
        "base_url": llm_base_url,
        "model": llm_model
    }
    
    generator_config = {
        "api_key": t2i_api_key,
        "provider": t2i_provider,
        "model": t2i_model
    }
    
    posterizer_config = {
        "font_path": args.font
    }
    
    # 执行流水线
    pipeline = PoetryArtPipeline(
        parser_config=parser_config,
        generator_config=generator_config,
        posterizer_config=posterizer_config,
        proxy_config=proxy
    )

    if args.poetry_file:
        poems = load_poetry_series(args.poetry_file)
        if not poems:
            logger.error(f"[!] 未能从诗词文件读取内容: {args.poetry_file}")
            sys.exit(1)
        results = pipeline.run_series(poems, args.series_output, make_a3=True)
        success = len(results) == len(poems)
        logger.info(f"[+] 系列作品已输出到: {os.path.abspath(args.series_output)}")
    else:
        # 临时存放底图的路径，单张模式仍保持兼容
        temp_bg_path = "assets/images/temp_bg.png"
        process_json_path = os.path.splitext(args.output)[0] + "_process.json"
        success = pipeline.run(
            args.poetry,
            args.output,
            temp_bg_path,
            a3_output_path=args.a3_output if args.make_a3 else None,
            process_json_path=process_json_path
        )
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
