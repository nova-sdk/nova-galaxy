# nova-galaxy
=======================

# Introduction

This is the repository for the nova-galaxy project. This project creates a python package that makes it easier to work with the ORNL Galaxy instance.

## Documentation

A user guide, examples, and a full API for this package can be found at https://nova-galaxy.readthedocs.io/en/stable/.

## Installation
You can install this package directly with

```commandline
pip install nova-galaxy
```

or with Poetry by placing the following in your pyproject.toml file (you can version lock with typical Semantic Versioning syntax)


```
[tool.poetry.dependencies]
nova-galaxy = "*"
```

## Formatting
```commandline
poetry run ruff format
```

## Linting
```commandline
poetry run ruff check
poetry run mypy .
```

## Testing
You can run the tests for this package with the following command from the base directory:
```commandline
NOVA_GALAXY_TEST_GALAXY_URL=galaxy-url NOVA_GALAXY_TEST_GALAXY_KEY=key poetry run pytest tests/
```
with `NOVA_GALAXY_TEST_GALAXY_URL` being the url of your Galaxy instance and `NOVA_GALAXY_TEST_GALAXY_KEY` being your
Galaxy API Key.

To run tests with coverage (include the above environment variables):
```commandline
poetry run coverage run
poetry run coverage report
```

## CI/CD in GitHub

Take a look at the [`.github/workflows`](.github/workflows) folder.
Actions to lint and test your code will run automatically on each commit.
The action for building and releasing this package needs to be triggered manually.

### Publishing docs to readthedocs.io

This repo has a [webhook](https://github.com/nova-model/nova-galaxy/settings/hooks) that automatically triggers documentation builds on readthedocs.
