.PHONY: lint type test check
lint:
	ruff check .
type:
	mypy
test:
	pytest -q
check: lint type test
