# geo-notify

Webhook 通知脚本，支持 Slack、钉钉、企业微信三种通道，可自动解析改写/审计文件并嵌入评分信息。

## 用法

```bash
python3 geo_notify.py --webhook-url <URL> [OPTIONS]
```

## 平台自动检测

URL 包含 `hooks.slack.com` → Slack  
URL 包含 `oapi.dingtalk.com` → 钉钉  
URL 包含 `qyapi.weixin.qq.com` → 企业微信

## 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--webhook-url` | STR | *必填* | Webhook URL |
| `--platform` | STR | 自动检测 | slack/dingtalk/wecom |
| `--message` | STR | "GEO 改写完成" | 自定义通知消息 |
| `--file` | PATH | — | 附加文件摘要（读取评分和摘要） |
| `--test` | FLAG | — | 发送测试通知 |

## 通知格式

**Slack**: Block Kit（header + fields + summary + divider）  
**钉钉**: Markdown（标题 + 文件/平台/评分 + 摘要）  
**企业微信**: Markdown（带颜色标注的评分信息）

## 示例

```bash
# 测试通知
geo_notify.py --test --platform slack --webhook-url https://hooks.slack.com/...

# 带文件摘要的通知
geo_notify.py --file output-audit.md --webhook-url https://oapi.dingtalk.com/...

# 自定义消息
geo_notify.py --message "10篇文章全部改写完成" --webhook-url https://qyapi.weixin.qq.com/...
```
