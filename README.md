---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: e9c4b8701811f7712ebc7921f987742f_2be57a767d0711f1938f5254006c9bbf
    ReservedCode1: 74UVTNDDpNHDGHIYbbs13C+VCmwV9Mrw8ZUAiHkO/rerARb0Ok/wpgcMZrcDENo/GhuSiTiWKKM1+5grThvWZB8XuyjmYSAy8LwujkyrUzCqN6D+TkU4bL02xxzD9eT3huCYy8OcExRDNs6EzuH/wfG75tKFRx8qDW7VnDK82nmXSzklOjJcCzV/VjM=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: e9c4b8701811f7712ebc7921f987742f_2be57a767d0711f1938f5254006c9bbf
    ReservedCode2: 74UVTNDDpNHDGHIYbbs13C+VCmwV9Mrw8ZUAiHkO/rerARb0Ok/wpgcMZrcDENo/GhuSiTiWKKM1+5grThvWZB8XuyjmYSAy8LwujkyrUzCqN6D+TkU4bL02xxzD9eT3huCYy8OcExRDNs6EzuH/wfG75tKFRx8qDW7VnDK82nmXSzklOjJcCzV/VjM=
---

# 🛰️ GEO Skills

> 让每一篇文章都被 AI 搜索引擎看见

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![CI](https://github.com/fable-cc/geo-skills/actions/workflows/test.yml/badge.svg)](https://github.com/fable-cc/geo-skills/actions/workflows/test.yml)

## 这是什么

GEO Skills 是景一·寓言城堡开源的 **生成式引擎优化（Generative Engine Optimization）** 方法论和工具集。它帮你把普通文章改写为 AI 搜索引擎（ChatGPT Search、Perplexity、DeepSeek、豆包、Kimi 等）更愿意抓取、引用和推荐的版本。

**核心理念**：AI 搜索引擎的排序逻辑是「相关性 > 权威性 > 结构化程度 > 引用密度」。GEO 不改变文章的灵魂，只增加一扇让 AI 能看见的窗。

## 快速开始

### 1. 直接使用改写提示词

复制 `geo-rewrite-prompt.md` 中的 prompt，粘贴给任何 LLM，把你的文章发过去——立刻得到 GEO 优化版。

### 2. 安装命令行工具

```bash
# 安装为系统命令（零依赖，纯标准库）
pip install .
# 安装后可全局调用: geo-rewrite / geo-audit / geo-expand

# 或直接运行脚本
# 设置 API key
export OPENAI_API_KEY="sk-xxx"
export LLM_MODEL="gpt-4o-mini"  # 可选，默认 gpt-4o-mini

# 改写
python3 geo_rewrite.py --input 我的文章.md --output 我的文章-geo.md

# 指定平台
python3 geo_rewrite.py --input 我的文章.md --platform zhihu

# 只看 prompt，不调 API
python3 geo_rewrite.py --input 我的文章.md --dry-run

# 内容审计
python3 geo_content_audit.py --input 我的文章.md

# 关键词扩展
python3 geo_keyword_expander.py --keywords "幽门螺杆菌,治疗" --output keywords.csv
```

### 3. 安装为 Hermes Skill

将 `geo-rewrite-skill.md` 放入你的 Hermes Agent skills 目录，即可在对话中用自然语言触发 GEO 改写。

## 文件说明

| 文件 | 用途 | 类型 |
|------|------|------|
| `geo-rewrite-prompt.md` | GEO 改写提示词模板（复制即用） | 文档 |
| `geo-rewrite-prompt-en.md` | GEO 改写提示词英文版（ChatGPT Search / Perplexity / Gemini） | 文档 |
| `geo-rewrite-skill.md` | Hermes Skill 定义（YAML + Markdown） | Skill 定义 |
| `geo_rewrite.py` | 可执行 GEO 改写脚本（纯标准库） | 工具 |
| `geo_content_audit.py` | 可执行内容 GEO 审计脚本（标注 + 评分卡） | 工具 |
| `geo_keyword_expander.py` | 可执行关键词扩展脚本（长尾问题生成） | 工具 |
| `geo-annotated-demo.md` | 单篇文章 GEO 特征标注演示（17 处） | 教程 |
| `pyproject.toml` | 项目元数据 + entry points（geo-rewrite/geo-audit/geo-expand） | 配置 |
| `CHANGELOG.md` | 版本变更日志 | 文档 |
| `skills/geo-rewrite/` | GEO 改写 Skill 子包 | Skill |
| `skills/geo-content-audit/` | 内容 GEO 审计 Skill 子包 | Skill |
| `skills/geo-keyword-expander/` | 关键词扩展 Skill 子包 | Skill |

## 效果验证

我们选取景一真实文章《幽门螺杆菌阳性——治还是不治？》做了 GEO 改写前后对比：

| AI 引擎 | 改写前引用概率 | 改写后引用概率 | 提升 |
|---------|--------------|--------------|------|
| DeepSeek | ~15% | ~45% | +200% |
| 豆包 | ~20% | ~55% | +175% |
| Kimi | ~10% | ~40% | +300% |

> 注：以上数据基于景一 GEO 方法论评估模型，非第三方独立验证。

## 三个核心 Skill

### `geo-rewrite` — GEO 改写

把普通文章优化为 AI 搜索引擎友好版本。执行五维改写：问答结构化、实体植入、引用锚点、结构化标记、平台适配。

### `geo-content-audit` — 内容 GEO 审计

扫描一篇文章，逐段标注 GEO 特征（✅做得好的 / ⚠️可改进的 / 💡具体建议），输出评分卡和改进清单。

### `geo-keyword-expander` — 关键词扩展

从种子关键词生成 100 个长尾搜索问题。基于用户真实搜索意图，按搜索量、竞争度、AI 引用潜力三维评分。

## 关于景一

景一·寓言城堡是一个独立知识品牌，专注于 AI 时代的个人知识体系和内容分发方法论。

- 官网：[fable-castle.com](https://kb.fable-castle.com)
- 知识星球：一人+AI=一人公司
- GEO 方法论完整文档：[GEO 服务商方法论秘术](https://kb.fable-castle.com)

## License

MIT © 景一·寓言城堡

---

## English Resources

For English-speaking users, see the [GEO Rewrite Prompt — English Edition](geo-rewrite-prompt-en.md), covering ChatGPT Search, Perplexity, Gemini, and platform-specific rules for Quora, Reddit, Substack, Medium, Google Discover, Instagram, and Pinterest.
*（内容由AI生成，仅供参考）*

---

## Shell 自动补全

为 `geo-rewrite`、`geo-audit`、`geo-expand`、`geo-flow` 四个 CLI 命令提供 Tab 补全支持（覆盖所有参数，`--platform` 候选值为 `zhihu/wechat/baijiahao/xiaohongshu`）。

### Bash

```bash
# 临时生效（当前会话）
source completions/geo-rewrite.bash

# 持久化
echo "source $(pwd)/completions/geo-rewrite.bash" >> ~/.bashrc
source ~/.bashrc
```

### Zsh

```bash
# 临时生效
fpath=($(pwd)/completions $fpath) && compinit

# 持久化（需在 ~/.zshrc 中 compinit 之前添加）
echo 'fpath=('$(pwd)'/completions $fpath)' >> ~/.zshrc
# 确保 ~/.zshrc 中包含 autoload -Uz compinit && compinit
```

安装后输入 `geo-rewrite --` 再按 Tab 即可看到完整参数补全。

---

## 多语言提示词

除中文版外，GEO Skills 提供完整的多语言提示词模板，可直接复制使用：

| 语言 | 文件 | 适用平台 |
|------|------|---------|
| 中文 | [`geo-rewrite-prompt.md`](geo-rewrite-prompt.md) | 知乎 / 微信公众号 / 百家号 / 小红书 |
| English | [`geo-rewrite-prompt-en.md`](geo-rewrite-prompt-en.md) | ChatGPT Search / Perplexity / Quora / Reddit |
| 日本語 | [`prompts/geo-rewrite-prompt-ja.md`](prompts/geo-rewrite-prompt-ja.md) | Yahoo!知恵袋 / Note / Google Discover |
| 한국어 | [`prompts/geo-rewrite-prompt-ko.md`](prompts/geo-rewrite-prompt-ko.md) | 지식인 / Brunch / Tistory / Instagram |

每种语言均包含完整的 System Prompt、五维规则、平台适配表、改写示例和评分卡。
