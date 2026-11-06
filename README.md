# 高中专属词光 · High School Word Atlas

基于 [Word Atlas（词光）](https://github.com/designfuchen/word-atlas) 开源项目制作的高中英语教材专属版本。

在线访问：[https://dage-ai-edu.github.io/high-school-word-atlas/](https://dage-ai-edu.github.io/high-school-word-atlas/)

## 当前词库

- 教材范围：人教版高中英语必修第一至第三册、选择性必修第一至第四册。
- 学习范围：初中基础、高一上、高一下、高二、高三。
- 用户提供的 50 页词表：2596 条，其中独立词记录 2147 条、短语或多词项目 449 条。
- 初中基础与高中教材词合并去重：3698 词。
- 与词光官方 7298 词精确重合：3159 词。
- 复用初中版补充词条：88 词。
- 新建教材补充词条：451 词。

3159 个官方重合词保留词光原版的释义、插画、英美发音、例句与搭配（以原词条实际资源为准）。教材补充词使用教材中文释义、同版式视觉词卡与设备语音，后续可继续补充例句、搭配和独立录音。

## 教材阶段映射

| 学习范围 | 教材册次 | 首次出现词数 |
| --- | --- | ---: |
| 初中基础 | 初中专属词光累计词 | 1996 |
| 高一上 | 必修第一册 | 173 |
| 高一下 | 必修第二、三册 | 492 |
| 高二 | 选择性必修第一、二册 | 540 |
| 高三 | 选择性必修第三、四册 | 497 |

学校实际教学进度可能不同，因此每个词同时保留教材册次；年级映射仅作为学习入口。

## 本地运行

需要 Node.js 20+：

```bash
npm ci
npm run dev
```

构建和检查：

```bash
npm test
npm run check:atlas
npm run build
```

## 数据位置

- `data/word-atlas.json`：完整词条数据。
- `data/word-atlas.csv`：便于审阅的表格版本。
- `data/high-school-source/`：教材逐册明细、去重汇总、重合词、补充词和构建摘要。
- `public/atlas/`：网页实际加载的分块词条、插画与音频。

重新生成高中词库：

```bash
python3 scripts/build_high_school_atlas.py \
  --source-csv /path/to/高中教材单词_去重汇总.csv \
  --official-repo /path/to/designfuchen-word-atlas \
  --junior-repo /path/to/junior-word-atlas
```

## 来源与许可

- 上游代码与官方词光内容来自 [designfuchen/word-atlas](https://github.com/designfuchen/word-atlas)。
- 本项目沿用并保留上游仓库的许可证与来源说明。
- 教材补充词的中文释义来自用户提供的本地教材词汇表，仅供个人学习；公开发布前需再次核对教材内容的授权边界。
- 本项目不包含账号系统；学习记录默认保存在当前浏览器，可在“我的”页面导出备份。
