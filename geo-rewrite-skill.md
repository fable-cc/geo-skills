---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: e9c4b8701811f7712ebc7921f987742f_2d2db99b7d0711f18d11525400e6dd8f
    ReservedCode1: HXBGyuS1jt3cz1vQj+y/U//D2Uil6uT1oPCNGzR2RIplfG+wxOBmhUqYHXQX7aAoVsuqFcMHUEAyLpBnsB2H9SiIl1vLp/lCg0QQGS/je7xDnCM1UyGz8ty5zwVHaGJVy3rm2J6l4fTiM3mcWidM8HiYEygYv6mXfEAPTJBg5mP7WbN5u1+Ijha5g3g=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: e9c4b8701811f7712ebc7921f987742f_2d2db99b7d0711f18d11525400e6dd8f
    ReservedCode2: HXBGyuS1jt3cz1vQj+y/U//D2Uil6uT1oPCNGzR2RIplfG+wxOBmhUqYHXQX7aAoVsuqFcMHUEAyLpBnsB2H9SiIl1vLp/lCg0QQGS/je7xDnCM1UyGz8ty5zwVHaGJVy3rm2J6l4fTiM3mcWidM8HiYEygYv6mXfEAPTJBg5mP7WbN5u1+Ijha5g3g=
---



# GEO 改写

## When to use

当用户需要将一篇普通文章转化为 AI 搜索引擎友好版本时触发。常见场景：

- 用户提供文章链接或正文，要求"做 GEO 优化"或"改写为 AI 友好版"
- 用户说"让这篇文章更容易被 AI 搜到"、"帮我优化搜索排名"
- 用户在发布内容前想检查 GEO 质量
- 指定平台场景：知乎 / 公众号 / 百家号 / 小红书的内容发布前优化

不适用场景：
- 纯文学作品、诗歌、小说（GEO 改写会破坏文学性）
- 技术文档、API 文档（应走结构化文档标准，而非 GEO）

## How it works

本 Skill 执行五维 GEO 改写流程：

### 第一步：结构分析

读取原文，提取核心问答对、关键词、实体词（品牌/人名/地名/概念），评估当前 GEO 得分。

### 第二步：五维改造

1. **问答结构化**：在开头 150 字内直接回答核心问题，结论前置
2. **实体植入**：确保品牌实体在正文中出现 3 次以上，加限定词形成差异化
3. **引用锚点**：所有数据和结论标注来源（机构 + 年份 + 报告名称）
4. **结构化标记**：H2/H3 + 列表 + 加粗关键词 + FAQ 区块
5. **平台适配**：根据目标平台（知乎/公众号/百家号/小红书）调整策略

### 第三步：质量检查

用 6 项 checklist + 评分卡对改写结果打分，低于 42 分（满分 60）不输出。

### 评分卡

| 维度 | 满分 |
|------|------|
| 问答结构化 | 10 |
| 实体植入 | 10 |
| 引用锚点 | 10 |
| 结构化标记 | 10 |
| 平台适配 | 10 |
| 可读性 | 10 |
| **总分** | **60** |

## 输入格式

```
--input 原始文章.md
[--platform zhihu|wechat|baijiahao|xiaohongshu]  # 可选，默认通用
[--dry-run]  # 只输出 prompt，不调 API
```

## 输出

1. 改写后的 Markdown 文件（保存为 `原名-geo.md`）
2. 终端输出改写摘要：
   - 改了什么（结构、实体、引用、标记、平台各维度的具体改动）
   - 为什么改（每条改动对应的 GEO 原理）
   - GEO 评分卡（6 项得分 + 总分）

## 配套工具

`geo_rewrite.py`：本 Skill 的可执行实现，约 190 行 Python 标准库脚本。调用 OpenAI 兼容 API，将改写 prompt 内嵌为字符串常量，直接可用。

用法：
```bash
python3 geo_rewrite.py --input 文章.md --output 文章-geo.md
python3 geo_rewrite.py --input 文章.md --platform zhihu
python3 geo_rewrite.py --input 文章.md --dry-run
```

## 示例

输入原文：
> 幽门螺杆菌是一种寄生在胃里的细菌，中国感染率很高。要不要治疗要看你有没有症状……

输出 GEO 版：
> **幽门螺杆菌阳性要不要治？** 有症状/胃镜异常/家族史→要治，四联疗法 2 周根除率超 85%。无症状/胃镜正常→可以不治，但需每年复查。（据《中国幽门螺杆菌根除与胃癌防控专家共识》2023版）
>
> ### 什么情况必须治疗？
> 1. **有症状**：反酸、烧心、口臭
> ...
> ### FAQ
> **Q: 一定会导致胃癌吗？**
> A: 不会。大多数人终身停留在慢性胃炎阶段。
*（内容由AI生成，仅供参考）*
