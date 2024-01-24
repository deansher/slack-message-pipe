## Setting Up Development Environment

To set up a development environment for `slack-message-pipe`, you should create a virtual environment and install the package in editable mode along with its development dependencies.

### Creating a Virtual Environment

A virtual environment is an isolated Python environment that allows you to manage dependencies for different projects. To create a virtual environment, run:

```sh
python -m venv venv
```

This command creates a new directory called `venv` where the virtual environment files are stored. To activate the virtual environment, use the following command:

On Unix or MacOS:
```sh
source venv/bin/activate
```

On Windows:
```sh
venv\Scripts\activate
```

### Installing the Package in Editable Mode

To install `slack-message-pipe` in editable mode, which allows you to make changes to the code and see them reflected immediately, run:

```sh
pip install -e .
```

This command installs the package in such a way that changes to the source files will immediately affect the installed package without needing to reinstall.

### Installing Development Dependencies

To install the additional dependencies required for testing and other development tasks, run:

```sh
pip install '.[dev,test]'
```

This command installs the dependencies specified under the `optional-dependencies` section in `pyproject.toml` for the `dev` extra.

### Updating pip and Build Tools

Ensure you have the latest versions of `pip` and build tools to handle the `pyproject.toml` configuration:

```sh
pip install --upgrade pip build
```

## Development Workflow

When developing new features or fixing bugs, it's important to frequently run tests and check code quality. Use the following commands to ensure your changes meet the project standards:

- **Running Tests**: `make test` or `tox`
- **Running a Specific Test**: `tox -e py310 -- tests/test_module.py`
- **Checking Code Quality**: `make pylint` or `tox -e flake8`

After making changes, you can build the package locally to test the installation process:

```sh
python -m build
```

This command generates distribution files in the `dist/` directory that you can install using `pip`.

Remember to deactivate your virtual environment when you're done working on the project:

```sh
deactivate
```

Thank you for maintaining `slack-message-pipe`. Your contributions help improve the tool for everyone!
