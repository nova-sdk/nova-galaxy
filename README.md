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

or with [Pixi](https://pixi.sh/latest/):


```commandline
pixi add --pypi nova-galaxy
```

## Command line

This package installs a `nova` command.

```commandline
export GALAXY_URL=https://your-galaxy.instance
export GALAXY_KEY=your-api-key

nova connect
# If you prefer the CLI over environment variables for providing credentials, then below is equivalent.
# nova connect --galaxy-url https://your-galaxy.instance --galaxy-key "your-api-key"
```

```
Connected to Galaxy
  requested_url: https://your-galaxy.instance
  resolved_url: https://your-galaxy.instance
  version:
    version_major: 26.1
    version_minor: rc1
  user:
    ...
```

Add `-o json` for machine-readable output.

## Formatting
```commandline
pixi run ruff format
```

## Linting
```commandline
pixi run ruff check
pixi run mypy .
```

## Testing
You can run the tests for this package with the following command from the base directory:
```commandline
NOVA_GALAXY_TEST_GALAXY_URL=galaxy-url NOVA_GALAXY_TEST_GALAXY_KEY=key pixi run pytest tests/
```
with `NOVA_GALAXY_TEST_GALAXY_URL` being the url of your Galaxy instance and `NOVA_GALAXY_TEST_GALAXY_KEY` being your
Galaxy API Key.

To run tests with coverage (include the above environment variables):
```commandline
pixi run coverage run
pixi run coverage report
```

## CI/CD in GitHub

Take a look at the [`.github/workflows`](.github/workflows) folder.
Actions to lint and test your code will run automatically on each commit.
The action for building and releasing this package needs to be triggered manually.

### Publishing docs to readthedocs.io

This repo has a [webhook](https://github.com/nova-model/nova-galaxy/settings/hooks) that automatically triggers documentation builds on readthedocs.
