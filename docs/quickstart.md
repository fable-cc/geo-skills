# 快速开始

## 第一步：安装

```bash
# 安装为系统命令（零依赖，纯标准库）
pip install .

# 安装后全局可用:
#   geo-rewrite / geo-audit / geo-expand / geo-flow
```

## 第二步：配置环境变量

```bash
export OPENAI_API_KEY="sk-xxx"
export LLM_MODEL="gpt-4o-mini"  # 可选，默认 gpt-4o-mini
```

支持的模型：`gpt-4o-mini` / `gpt-4o` / `deepseek-v3` / `claude-3.5-sonnet`

## 第三步：第一条命令

### 改写一篇文章

```bash
# 基础改写
python3 geo_rewrite.py --input 我的文章.md --output 我的文章-geo.md

# 指定平台
python3 geo_rewrite.py --input 我的文章.md --platform zhihu --brand "景一"

# 先预览（不调 API）
python3 geo_rewrite.py --input 我的文章.md --dry-run
```

### 审计一篇文章

```bash
python3 geo_content_audit.py --input 我的文章.md
```

### 扩展关键词

```bash
python3 geo_keyword_expander.py --keywords "幽门螺杆菌,治疗" --output keywords.csv
```

### 运行完整管线

```bash
python3 geo_flow.py --mode full --keywords "AI工具,效率提升" --top 10 --dry-run
```

## 下一步

- 查看 [脚本参考](scripts/geo-rewrite.md) 了解所有命令行工具
- 阅读 [方法论](methodology.md) 理解五维规则原理
- 复制 [提示词](prompts/cn.md) 在任意 LLM 中直接使用
