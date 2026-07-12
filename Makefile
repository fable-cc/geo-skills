.PHONY: install test pipeline clean all coverage build release lint

install:
	pip install .

test:
	cd tests && python3 -c "import ast; [ast.parse(open(f).read()) for f in ['test_real_api.py','benchmark.py']]; print('语法 OK')"
	python3 -m unittest tests/test_core.py -v
	python3 -m unittest tests/test_pipeline.py -v

pipeline:
	python3 geo_flow.py --mode full --keywords "AI工具,效率提升" --top 3 --dry-run

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

all: test lint coverage build

coverage:
	pip install -q coverage
	coverage run -m unittest discover tests -v
	coverage report -m
	coverage html
	@echo "Coverage report: htmlcov/index.html"

build:
	pip install -q build
	python3 -m build
	@echo "Built: dist/"

release:
	@echo "Tagging v$(shell python3 setup.py --version)..."
	git tag -a "v$(shell python3 setup.py --version)" -m "Release v$(shell python3 setup.py --version)"
	git push origin main --tags
	@echo "Released: v$(shell python3 setup.py --version)"

lint:
	pip install -q mypy
	mypy geo_skills/ --config-file mypy.ini
	@echo "mypy OK"
