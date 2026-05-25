# Common tasks via uv (use GNU Make — e.g. Git for Windows ships `mingw32-make`, or https://gnuwin32.sourceforge.net/).
# Lint and test require dev dependency groups (`make dev`).

UV ?= uv

.PHONY: help sync sync-dev setup dev bootstrap test lint lint-fix fmt lock

help:
	@echo Targets:
	@echo   make sync - uv sync, runtime deps only
	@echo   make sync-dev - uv sync --dev
	@echo   make setup - sync then install.py NLTK and UniDic
	@echo   make dev - sync-dev then install.py
	@echo   make bootstrap - install.py only
	@echo   make test - pytest, run sync-dev or dev first
	@echo   make lint - ruff and black checks
	@echo   make lint-fix - ruff --fix and ruff format
	@echo   make fmt - black and ruff format in place
	@echo   make lock - uv lock

sync:
	$(UV) sync

sync-dev:
	$(UV) sync --dev

setup: sync bootstrap

dev: sync-dev bootstrap

bootstrap:
	$(UV) run python install.py

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(UV) run black --check .

lint-fix:
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

fmt:
	$(UV) run ruff format .
	$(UV) run black .

lock:
	$(UV) lock
