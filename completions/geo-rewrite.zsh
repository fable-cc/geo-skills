#compdef geo-rewrite geo_rewrite.py geo-audit geo_content_audit.py geo-expand geo_keyword_expander.py geo-flow geo_flow.py
# GEO Skills — Zsh 自动补全
# 安装方法:
#   fpath=($(pwd)/completions $fpath) && compinit
# 持久化:
#   echo 'fpath=('$(pwd)'/completions $fpath)' >> ~/.zshrc && echo 'compinit' >> ~/.zshrc

local -a _geo_platforms
_geo_platforms=(zhihu wechat baijiahao xiaohongshu)

# ---- geo-rewrite / geo_rewrite.py ----
_geo_rewrite() {
    _arguments \
        '--input[输入文章路径]:文件:_files' \
        '--output[输出文件路径]:文件:_files' \
        '--platform[目标平台]:平台:(zhihu wechat baijiahao xiaohongshu)' \
        '--brand[品牌实体名称]:品牌:' \
        '--score[输出评分卡]' \
        '--json[输出 JSON 格式]' \
        '--stream[流式输出]' \
        '--retry[失败重试次数]:次数:(1 2 3 5)' \
        '--stats[输出统计信息]' \
        '--dry-run[只打印 prompt 不调用 API]' \
        '--help[显示帮助]'
}

# ---- geo-audit / geo_content_audit.py ----
_geo_audit() {
    _arguments \
        '--input[输入文章路径]:文件:_files' \
        '--output[输出文件路径]:文件:_files' \
        '--platform[目标平台]:平台:(zhihu wechat baijiahao xiaohongshu)' \
        '--dry-run[只打印 prompt 不调用 API]' \
        '--retry[失败重试次数]:次数:(1 2 3 5)' \
        '--stream[流式输出]' \
        '--help[显示帮助]'
}

# ---- geo-expand / geo_keyword_expander.py ----
_geo_expand() {
    _arguments \
        '--keywords[种子关键词（逗号分隔）]:关键词:' \
        '--count[生成数量]:数量:(50 100 200 500)' \
        '--output[输出 CSV 路径]:文件:_files' \
        '--dry-run[只打印 prompt 不调用 API]' \
        '--help[显示帮助]'
}

# ---- geo-flow / geo_flow.py ----
_geo_flow() {
    _arguments \
        '--mode[管线模式]:模式:(full single matrix)' \
        '--keywords[种子关键词（逗号分隔）]:关键词:' \
        '--input[单篇文章路径（single模式）]:文件:_files' \
        '--count[expand 生成数量]:数量:(50 100 200 500)' \
        '--top[选取前 N 个改写]:数量:(3 5 10 20 50)' \
        '--platform[目标平台]:平台:(zhihu wechat baijiahao xiaohongshu)' \
        '--brand[品牌实体名称]:品牌:' \
        '--output-dir[输出目录]:目录:_files -/' \
        '--dry-run[只打印执行计划]' \
        '--help[显示帮助]'
}

# Bind functions to commands
compdef _geo_rewrite geo-rewrite
compdef _geo_rewrite geo_rewrite.py
compdef _geo_audit geo-audit
compdef _geo_audit geo_content_audit.py
compdef _geo_expand geo-expand
compdef _geo_expand geo_keyword_expander.py
compdef _geo_flow geo-flow
compdef _geo_flow geo_flow.py
