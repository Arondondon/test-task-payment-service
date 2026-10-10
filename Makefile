lint:
	-@ruff check --fix .
	-@ruff format .
	-@mypy .
.PHONY: lint

check-docker:
	@echo Checking Docker status...
ifeq ($(OS),Windows_NT)
	@docker info > NUL 2>&1 || (echo ERROR: Docker daemon is not running. Please start Docker and try again. && exit 1)
else
	@docker info > /dev/null 2>&1 || (echo ERROR: Docker daemon is not running. Please start Docker and try again. && exit 1)
endif
	@echo Docker is running.
.PHONY: check-docker

test: check-docker
ifeq ($(OS),Windows_NT)
	@powershell -Command "\
		$$parentDir = (Split-Path -Parent (Get-Location)); \
		$$env:PYTHONPATH = \"$$parentDir\"; \
		echo \"PYTHONPATH has been installed: $$env:PYTHONPATH\"; \
		python -m coverage run -m pytest tests/ -v; \
		python -m coverage report; \
	"
else
	@PARENT_DIR="$$(dirname "$$(pwd)")"; \
	export PYTHONPATH="$$PARENT_DIR"; \
	echo "PYTHONPATH has been installed: $$PYTHONPATH"; \
	python -m coverage run -m pytest tests/ -v; \
	python -m coverage report
endif
.PHONY: test
