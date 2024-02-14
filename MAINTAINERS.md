# Maintainer's Guide for Slack Message Pipe

This guide is intended for maintainers and contributors to the Slack Message Pipe project. It outlines the development workflow, emphasizing the use of `make` to simplify common tasks such as setting up the environment, testing, linting, and building the project.

## Getting Started

### Setting Up Your Development Environment

To set up your development environment, ensure you have Python 3.8 or newer and `make` installed on your system. Then, run the following command:

```bash
make setup
```

This command creates a virtual environment, installs necessary dependencies, and prepares your development environment.

### Activating the Virtual Environment

After setting up your environment, activate the virtual environment with:

- On Unix-like systems (Linux/macOS):

  ```bash
  source venv/bin/activate
  ```

- On Windows (using Command Prompt or PowerShell):

  ```bash
  venv\Scripts\activate
  ```

## Development Workflow

### Running Tests

To run all tests across the configured environments, use:

```bash
make test
```

This command leverages `tox` to run the test suite, ensuring compatibility across different Python versions.

### Performing Lint Checks

To run lint checks on the codebase, execute:

```bash
make lint
```

This ensures that your code adheres to the project's coding standards and guidelines.

### Building the Project

When you're ready to build the project, use:

```bash
make build
```

This command packages the project, making it ready for distribution.

### Cleaning the Project Directory

To clean up the project directory, removing build artifacts and caches, run:

```bash
make clean
```

This is useful for ensuring a clean state before a build or test run.

## Additional Commands

For a list of all available `make` commands and their descriptions, run:

```bash
make help
```

## Pushing a Release

To push a new release, follow these steps:

1. Update the version number in `slack_message_pipe/__init__.py`.
2. Commit the changes.
3. Create a new release on GitHub, creating a new version tag with the same version number.

## Contributing

We welcome contributions from the community. Please ensure you run tests and lint checks before submitting a pull request. If you're adding new features or making significant changes, consider updating the documentation accordingly.

## Questions or Issues

If you encounter any problems or have questions about the development workflow, please open an issue on the project's GitHub page. We aim to provide support and address issues promptly.
