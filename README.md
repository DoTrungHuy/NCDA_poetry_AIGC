# 诗境再造：古典诗词意象的 AIGC 视觉转译系统

面向未来设计师 NCDA AIGC 图片类的古诗词系列视觉生成项目。系统通过 LLM 解析古典诗词意象，生成英文文生图提示词，调用云端文生图 API 生成诗境底图，再使用 Pillow 完成竖排文字、挂轴、印章和 A3 宣传海报排版。

## 参赛定位

- 推荐赛项：NCDA 非命题赛道 1L 类 AIGC-图片类
- 作品形式：5 张或以上成系列 JPG 图片
- 过程材料：自动生成 JSON 过程日志与 `process_report.md`，可整理为创作过程 PDF
- 宣传材料：自动生成 A3 竖版 300dpi JPG 宣传海报

## 安装

```bash
pip install -r requirements.txt
```

复制 `.env.example` 为 `.env`，填写 LLM 和文生图 API Key。

## 单张生成

```bash
python main.py --poetry "床前明月光，疑是地上霜。举头望明月，低头思故乡。" --make_a3
```

输出：

- `poetry_poster.jpg`
- `poetry_poster_a3.jpg`
- `poetry_poster_process.json`

## 系列生成

```bash
python main.py --poetry_file poems_sample.txt --series_output outputs/ncda_series
```

输出结构：

```text
outputs/ncda_series/
  works/               # 5 张或以上系列作品图
  a3_posters/          # A3 竖版宣传海报
  backgrounds/         # 文生图底图
  process/             # 单张与系列 JSON 过程日志
  process_report.md    # 创作过程报告草稿
```

## 本地排版验证

不消耗 API Token，仅验证字体、挂轴排版和图片输出：

```bash
python verify_typesetting.py
```

## 提交前检查

- 系列作品不少于 5 张
- JPG 单张不超过 5MB
- 宣传海报为 A3 竖版、300dpi、JPG
- 作品图、宣传海报、宣讲视频中不要出现参赛作者、指导教师、学校名称
- 将 `process_report.md` 补充截图后导出为 PDF
