# geo-audit

内容 GEO 审计脚本，逐段标注 GEO 特征，输出六维评分卡和优先级改进清单。

## 用法

```bash
python3 geo_content_audit.py --input <文章.md> [OPTIONS]
```

或：

```bash
geo-audit --input 文章.md
```

## 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--input` | PATH | *必填* | 输入文章路径 |
| `--output` | PATH | 自动 | 输出路径 |
| `--platform` | STR | 通用 | 目标平台 |
| `--dry-run` | FLAG | — | 只打印不调用 API |
| `--retry` | INT | — | 失败重试次数 |
| `--stream` | FLAG | — | 流式输出 |

## 输出内容

- 逐段 GEO 特征标注（✅ 做得好 / ⚠️ 可改进 / 💡 建议）
- 六维评分卡（问答可见性 / 实体密度 / 引用锚点 / 结构化标记 / 平台适配 / 可读性）
- 优先级改进清单（按收益排序）

## 示例

```bash
geo-audit --input article.md
geo-audit --input article.md --platform zhihu
geo-audit --input article.md --platform wechat --stream
```
