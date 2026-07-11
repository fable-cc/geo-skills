.PHONY: install test pipeline clean all

install:
	pip install .

test:
	cd tests && python3 -c "import ast; [ast.parse(open(f).read()) for f in ['test_real_api.py','benchmark.py']]; print('语法 OK')"

pipeline:
	python3 geo_flow.py --mode full --keywords "AI工具,效率提升" --top 3 --dry-run

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

all: install test
