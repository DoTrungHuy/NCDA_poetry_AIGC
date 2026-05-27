#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
验证排版引擎脚本 (verify_typesetting.py)
用以在不消耗任何 LLM / T2I API Token 的情况下，测试 Pillow 的古风挂轴排版、中文字体下载、自适应字号及印章绘制逻辑是否正常运行。
"""

import os
from PIL import Image
from main import VisualPosterizer

def verify():
    print("[*] 启动本地排版与艺术字体渲染验证...")
    
    # 1. 自动创建一个 1024x1024 的纯色或渐变测试底图
    bg_dir = "assets/images"
    os.makedirs(bg_dir, exist_ok=True)
    temp_bg_path = os.path.join(bg_dir, "test_bg.png")
    
    # 创建一个古风淡墨色渐变背景作为测试底图
    print(f"[*] 正在生成测试底图: {temp_bg_path}")
    bg_img = Image.new("RGBA", (1024, 1024), (200, 195, 185, 255))
    bg_img.save(temp_bg_path)
    
    # 2. 模拟大语言模型返回的诗词元数据
    mock_metadata = {
        "title": "静夜思",
        "author": "李白",
        "dynasty": "唐",
        "translation": "Thinking on a Quiet Night. Looking at the bright moon, I think of my home.",
        "mood": "幽静、思乡"
    }
    poetry_raw_text = "床前明月光，疑是地上霜。举头望明月，低头思故乡。"
    
    # 3. 初始化排版引擎
    # 这里可配置本地代理，如下载字体遇到网络阻碍可填写，如: proxy="http://127.0.0.1:7890"
    posterizer = VisualPosterizer(proxy=None)
    
    # 4. 执行排版渲染
    output_poster_path = "poetry_poster_test.jpg"
    try:
        print("[*] 正在渲染挂轴海报...")
        output_path = posterizer.generate_poster(
            bg_image_path=temp_bg_path,
            metadata=mock_metadata,
            poetry_raw_text=poetry_raw_text,
            output_path=output_poster_path
        )
        print(f"[+] 验证成功！生成的测试海报已保存至: {os.path.abspath(output_path)}")
        print("[+] 请打开该图片文件检查是否包含：")
        print("    1. 居中的古典宣纸色挂轴底纸及木质轴头")
        print("    2. 三角形的挂绳挂痕")
        print("    3. 标题“静夜思”和作者“〔唐〕李白”")
        print("    4. 诗句从右向左的竖排版")
        print("    5. 李白名字下方印有白字“白”或“印”的红色印章")
        print("    6. 周围精致的金棕色双细线花纹框")
    except Exception as e:
        print(f"[!] 验证失败，发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
