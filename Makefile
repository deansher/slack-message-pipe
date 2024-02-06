appname = slack-message-pipe
package = slack_message_pipe

help:
	@echo "Makefile for $(appname)"

test:
	tox

clean:
	rm -rf dist/ # distribution packages directory
	rm -rf build/ # build artifacts directory
	rm -rf slack-message-pipe.egg-info/ # package metadata directory
	rm -rf .pytest_cache/ # pytest cache directory
	rm -rf .tox/ # Tox virtual environments and logs directory
	rm -rf .mypy_cache/ # mypy cache directory
	rm -rf htmlcov/ # HTML coverage reports directory
	find . -type f -name '*.pyc' -delete # compiled Python files
	find . -type d -name '__pycache__' -delete # Python cache directories
