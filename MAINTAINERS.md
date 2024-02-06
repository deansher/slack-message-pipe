# Maintainers Guide for `slack-message-pipe`

Thank you for contributing to `slack-message-pipe`! This guide is designed to help maintainers and contributors set up their development environment, follow best practices, and release updates to PyPI.

## Setting Up Development Environment

To contribute to `slack-message-pipe`, you'll need to set up a local development environment. This involves creating a virtual environment, installing the package in editable mode, and installing development dependencies.

### Creating a Virtual Environment

A virtual environment isolates project dependencies. Create one by running:

```sh
python3 -m venv venv
```

Activate the virtual environment with:

- **Unix or MacOS**: `source venv/bin/activate`
- **Windows**: `venv\Scripts\activate`

### Installing the Package in Editable Mode

Installing the package in editable mode (`-e`) allows you to modify the code and see changes without reinstalling the package:

```sh
pip3 install -e '.[dev,test]'
```

This installs all development and test dependencies to ensure you can run tests, linting, and other development tools.


### Updating pip and Build Tools

Ensure your `pip` and build tools are up-to-date to handle the project's `pyproject.toml` configuration:

```sh
pip3 install --upgrade pip build
```

## Development Workflow

To streamline the setup, you can use this combined command to create the environment, activate it, and install all necessary dependencies:

```sh
rm -rf venv && python3 -m venv venv && source venv/bin/activate && pip3 install --upgrade pip && pip3 install -e '.[dev,test]'
```

### Common Development Tasks

- **Running Tests**: Execute `make test` or `tox` to run all tests.
- **Running a Specific Test**: Use `tox -e py310 -- tests/test_module.py` for targeted testing.
- **Checking Code Quality**: Run `make pylint` or `tox -e flake8` for linting and code quality checks.

### Building the Package Locally

Before releasing, build the package locally to test the installation process:

```sh
python3 -m build
```

This generates distribution files in the `dist/` directory, which you can install using `pip`.

### Releasing to PyPI

To release a new version to PyPI, ensure all tests pass and your changes are merged into the main branch. Then, tag your release with a version number and create a GitHub Release. The GitHub Actions workflow defined in `.github/workflows/release.yml` will automatically package and upload the new version to PyPI.

To create a GitHub Release, navigate to the "Releases" section of your GitHub repository, click on "Draft a new release," select the tag you created for your version, fill in the release title and description with the details of your changes, and then click "Publish release" to make it official.

### Deactivating the Virtual Environment

When you're finished, deactivate the virtual environment:

```sh
deactivate
```

## Thank You!

Your contributions are invaluable to the `slack-message-pipe` project. By following these guidelines, you help ensure a robust and reliable tool for everyone.
