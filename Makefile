.PHONY: install run test fmt

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
