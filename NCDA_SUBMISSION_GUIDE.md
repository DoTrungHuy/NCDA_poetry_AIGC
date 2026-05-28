# NCDA 参赛提交指南

本项目面向 **未来设计师·全国高校数字艺术设计大赛（NCDA）非命题赛道 1L AIGC-图片类** 进行整理。

> 说明：不同届别、不同赛区可能会微调提交细节，正式提交前请以 NCDA 官网与学校通知为准。本文件用于把项目材料整理成更接近参赛提交的状态。

---

## 1. 作品定位

- **作品名称**：诗境再造：古典诗词意象的 AIGC 视觉转译系统
- **推荐赛道**：非命题赛道
- **推荐类别**：1L AIGC-图片类
- **作品形式**：5 张或以上成系列 JPG 图片
- **核心方法**：LLM 解析古典诗词意象 → 生成英文文生图提示词 → 文生图模型生成诗境底图 → Python/Pillow 程序化竖排排版 → 输出系列作品与 A3 宣传海报

---

## 2. 建议提交材料清单

### 必交/核心材料

1. **系列作品图**
   - 目录：`outputs/ncda_series/works/`
   - 格式：JPG
   - 数量：不少于 5 张
   - 建议：单张不超过 5MB

2. **创作过程说明 PDF**
   - 草稿文件：`outputs/ncda_series/process_report.md`
   - 建议整理为 PDF 后提交
   - 内容应包含：创意来源、诗词意象解析、Prompt 设计、模型生成过程、筛选与后期排版逻辑

3. **A3 宣传海报**
   - 目录：`outputs/ncda_series/a3_posters/`
   - 格式：JPG
   - 规格：A3 竖版，300dpi
   - 建议：单张不超过 5MB

### 辅助证明材料

4. **过程 JSON 记录**
   - 目录：`outputs/ncda_series/process/`
   - 用途：保留每首诗对应的解析结果、提示词、模型名称、生成时间等过程证据

5. **演示视频或展示说明**
   - 可录制从输入诗词到生成作品的过程
   - 画面中不要出现作者、指导教师、学校名称等可能影响匿名评审的信息

---

## 3. 本地生成流程

### 3.1 安装依赖

```bash
pip install -r requirements.txt
```

### 3.2 配置 API Key

复制配置模板：

```bash
cp .env.example .env
```

然后填写：

```env
LLM_API_KEY=你的大语言模型APIKey
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

T2I_PROVIDER=siliconflow
T2I_API_KEY=你的文生图APIKey
T2I_MODEL=black-forest-labs/FLUX.1-schnell
```

### 3.3 生成系列作品

```bash
python main.py --poetry_file poems_sample.txt --series_output outputs/ncda_series
```

生成后主要查看：

```text
outputs/ncda_series/
├── works/               # 系列作品图
├── a3_posters/          # A3 竖版宣传海报
├── backgrounds/         # 文生图底图
├── process/             # JSON 过程日志
└── process_report.md    # 创作过程报告草稿
```

### 3.4 提交前检查

```bash
python ncda_check.py --dir outputs/ncda_series
```

如果要额外检查文件名中是否出现学校或个人信息：

```bash
python ncda_check.py --dir outputs/ncda_series --forbidden 你的姓名 学校名 指导老师名
```

---

## 4. 匿名评审与版权注意事项

- 作品图、A3 宣传海报、过程报告、演示视频中，尽量不要出现参赛作者、指导教师、学校名称。
- 使用古诗词时，优先选择已进入公有领域的古典诗词。
- AIGC 生成过程应保留 Prompt、模型名称、生成时间和筛选记录。
- 不要直接提交未经过筛选和后期整理的随机生成图，应体现设计主题、系列一致性和人工设计判断。
- 最终提交前，应再次查看当届 NCDA 官网和学校通知，确认文件格式、大小、命名和上传入口要求。

---

## 5. 项目还可以继续增强的方向

1. **统一系列视觉语言**：固定色调、纸张质感、边框比例、印章风格。
2. **增加人工筛选说明**：在过程报告里说明为什么选择某张图，淘汰了哪些方向。
3. **补充创意阐释**：强调“传统文化 + AIGC + 程序化设计”的创新点。
4. **完善展示视频**：录制 30 秒到 1 分钟的生成流程或作品展示。
5. **导出 PDF 报告**：将 `process_report.md` 补充截图后导出为正式 PDF。
