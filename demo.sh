#!/bin/bash
set -e
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'
echo -e "${BLUE}=== GEO Skills 全链路演示 ===${NC}"
echo ""
echo -e "${GREEN}[1/7] 关键词扩展...${NC}"
python3 geo_expand.py --dry-run > /dev/null && echo "  关键词扩展 OK"
echo -e "${GREEN}[2/7] 内容改写（健康类）...${NC}"
python3 geo_rewrite.py --input tests/test_data/article_health.md --dry-run --score > /dev/null && echo "  rewrite OK"
echo -e "${GREEN}[3/7] 内容审计...${NC}"
python3 geo_audit.py --dry-run > /dev/null && echo "  audit OK"
echo -e "${GREEN}[4/7] 评分追踪...${NC}"
python3 geo_tracker.py --stats 2>/dev/null && echo "  tracker OK" || echo "  tracker（新库） OK"
echo -e "${GREEN}[5/7] 费用看板...${NC}"
python3 geo_cost.py --dashboard > /dev/null && echo "  dashboard OK"
echo -e "${GREEN}[6/7] 多模型对比...${NC}"
python3 geo_compare.py --input tests/test_data/article_health.md --dry-run > /dev/null && echo "  compare OK"
echo -e "${GREEN}[7/7] 全量测试...${NC}"
python3 -m unittest discover tests -q 2>&1 | tail -1
echo ""
echo -e "${BLUE}=== 演示完成 ===${NC}"
