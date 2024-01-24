appname = slack-message-pipe
package = slack_message_pipe

help:
	@echo "Makefile for $(appname)"

coverage:
	coverage run -m unittest discover && coverage html && coverage report

test:
	coverage run -m unittest discover -s tests -v
	coverage report

pylint:
	pylint $(package)

check_complexity:
	flake8 $(package) --max-complexity=10

flake8:
	flake8 $(package) --count

deploy:
	rm -f dist/*
	python setup.py sdist
	twine upload dist/*

clean:
	rm -rf dist/ # distribution packages directory
	rm -rf build/ # build artifacts directory
	rm -rf slack-message-pipe.egg-info/ # package metadata directory
	rm -rf .pytest_cache/ # pytest cache directory
	rm -rf .tox/ # Tox virtual environments and logs directory
	rm -rf htmlcov/ # HTML coverage reports directory
	find . -type f -name '*.pyc' -delete # compiled Python files
	find . -type d -name '__pycache__' -delete # Python cache directories