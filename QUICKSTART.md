# GEO Skills 快速上手

## 前提
- Python 3.10+
- Git

## 三步走

### 1. 克隆仓库
```bash
git clone https://github.com/fable-cc/geo-skills.git
cd geo-skills
```

### 2. 一键安装
```bash
bash install.sh
```
预期输出：每步 `[OK]`，最后提示 source completions/

### 3. 全链路演示
```bash
bash demo.sh
```
预期输出：7 步全绿，最后显示 `OK (skipped=N)` 测试结果

## 接下来

- `make all` — 完整验证（测试 + 类型检查 + 覆盖率 + 构建）
- `python3 geo_rewrite.py --input your_article.md --score` — 改写你的第一篇文章
- 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 了解系统设计
- 阅读 [文档站](https://fable-cc.github.io/geo-skills) 学习高级用法
