# geo-watch

文件监控自动处理，监控目录中的 `.md` / `.txt` 文件，发现新文件自动调 `geo_rewrite.py` 改写后归档。

纯 Python 标准库轮询实现，不依赖 watchdog。

## 用法

```bash
python3 geo_watch.py --dir <监控目录> --output-dir <输出目录> [OPTIONS]
```

## 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--dir` | PATH | `./input/` | 监控目录 |
| `--output-dir` | PATH | `./output/` | 输出目录 |
| `--platform` | STR | — | 目标平台 |
| `--brand` | STR | — | 品牌实体 |
| `--daemon` | FLAG | — | 后台运行（仅 Unix） |
| `--interval` | INT | 5 | 轮询间隔秒数 |
| `--once` | FLAG | — | 仅处理一次后退出 |
| `--dry-run` | FLAG | — | 只打印命令不执行 |

## 工作流

1. 轮询 `--dir` 目录
2. 发现新的 `.md` / `.txt` 文件
3. 调用 `geo_rewrite.py` 改写
4. 原文件移至 `../processed/` 归档

## 示例

```bash
# 单次处理
geo_watch.py --dir ./input --output-dir ./output --once

# 持续监控
geo_watch.py --dir ./articles --platform zhihu --brand "景一"

# 后台运行
geo_watch.py --dir ./input --daemon --interval 10
```
