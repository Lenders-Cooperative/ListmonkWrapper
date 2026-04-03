ifneq (,$(wildcard .env))
    include .env
    export
endif

.PHONY: help listmonk-up listmonk-down test lint fmt setup pre-commit-install pre-commit-run complexity

help:
	@echo "Available targets:"
	@echo ""
	@echo "  make setup              Make helper scripts executable and install pre-commit hooks"
	@echo "  make listmonk-up        Start local ListMonk + Postgres via docker-compose"
	@echo "  make listmonk-down      Stop the local ListMonk + Postgres stack"
	@echo "  make test               Run pytest (auto-start Listmonk if needed)"
	@echo "                         Options: CAPTURE=no (default) to show output, DIR=tests/ (default)"
	@echo "                         Example: make test CAPTURE=yes DIR=tests/test_listmonk_methods.py"
	@echo "  make lint               Run pylint on the listmonk_wrapper package"
	@echo "  make fmt                Run black and isort on src/ and tests/"
	@echo "  make complexity         Run xenon to check code complexity (per-file scores)"
	@echo "  make pre-commit-install Install pre-commit hooks"
	@echo "  make pre-commit-run     Run pre-commit hooks on all files"
	@echo ""
	@echo "Environment variables:"
	@echo "  LISTMONK_HOST           Override ListMonk host (default: http://localhost)"
	@echo "  LISTMONK_PORT           Override ListMonk port (default: 9000)"

setup:
	chmod +x bin/start-listmonk
	chmod +x bin/stop-listmonk
	@echo "Scripts are now executable: bin/start-listmonk, bin/stop-listmonk"
	@if command -v pre-commit > /dev/null; then \
		pre-commit install; \
		echo "Pre-commit hooks installed"; \
	else \
		echo "Warning: pre-commit not found. Install with: pip install pre-commit"; \
	fi

pre-commit-install:
	@if command -v pre-commit > /dev/null; then \
		pre-commit install; \
		echo "Pre-commit hooks installed"; \
	else \
		echo "Error: pre-commit not found. Install with: pip install pre-commit"; \
		exit 1; \
	fi

pre-commit-run:
	@if command -v pre-commit > /dev/null; then \
		pre-commit run --all-files; \
	else \
		echo "Error: pre-commit not found. Install with: pip install pre-commit"; \
		exit 1; \
	fi

listmonk-up:
	# Calls the script that handles health checks, install/upgrade, and API wait
	./bin/start-listmonk

listmonk-down:
	# Calls the script that handles graceful teardown
	./bin/stop-listmonk

# Default values for test arguments
CAPTURE ?= no
DIR ?= tests/
COUNT ?= 1

test:
	@echo "--- Ensuring environment is up and healthy before running tests ---"
	# Call listmonk-up to run the startup script, which waits for readiness
	$(MAKE) listmonk-up

	@echo "--- Environment ready. Running tests ---"
	@if [ "$(CAPTURE)" = "no" ]; then \
		pytest -q -s $(DIR) --count=$(COUNT); \
	else \
		pytest -q $(DIR) --count=$(COUNT); \
	fi

	@echo "--- Tests finished. Tearing down environment ---"
	# Call listmonk-down to clean up the containers
	$(MAKE) listmonk-down

lint:
	pylint src/listmonk_wrapper

fmt:
	black -l 100 src tests
	isort --profile black --line-length 100 src tests

complexity:
	@echo "=== Per-File Maintainability Index (radon mi) ==="
	@echo ""
	@if command -v radon > /dev/null 2>&1 || python -m radon --version > /dev/null 2>&1; then \
		python -m radon mi src/listmonk_wrapper --show; \
		echo ""; \
		echo "=== Per-File Complexity Breakdown (radon cc) ==="; \
		echo ""; \
		python -m radon cc src/listmonk_wrapper --show-complexity; \
		echo ""; \
		echo "=== Xenon Summary ==="; \
		echo ""; \
		if command -v xenon > /dev/null 2>&1 || python -m xenon --version > /dev/null 2>&1; then \
			python -m xenon --max-average=C --max-modules=C --max-absolute=C src/listmonk_wrapper 2>&1 | grep -E "(Found|Average|ERROR)" || true; \
		fi; \
		echo ""; \
		echo "Note: Ratings: A=best, B=good, C=moderate, D=high, E=very high, F=extreme"; \
	else \
		echo "Error: radon not found. Install it in the active environment (e.g.: pip install radon xenon)"; \
		exit 1; \
	fi
