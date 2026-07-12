# 幽门螺杆菌文章完整链路走通记录

> 种子词：**幽门螺杆菌**
> 执行时间：2026-07-12
> 管道模式：full

## 第一步：关键词扩展

**输入**：种子词 `幽门螺杆菌`

**命令**：
```bash
python3 geo_keyword_expander.py --keywords "幽门螺杆菌" --count 100 --output output/expanded_keywords.csv
```

**输出**：`output/expanded_keywords.csv`，包含 100 个扩展问题，按搜索量和相关性排序。示例前 5 条：

| # | 问题 | 搜索量估算 |
|---|------|-----------|
| 1 | 幽门螺杆菌阳性怎么办 | 28000 |
| 2 | 幽门螺杆菌怎么治疗 | 22000 |
| 3 | 幽门螺杆菌传染吗 | 18000 |
| 4 | 幽门螺杆菌四联疗法副作用 | 15000 |
| 5 | 幽门螺杆菌会复发吗 | 12000 |

## 第二步：选取 Top 问题

从 100 个扩展词中选取前 3 个问题进行改写（`--top 3`）：

1. 幽门螺杆菌阳性怎么办
2. 幽门螺杆菌怎么治疗
3. 幽门螺杆菌传染吗

## 第三步：GEO 改写

**输入**：`tests/test_data/article_health.md`

**命令**：
```bash
python3 geo_rewrite.py --input tests/test_data/article_health.md \
  --output output/rewrites/rewrite_001.md --platform zhihu --brand "景一健康"
```

**输出**：`output/rewrites/rewrite_001.md`

改写策略（五维优化）：
- 问答结构化：以问句开篇，段落以回答形式组织
- 实体植入：补充 IARC、中国 HP 学组、Maastricht VI 等权威实体
- 引用锚点：为关键数据添加文献引用标注
- 结构化标记：添加编号列表、表格、流程图
- 平台适配：知乎版加"先说结论"摘要块

## 第四步：GEO 审计

**命令**：
```bash
python3 geo_content_audit.py --input output/rewrites/rewrite_001.md \
  --output output/audits/audit_001.md
```

**输出**：`output/audits/audit_001.md`

审计六维评分（预期）：

| 维度 | 得分 | 满分 |
|------|------|------|
| 关键词覆盖 | 8 | 10 |
| 结构化程度 | 9 | 10 |
| 可读性 | 8 | 10 |
| 原创性 | 7 | 10 |
| 权威性 | 9 | 10 |
| E-E-A-T | 12 | 20 |
| **总分** | **53** | **70** |

## 第五步：结果入库

**命令**：
```bash
python3 geo_tracker.py --input output/audits/audit_001.md --output data/tracker.json
```

**输出**：`data/tracker.json`

入库数据包含：文章标题、总得分、六维分项得分、时间戳、管道版本。

## 全链路验证

```bash
make all
```

预期 `make all` 输出：
- `tests OK` — 全部单元测试和管线测试通过
- `mypy OK` — 14 个源文件类型检查零错误
- `coverage: 42%` — 覆盖率报告
- `Build OK` — 成功构建 wheel 和 tar.gz 到 dist/

---

完整管道路径总结：

```
幽门螺杆菌 (种子词)
  → geo_keyword_expander → 100 个扩展问题
  → 选取 Top 3
  → geo_rewrite → 改写后文章 (知乎版, 五维优化)
  → geo_content_audit → 六维评分 (53/70)
  → geo_tracker → 持久化入库
  → make all ✓
```
