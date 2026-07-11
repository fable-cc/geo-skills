# GEO Skills — Bash 自动补全
# 安装方法:
#   source completions/geo-rewrite.bash
# 持久化:
#   echo "source $(pwd)/completions/geo-rewrite.bash" >> ~/.bashrc

_geo_common_opts="--help"

_geo_platforms="zhihu wechat baijiahao xiaohongshu"

_geo_complete_rewrite() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    opts="--input --output --platform --brand --score --json --stream --retry --stats --dry-run"

    case "${prev}" in
        --input|--output|--input-dir|--output-dir)
            COMPREPLY=( $(compgen -f -- "${cur}") )
            return 0
            ;;
        --platform)
            COMPREPLY=( $(compgen -W "${_geo_platforms}" -- "${cur}") )
            return 0
            ;;
        --brand)
            COMPREPLY=()
            return 0
            ;;
        *)
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
    esac
}

_geo_complete_audit() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    opts="--input --output --platform --dry-run --retry --stream --help"

    case "${prev}" in
        --input|--output)
            COMPREPLY=( $(compgen -f -- "${cur}") )
            return 0
            ;;
        --platform)
            COMPREPLY=( $(compgen -W "${_geo_platforms}" -- "${cur}") )
            return 0
            ;;
        *)
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
    esac
}

_geo_complete_expand() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    opts="--keywords --count --output --dry-run --help"

    case "${prev}" in
        --output)
            COMPREPLY=( $(compgen -f -- "${cur}") )
            return 0
            ;;
        --count)
            COMPREPLY=( $(compgen -W "50 100 200 500" -- "${cur}") )
            return 0
            ;;
        *)
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
    esac
}

_geo_complete_flow() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    opts="--mode --keywords --input --count --top --platform --brand --output-dir --dry-run --help"

    case "${prev}" in
        --mode)
            COMPREPLY=( $(compgen -W "full single matrix" -- "${cur}") )
            return 0
            ;;
        --input|--output-dir)
            COMPREPLY=( $(compgen -f -- "${cur}") )
            return 0
            ;;
        --platform)
            COMPREPLY=( $(compgen -W "${_geo_platforms}" -- "${cur}") )
            return 0
            ;;
        --brand)
            COMPREPLY=()
            return 0
            ;;
        --count|--top)
            COMPREPLY=( $(compgen -W "5 10 20 50 100" -- "${cur}") )
            return 0
            ;;
        *)
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
    esac
}

complete -F _geo_complete_rewrite geo-rewrite
complete -F _geo_complete_rewrite geo_rewrite.py
complete -F _geo_complete_audit geo-audit
complete -F _geo_complete_audit geo_content_audit.py
complete -F _geo_complete_expand geo-expand
complete -F _geo_complete_expand geo_keyword_expander.py
complete -F _geo_complete_flow geo-flow
complete -F _geo_complete_flow geo_flow.py
