appname = slack-message-pipe
package = slack_message_pipe

.PHONY: help setup test lint build clean

# Note that the make target comments are processed by the help target.

help: ## Display this help screen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $\$1, $\$2}'

dev: ## Set up the development environment
	python3 -m venv venv && \
	. venv/bin/activate && \
	pip install --upgrade pip && \
	pip install tox flit && \
	flit install --symlink

clean-dev: ## Clean up the development environment
	rm -rf venv

test: ## Run tests with tox
	tox

lint: ## Run linting with tox
	tox -e pylint

build: ## Build the package with flit
	flit build

clean: ## Clean up the project directory
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ .tox/ .mypy_cache/ htmlcov/
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
