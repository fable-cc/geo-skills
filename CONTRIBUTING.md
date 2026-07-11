---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: e9c4b8701811f7712ebc7921f987742f_2c8e59397d0711f18d11525400e6dd8f
    ReservedCode1: aLaD6jMyARs3yn5WhWN3ERe5qsdu/EYd0yglSp8JbfQTXZNEWlm3qVgj+QnNdrnHNHyQ+yTvyh8tuTA2XRF6d6ch8YFmTTYxCpOrqt4tKGjYwimNihs5yDiLLIwpXR1pnuFsRGEgn/8P1EdRXtBdZSUct4/p5KUYZ2h9izwgiacrx14rw5sC7U7mXDM=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: e9c4b8701811f7712ebc7921f987742f_2c8e59397d0711f18d11525400e6dd8f
    ReservedCode2: aLaD6jMyARs3yn5WhWN3ERe5qsdu/EYd0yglSp8JbfQTXZNEWlm3qVgj+QnNdrnHNHyQ+yTvyh8tuTA2XRF6d6ch8YFmTTYxCpOrqt4tKGjYwimNihs5yDiLLIwpXR1pnuFsRGEgn/8P1EdRXtBdZSUct4/p5KUYZ2h9izwgiacrx14rw5sC7U7mXDM=
---

# 贡献指南

感谢你对 GEO Skills 的关注！本文档将指导你如何参与贡献。

## 行为准则

本项目遵循 [Contributor Covenant](https://www.contributor-covenant.org/) 行为准则。参与即表示你同意遵守其条款。

## 如何贡献

### 报告 Bug

如果你发现了 Bug，请在 GitHub Issues 中提交，并包含以下信息：

1. **标题**：简要描述问题
2. **环境信息**：Python 版本、操作系统、依赖版本
3. **复现步骤**：详细描述触发该 Bug 的操作步骤
4. **预期行为**：你期望发生什么
5. **实际行为**：实际发生了什么
6. **截图/日志**：如有，附上相关终端输出或截图

### 提 Feature 请求

如果你有新的功能想法，请先在 Issues 中发起讨论，说明：

1. **使用场景**：这个功能解决什么实际问题
2. **建议方案**：你期望的 API 或交互方式
3. **替代方案**：考虑过的其他实现方式

### 提交 Pull Request

1. **Fork 本仓库**并克隆到本地
2. **创建功能分支**：`git checkout -b feature/your-feature-name`
3. **编写代码**并确保通过本地测试
4. **提交更改**：使用清晰的 commit message
   ```
   feat: 添加批量处理支持
   fix: 修复 API 超时未重试的问题
   docs: 更新 README 中的使用示例
   ```
5. **推送分支**并创建 Pull Request
6. **等待 Review**：维护者会在 3 个工作日内回复

## 代码风格

### Python 代码

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 规范
- 使用 4 空格缩进，禁止 Tab
- 函数和类必须有 docstring
- 类型注解推荐但不强制
- 优先使用 Python 标准库，减少外部依赖

### Markdown 文档

- 标题层级合理（H1 → H2 → H3，不跳级）
- 代码块标注语言类型
- 中文和英文/数字之间加空格
- 文件末尾保留一个空行

### 提交前检查

```bash
# 语法检查
python3 -m py_compile geo_rewrite.py

# Dry-run 验证 prompt 构建
python3 geo_rewrite.py --input geo-annotated-demo.md --dry-run
```

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/geo-skills.git
cd geo-skills

# 本项目零外部依赖，纯 Python 标准库即可运行
# 如需开发调试，建议安装以下辅助工具（可选）：
pip install ruff mypy  # 代码质量检查
```

## 目录结构

```
geo-skills/
├── geo_rewrite.py              # 核心改写脚本
├── geo-rewrite-prompt.md       # 改写提示词模板
├── geo-rewrite-skill.md        # Hermes Skill 定义
├── geo-annotated-demo.md       # GEO 特征标注演示
├── skills/
│   ├── geo-rewrite/            # GEO 改写 Skill
│   ├── geo-content-audit/      # 内容审计 Skill
│   └── geo-keyword-expander/   # 关键词扩展 Skill
├── .github/workflows/          # CI 配置
├── README.md
├── CONTRIBUTING.md
├── LICENSE
└── .gitignore
```

## 发布流程

维护者使用以下流程发布新版本：

1. 更新 `geo-rewrite-skill.md` 中的 `version` 字段
2. 更新 `skills/*/SKILL.md` 中的 `version` 字段
3. 在 CHANGELOG（如有）中记录变更
4. 创建 Git tag：`git tag v1.x.x && git push --tags`

## 许可证

贡献的代码默认采用 MIT 许可证，与本项目保持一致。
*（内容由AI生成，仅供参考）*
