# Maintainers' Guide for slack-message-pipe

This document is intended for maintainers of the `slack-message-pipe` project. It provides an overview of the project structure, key maintenance tasks, and common commands used in the development and release process.

## Overview

The `slack-message-pipe` project is a command-line tool for exporting Slack channel messages to a PDF file. The project is structured as follows:

- `slack-message-pipe/`: Main Python package directory.
- `tests/`: Contains all the unit tests for the project.
- `fonts/`: Directory containing fonts used in PDF generation.
- `fpdf_mod/`: Modifications or extensions to the FPDF library.
- `pyproject.toml`: Configuration for build system and project metadata.
- `tox.ini`: Configuration for automated testing with `tox`.
- `.pre-commit-config.yaml`: Configuration for pre-commit hooks.
- `.github/workflows/`: CI/CD workflows for GitHub Actions.

## Key Processes

### Testing

To run the full test suite with coverage, use the following command:

```sh
make test
```

For linting, use:

```sh
make pylint
```

### Building

To build the project, ensure all tests pass and then use:

```sh
python -m build
```

### Releasing

To release a new version, update the `__version__` string in `slack-message-pipe/__init__.py` to the new version number, following semantic versioning rules.

After updating the version, tag the repository and push the tag:

```sh
git tag -a v2.0.0 -m "Release version 2.0.0"
git push origin v2.0.0
```

Create a release on GitHub associated with the pushed tag. This will trigger the GitHub Actions workflow to package and release the new version to PyPI.

### Deploying

To deploy the package to PyPI, use the `deploy` command in the `Makefile`:

```sh
make deploy
```

Ensure you have the necessary permissions and the `TWINE_PASSWORD` is set as a secret in the GitHub repository.

## Sample Commands

Here are some sample commands for common tasks:

- **Running Tests**: `tox`
- **Running a Specific Test**: `tox -e py310 -- tests/test_module.py`
- **Checking Code Quality**: `tox -e flake8`
- **Building the Package**: `python -m build`
- **Uploading to PyPI**: `twine upload dist/*`

Remember to update the `CHANGELOG.md` with the changes for the new version before releasing.

## Additional Notes

- The `Makefile` contains several shortcuts for common tasks.
- The `tox.ini` file is configured to run tests against multiple Python versions.
- Pre-commit hooks are set up to run formatting and linting checks before commits.

Thank you for maintaining `slack-message-pipe`. Your contributions are greatly appreciated!