.PHONY: install run test fmt lint type hooks check

PY=python
PIP=pip
UVICORN=uvicorn

install:
	$(PIP) install -r requirements.txt

run:
	$(PY) -m $(UVICORN) app.main:app --reload

test:
	$(PY) -m pytest -q

fmt:
	$(PY) -m black app tests

lint:
	ruff check .
	$(PY) -m black --check app tests

type:
	$(PY) -m mypy app

hooks:
	pre-commit install

check: lint type test
