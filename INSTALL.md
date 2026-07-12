# GEO Skills 安装指南

三种安装方式，按需选择一种。

---

## 方式一：pip 从 PyPI 安装（推荐）

```bash
pip install geo-skills
```

安装后 CLI 入口点自动就绪：

```bash
geo-rewrite --help
geo-audit --help
geo-expand --help
```

---

## 方式二：pip 开发模式安装（本地开发）

```bash
cd geo-skills
pip install -e .
```

源码修改即时生效，无需重复安装。适合二次开发或定制 prompt。

---

## 方式三：git clone + pip 安装

```bash
git clone https://github.com/fable-cc/geo-skills.git
cd geo-skills
pip install -e .
```

> 如果需要补全脚本（bash/zsh），安装后将 `completions/` 下的脚本 source 到 `.bashrc` / `.zshrc` 中。

---

## 安装后验证

```bash
geo-rewrite --version
```

预期输出：

```
geo-skills v1.1.0
```

---

## 可选：一键安装脚本

```bash
chmod +x install.sh
./install.sh
```

脚本自动完成环境检测、pip 安装和 shell 补全配置。
