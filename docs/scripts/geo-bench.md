# geo-bench

性能压测脚本，生成 mock 文章并模拟/真实运行管线，测量吞吐量、内存和阶段耗时。

## 用法

```bash
python3 geo_bench.py --count <N> --mode <模式>
```

## 模式

| 模式 | 说明 |
|------|------|
| `mock` | 只生成 N 篇 mock 文章，验证生成逻辑 |
| `dry` | 模拟四阶段调度耗时（不调 API），输出 ASCII 柱状图 + 规模预估 |
| `real` | 真实运行 `geo_flow.py`（需 API Key），默认最多执行 5 篇 |

## 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--count` | INT | 100 | 测试文章数量 |
| `--mode` | STR | dry | mock/dry/real |
| `--real-limit` | INT | 5 | real 模式最多执行篇数 |

## 输出

- 吞吐量（篇/秒）
- 内存峰值（MB）
- 总耗时
- ASCII 柱状图展示各阶段耗时分布
- 规模预估（×100/×500/×1000/×5000）

## 示例

```bash
# 生成 mock
geo_bench.py --count 50 --mode mock

# 模拟压测
geo_bench.py --count 200 --mode dry

# 真实压测
geo_bench.py --count 100 --mode real --real-limit 10
```
