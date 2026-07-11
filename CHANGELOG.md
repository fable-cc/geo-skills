---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: e9c4b8701811f7712ebc7921f987742f_e4ddb8467d0911f1baf4525400bff409
    ReservedCode1: I+Vr7wQdYPC8WGAHhYrTKCcTcTtY/A//Inr+7PPLxBrqhYkmE8A5UB0YBzgWlUBukwVm6O7wVZ0TTDChOPsLANlG6RDWr4dRw0p90KRRKKoZJvfzNjL7UyF6izvUA/BOLgO6wHaxs7g5MjpLljq0i1TVOuP5F2LYU1fuof4P3IY3+Wg/YYZWLPOD+08=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: e9c4b8701811f7712ebc7921f987742f_e4ddb8467d0911f1baf4525400bff409
    ReservedCode2: I+Vr7wQdYPC8WGAHhYrTKCcTcTtY/A//Inr+7PPLxBrqhYkmE8A5UB0YBzgWlUBukwVm6O7wVZ0TTDChOPsLANlG6RDWr4dRw0p90KRRKKoZJvfzNjL7UyF6izvUA/BOLgO6wHaxs7g5MjpLljq0i1TVOuP5F2LYU1fuof4P3IY3+Wg/YYZWLPOD+08=
---

# Changelog

All notable changes to GEO Skills will be documented in this file.

---

## [1.0.0] — 2026-07-11

### Added — Initial Release

- `geo-rewrite-prompt.md`: GEO rewrite prompt template (copy-paste ready)
- `geo-rewrite-skill.md`: Hermes Agent Skill definition for GEO rewriting
- `geo_rewrite.py`: Executable CLI script for GEO article rewriting (single file, per-platform)
- `geo-annotated-demo.md`: Annotated demonstration with 17 GEO feature annotations
- `skills/geo-rewrite/`: GEO rewrite Skill subpackage with SKILL.md
- `skills/geo-content-audit/`: Content GEO audit Skill subpackage with SKILL.md
- `skills/geo-keyword-expander/`: Keyword expansion Skill subpackage with SKILL.md
- `README.md`: Project overview, quick start, file descriptions, and effect verification
- `LICENSE`: MIT License

### v2.0.0 Upgrade (same date)

- **Batch processing**: `--input-dir` and multi-file `--input` support in `geo_rewrite.py`
- **Retry mechanism**: `--retry N` for automatic API retry on failure
- **Streaming output**: `--stream` flag for real-time token streaming
- **Statistics**: `--stats` flag for before/after comparison (character counts)
- **Content audit script**: `geo_content_audit.py` — paragraph-level GEO feature annotation, six-dimension scoring card, priority improvement checklist
- **Keyword expander script**: `geo_keyword_expander.py` — long-tail question generation from seed keywords, CSV output with search volume / AI citation potential / competition scoring
- **Multi-industry rewrite examples**: 4 platform examples (Zhihu/Tech, WeChat/Career, Baijiahao/Lifestyle, Xiaohongshu/Beauty) + 3 industry scenario examples (E-commerce, B2B SaaS, Academic) added to prompt documentation
- **Semantic deep annotation**: Prescription-level source recommendations for each ⚠️ and 💡 annotation
- **English prompt**: `geo-rewrite-prompt-en.md` — full English version of GEO rewrite prompt for ChatGPT Search / Perplexity / Gemini
- **Project infrastructure**:
  - `pyproject.toml`: Standard Python project metadata with console_scripts entry points (`geo-rewrite`, `geo-audit`, `geo-expand`)
  - `.github/workflows/test.yml`: GitHub Actions CI (syntax check + dry-run validation)
  - `CONTRIBUTING.md`: Contribution guide
  - `.gitignore`: Python project ignore rules
  - README Badges: MIT License / Python 3.10+ / CI status
*（内容由AI生成，仅供参考）*
