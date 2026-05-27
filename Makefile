# Common tasks via uv (use GNU Make — e.g. Git for Windows ships `mingw32-make`, or https://gnuwin32.sourceforge.net/).
# Lint and test require dev dependency groups (`make dev`).

UV ?= uv

.PHONY: help sync sync-dev setup dev bootstrap bootstrap-force test lint lint-fix fmt lock

help:
	@echo Targets:
	@echo   make sync - uv sync, runtime deps only
	@echo   make sync-dev - uv sync --dev
	@echo   make setup - uv sync then install NLTK UniDic KoboldCPP and RVC base models
	@echo   make dev - sync-dev then full bootstrap scripts
	@echo   make bootstrap - install.py plus KoboldCPP and RVC HF assets
	@echo   make test - pytest, run sync-dev or dev first
	@echo   make lint - ruff and black checks
	@echo   make lint-fix - ruff --fix and ruff format
	@echo   make fmt - black and ruff format in place
	@echo   make bootstrap-force - force re-download of KoboldCPP and RVC HF assets
	@echo   make lock - uv lock

sync:
	$(UV) sync

sync-dev:
	$(UV) sync --dev

setup: sync bootstrap

dev: sync-dev bootstrap

bootstrap:
	$(UV) run python scripts/install.py
	$(UV) run python scripts/bootstrap_runtime_deps.py

bootstrap-force:
	$(UV) run python scripts/install.py
	$(UV) run python scripts/bootstrap_runtime_deps.py --force

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
