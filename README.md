# 🛰️ GEO Skills

> 让每一篇文章都被 AI 搜索引擎看见

## 这是什么

GEO Skills 是景一·寓言城堡开源的 **生成式引擎优化（Generative Engine Optimization）** 方法论和工具集。它帮你把普通文章改写为 AI 搜索引擎（ChatGPT Search、Perplexity、DeepSeek、豆包、Kimi 等）更愿意抓取、引用和推荐的版本。

**核心理念**：AI 搜索引擎的排序逻辑是「相关性 > 权威性 > 结构化程度 > 引用密度」。GEO 不改变文章的灵魂，只增加一扇让 AI 能看见的窗。

## 快速开始

### 1. 直接使用改写提示词

复制 `geo-rewrite-prompt.md` 中的 prompt，粘贴给任何 LLM，把你的文章发过去——立刻得到 GEO 优化版。

### 2. 使用命令行脚本

```bash
# 安装依赖（零依赖，纯标准库）
# 设置 API key
export OPENAI_API_KEY="sk-xxx"
export LLM_MODEL="gpt-4o-mini"  # 可选，默认 gpt-4o-mini

# 改写
python3 geo_rewrite.py --input 我的文章.md --output 我的文章-geo.md

# 指定平台
python3 geo_rewrite.py --input 我的文章.md --platform zhihu

# 只看 prompt，不调 API
python3 geo_rewrite.py --input 我的文章.md --dry-run
```

### 3. 安装为 Hermes Skill

将 `geo-rewrite-skill.md` 放入你的 Hermes Agent skills 目录，即可在对话中用自然语言触发 GEO 改写。

## 文件说明

| 文件 | 用途 | 类型 |
|------|------|------|
| `geo-rewrite-prompt.md` | GEO 改写提示词模板（复制即用） | 文档 |
| `geo-rewrite-skill.md` | Hermes Skill 定义（YAML + Markdown） | Skill 定义 |
| `geo_rewrite.py` | 可执行 GEO 改写脚本（纯标准库） | 工具 |
| `geo-annotated-demo.md` | 单篇文章 GEO 特征标注演示（17 处） | 教程 |
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
