# margin-watch: one-day prototype. Sample data only; nothing is sent anywhere.
#   make demo   run both sample days, build the dashboard and serve it on http://localhost:4173
#   make test   the full completion gate (agent + dashboard + test-integrity checks)
#   make clean  remove generated output and build folders

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
PORT ?= 4173
CORE := calc.py,margin_watch/status.py,margin_watch/validate.py

.PHONY: help deps test test-agent test-dashboard demo runs clean

help:
	@echo "make demo   - run 3 Nov (demo-bad) and 4 Nov (demo), build and serve the dashboard on :$(PORT)"
	@echo "make test   - ruff, mypy, pytest + coverage, integrity checks, svelte-check, eslint, vitest, playwright"
	@echo "make clean  - remove output/ contents and dashboard build folders"

deps:
	cd agent && uv sync --quiet
	@if [ ! -d dashboard/node_modules ]; then cd dashboard && npm ci; fi
	@cd dashboard && npx playwright install chromium >/dev/null

test: deps test-agent test-dashboard
	python3 scripts/check_test_integrity.py
	python3 scripts/check_frozen_tests.py
	@echo "All checks passed."

test-agent:
	cd agent && uv run ruff check . && uv run ruff format --check . && uv run mypy --strict margin_watch && uv run pytest -q
	cd agent && uv run coverage report --include="margin_watch/$(CORE)" --fail-under=100

test-dashboard:
	cd dashboard && npm run check && npm run lint && npm run test && npm run test:e2e

# The two sample mornings, as the 6:30 AM scheduled run would produce them.
runs:
	find output -mindepth 1 ! -name .gitkeep -delete
	cd agent && uv run margin-watch run --source ../data/sample/jobs-2026-11-03.json --ai demo-bad --generated-at 2026-11-03T06:30:00+11:00
	cd agent && uv run margin-watch run --source ../data/sample/jobs-2026-11-04.json --ai demo --generated-at 2026-11-04T06:30:00+11:00

demo: deps runs
	cd dashboard && npm run sync-runs && npm run build
	@echo ""
	@echo "  Dashboard:      http://localhost:$(PORT)"
	@echo "  Excel report:   $(CURDIR)/output/margin-report-2026-11-04.xlsx"
	@echo "  Email preview:  $(CURDIR)/output/email/preview-2026-11-04.html"
	@echo "  Graph payload:  $(CURDIR)/output/email/graph-sendmail-2026-11-04.json"
	@echo "  Stop with Ctrl+C."
	@echo ""
	cd dashboard && npx vite preview --port $(PORT) --strictPort

clean:
	find output -mindepth 1 ! -name .gitkeep -delete
	rm -rf dashboard/build dashboard/.svelte-kit dashboard/static/runs dashboard/test-results dashboard/playwright-report
	rm -rf agent/.pytest_cache agent/.mypy_cache agent/.ruff_cache agent/.coverage
