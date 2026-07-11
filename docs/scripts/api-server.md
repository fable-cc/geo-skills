# api-server

Flask Web API 服务器，为 GEO Skills 提供 HTTP 接口。

## 路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/audit` | 内容审计 |
| POST | `/api/rewrite` | GEO 改写 |
| POST | `/api/expand` | 关键词扩展 |
| POST | `/api/flow` | 全流程管线 |

## 启动

```bash
python3 api_server.py
# 默认端口 8899
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥（必填） |
| `LLM_MODEL` | 模型名称（默认 gpt-4o-mini） |

## 请求格式

所有 POST 路由接受 JSON，返回 `{"success": true, "data": {...}}` 或 `{"success": false, "error": "..."}`。

## 示例

```bash
# 启动
python3 api_server.py

# 健康检查
curl http://localhost:8899/health

# 改写
curl -X POST http://localhost:8899/api/rewrite \
  -H "Content-Type: application/json" \
  -d '{"input": "article.md", "platform": "zhihu"}'
```
