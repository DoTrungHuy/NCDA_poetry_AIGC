# 诗境再造：古典诗词意象的 AIGC 视觉转译系统

面向 **未来设计师·全国高校数字艺术设计大赛（NCDA）非命题赛道 1L AIGC-图片类** 的古诗词系列视觉生成项目。

本项目通过 **LLM 解析古典诗词意象**，生成英文文生图提示词，调用云端文生图 API 生成诗境底图，再使用 **Python + Pillow** 完成竖排文字、挂轴、印章、宣纸肌理和 A3 宣传海报排版，最终形成可用于 NCDA 提交的系列图片作品与过程材料。

---

## 参赛定位

- **推荐赛事**：未来设计师·全国高校数字艺术设计大赛（NCDA）
- **推荐赛道**：非命题赛道
- **推荐类别**：1L AIGC-图片类
- **作品形式**：5 张或以上成系列 JPG 图片
- **过程材料**：自动生成 JSON 过程日志与 `process_report.md`，可整理为创作过程 PDF
- **宣传材料**：自动生成 A3 竖版 300dpi JPG 宣传海报

> 正式提交前请以当届 NCDA 官网与学校通知为准。项目内的 `NCDA_SUBMISSION_GUIDE.md` 提供了更完整的提交整理说明。

---

## 项目特点

- **传统文化主题**：以古典诗词为输入，围绕意象、情绪、空间与东方审美进行视觉转译。
- **AIGC 生成链路完整**：包含诗词解析、Prompt 生成、文生图、程序化排版、过程记录。
- **系列化输出**：支持一次生成 5 张或以上系列作品，适合 AIGC 图片类提交。
- **匿名评审友好**：宣传海报默认不包含作者、学校、指导教师等信息。
- **提交前检查**：提供 `ncda_check.py` 检查作品数量、JPG 大小、A3 海报、过程材料等。

---

## 安装

```bash
pip install -r requirements.txt
```

复制 `.env.example` 为 `.env`，填写 LLM 和文生图 API Key。

```bash
cp .env.example .env
```

示例配置：

```env
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

T2I_PROVIDER=siliconflow
T2I_API_KEY=your_t2i_api_key_here
T2I_MODEL=black-forest-labs/FLUX.1-schnell
```

---

## 单张生成

```bash
python main.py --poetry "床前明月光，疑是地上霜。举头望明月，低头思故乡。" --make_a3
```

输出：

- `poetry_poster.jpg`
- `poetry_poster_a3.jpg`
- `poetry_poster_process.json`

---

## 系列生成（推荐用于 NCDA）

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
  process_report.md    # 创作过程报告草稿，可补图后导出 PDF
```

---

## 本地排版验证

不消耗 API Token，仅验证字体、挂轴排版和图片输出：

```bash
python verify_typesetting.py
```

---

## NCDA 提交前检查

生成系列作品后运行：

```bash
python ncda_check.py --dir outputs/ncda_series
```

如果要检查文件名中是否出现作者、学校、指导老师等匿名评审不建议出现的信息：

```bash
python ncda_check.py --dir outputs/ncda_series --forbidden 你的姓名 学校名 指导老师名
```

脚本会检查：

- 系列作品是否不少于 5 张
- JPG 单张是否不超过 5MB
- A3 宣传海报是否接近 297mm × 420mm、300dpi
- 是否存在 `process_report.md`
- 是否存在过程 JSON 记录
- 文件名中是否出现指定的匿名评审敏感词

---

## 提交前人工检查

- 系列作品不少于 5 张。
- JPG 单张建议不超过 5MB。
- 宣传海报为 A3 竖版、300dpi、JPG。
- 作品图、宣传海报、过程报告、演示视频中尽量不要出现参赛作者、指导教师、学校名称。
- 将 `process_report.md` 补充生成截图、Prompt 迭代截图、筛选说明后导出为 PDF。
- 最终提交前再次查看当届 NCDA 官网和学校通知，确认上传入口、命名规范、文件大小和补充材料要求。

---

## 目录说明

```text
NCDA_poetry_AIGC/
├── main.py                     # 主生成管线
├── verify_typesetting.py        # 本地排版验证脚本
├── ncda_check.py                # NCDA 提交前检查脚本
├── NCDA_SUBMISSION_GUIDE.md     # NCDA 参赛提交指南
├── poems_sample.txt             # 系列生成示例诗词
├── requirements.txt             # Python 依赖
├── .env.example                 # API 配置模板
└── README.md
```

---

## 作品创新点

1. **文化输入可解释**：以古典诗词文本为源头，保留题名、作者、朝代、意象与情绪。
2. **生成过程可追溯**：每张作品保存结构化 JSON，记录模型、Prompt 和生成时间。
3. **人工设计介入明确**：通过程序化排版控制竖排文字、挂轴、印章、留白与 A3 宣传版式。
4. **系列视觉统一**：统一水墨质感、宣纸肌理、传统构图和东方留白。

---

**Made with ❤️ for NCDA AIGC Design**
