"""Command-line entry point for nova-galaxy."""

import functools
from typing import Any, Callable, TypeVar

import click

from nova.galaxy.cli.report import Report

URL_ENV = "GALAXY_URL"
KEY_ENV = "GALAXY_KEY"


Command = TypeVar("Command", bound=Callable[..., Any])


def _required(label: str, flag: str, env_var: str) -> Callable[[click.Context, click.Parameter, Any], str]:
    """Build a callback that rejects a value missing from both the environment and command-line."""

    def callback(ctx: click.Context, param: click.Parameter, value: Any) -> str:
        if not value:
            raise click.UsageError(f"No {label}. Pass {flag} or set {env_var}.")
        return str(value)

    return callback


def galaxy_credentials(command: Command) -> Command:
    """Add ``--galaxy-url`` and ``--galaxy-key`` to a command.

    Both fall back to the environment and are required, so a command using this decorator can
    take them as plain strings.
    """
    command = click.option(
        "--galaxy-key",
        envvar=KEY_ENV,
        callback=_required("Galaxy API key", "--galaxy-key", KEY_ENV),
        help=f"Galaxy API key.  [env: {KEY_ENV}]",
    )(command)
    return click.option(
        "--galaxy-url",
        envvar=URL_ENV,
        callback=_required("Galaxy URL", "--galaxy-url", URL_ENV),
        help=f"URL of the Galaxy instance.  [env: {URL_ENV}]",
    )(command)


def output_option(command: Callable[..., Report]) -> Callable[..., None]:
    """Add the ``-o/--output`` choice and print what the command returns in that format."""

    @functools.wraps(command)
    def print_report(*args: Any, output: str, **kwargs: Any) -> None:
        try:
            report = command(*args, **kwargs)
            failed = False
        except Exception as failure:
            report = Report(title="Galaxy error", payload={"error": str(failure)})
            failed = True

        if output == "json":
            click.echo(report.get_json(), err=failed)
        else:
            click.echo(report.get_text(), err=failed)

        if failed:
            raise SystemExit(1)

    return click.option(
        "-o",
        "--output",
        type=click.Choice(["text", "json"]),
        default="text",
        help="How to print the result.",
    )(print_report)


@click.group()
@click.version_option(package_name="nova-galaxy", prog_name="nova")
def cli() -> None:
    """Work with a Galaxy instance from the command-line."""


def galaxy_command(command: Callable[..., Report]) -> click.Command:
    """Register a command that talks to Galaxy and reports what it found.

    Such a command takes the credentials as plain strings and returns a Report; the flags,
    the output format and the exit code are all handled for it.
    """
    return cli.command()(galaxy_credentials(output_option(command)))


def main() -> Any:
    """Entry point for the ``nova`` console script."""
    import nova.galaxy.cli.commands  # noqa: F401

    return cli()
