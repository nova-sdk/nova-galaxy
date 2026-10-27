"""Tests for the command-line interface.

These tests were generated automatically by Claude Opus 5.
"""

import json
import subprocess
import sys
from typing import Callable
from unittest.mock import MagicMock

import click
import pytest
from click.testing import CliRunner

from nova.galaxy.cli import cli as cli_module
from nova.galaxy.cli import commands, main
from nova.galaxy.cli.cli import KEY_ENV, URL_ENV, cli, galaxy_command, output_option
from nova.galaxy.cli.report import Report

GALAXY_URL = "https://galaxy.example"
GALAXY_KEY = "test-api-key"


@pytest.fixture(autouse=True)
def no_credentials_in_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the developer's own credentials out of every test in this module."""
    monkeypatch.delenv(URL_ENV, raising=False)
    monkeypatch.delenv(KEY_ENV, raising=False)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def connection() -> MagicMock:
    """A stand-in for the helper yielded by ``Connection(...).connect()``."""
    helper = MagicMock()
    helper.galaxy_url = "https://resolved.example"
    helper.get_version.return_value = {"version_major": "24.1"}
    helper.get_current_user.return_value = {"username": "tester"}
    return helper


@pytest.fixture
def galaxy(monkeypatch: pytest.MonkeyPatch, connection: MagicMock) -> MagicMock:
    """Replace the Connection used by the commands, so no test reaches a real Galaxy."""
    factory = MagicMock()
    factory.return_value.connect.return_value.__enter__.return_value = connection
    monkeypatch.setattr(commands, "Connection", factory)
    return factory


def command_returning(report: Callable[[], Report]) -> click.Command:
    """Build a bare command wrapped in :func:`output_option`, without the credential flags."""

    @click.command()
    @output_option
    def built() -> Report:
        """Do something and report it."""
        return report()

    return built


def test_connect_passes_the_credentials_given_on_the_command_line(runner: CliRunner, galaxy: MagicMock) -> None:
    result = runner.invoke(cli, ["connect", "--galaxy-url", GALAXY_URL, "--galaxy-key", GALAXY_KEY])

    assert result.exit_code == 0
    galaxy.assert_called_once_with(GALAXY_URL, GALAXY_KEY)


def test_connect_falls_back_to_the_environment(
    runner: CliRunner, galaxy: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(URL_ENV, GALAXY_URL)
    monkeypatch.setenv(KEY_ENV, GALAXY_KEY)

    result = runner.invoke(cli, ["connect"])

    assert result.exit_code == 0
    galaxy.assert_called_once_with(GALAXY_URL, GALAXY_KEY)


def test_command_line_credentials_win_over_the_environment(
    runner: CliRunner, galaxy: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(URL_ENV, "https://ignored.example")
    monkeypatch.setenv(KEY_ENV, "ignored-key")

    result = runner.invoke(cli, ["connect", "--galaxy-url", GALAXY_URL, "--galaxy-key", GALAXY_KEY])

    assert result.exit_code == 0
    galaxy.assert_called_once_with(GALAXY_URL, GALAXY_KEY)


def test_a_missing_url_is_a_usage_error(runner: CliRunner, galaxy: MagicMock) -> None:
    result = runner.invoke(cli, ["connect", "--galaxy-key", GALAXY_KEY])

    assert result.exit_code == 2
    assert "No Galaxy URL. Pass --galaxy-url or set GALAXY_URL." in result.output
    galaxy.assert_not_called()


def test_a_missing_key_is_a_usage_error(runner: CliRunner, galaxy: MagicMock) -> None:
    result = runner.invoke(cli, ["connect", "--galaxy-url", GALAXY_URL])

    assert result.exit_code == 2
    assert "No Galaxy API key. Pass --galaxy-key or set GALAXY_KEY." in result.output
    galaxy.assert_not_called()


def test_an_empty_credential_is_a_usage_error(runner: CliRunner, galaxy: MagicMock) -> None:
    result = runner.invoke(cli, ["connect", "--galaxy-url", GALAXY_URL, "--galaxy-key", ""])

    assert result.exit_code == 2
    assert "No Galaxy API key." in result.output
    galaxy.assert_not_called()


def test_connect_reports_what_the_connection_knows(runner: CliRunner, galaxy: MagicMock) -> None:
    result = runner.invoke(cli, ["connect", "-o", "json", "--galaxy-url", GALAXY_URL, "--galaxy-key", GALAXY_KEY])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "requested_url": GALAXY_URL,
        "resolved_url": "https://resolved.example",
        "version": {"version_major": "24.1"},
        "user": {"username": "tester"},
    }


def test_connect_prints_a_titled_report_by_default(runner: CliRunner, galaxy: MagicMock) -> None:
    result = runner.invoke(cli, ["connect", "--galaxy-url", GALAXY_URL, "--galaxy-key", GALAXY_KEY])

    assert result.exit_code == 0
    assert result.stdout.splitlines()[0] == "Connected to Galaxy"
    assert "  requested_url: https://galaxy.example" in result.stdout


def test_connect_closes_the_connection(runner: CliRunner, galaxy: MagicMock) -> None:
    runner.invoke(cli, ["connect", "--galaxy-url", GALAXY_URL, "--galaxy-key", GALAXY_KEY])

    galaxy.return_value.connect.return_value.__exit__.assert_called_once()


def test_a_failure_to_connect_is_reported_on_stderr(runner: CliRunner, galaxy: MagicMock) -> None:
    galaxy.side_effect = Exception("could not reach Galaxy")

    result = runner.invoke(cli, ["connect", "--galaxy-url", GALAXY_URL, "--galaxy-key", GALAXY_KEY])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "Galaxy error" in result.stderr
    assert "error: could not reach Galaxy" in result.stderr


def test_a_failure_is_reported_as_json_when_asked(runner: CliRunner, galaxy: MagicMock) -> None:
    galaxy.side_effect = Exception("could not reach Galaxy")

    result = runner.invoke(cli, ["connect", "-o", "json", "--galaxy-url", GALAXY_URL, "--galaxy-key", GALAXY_KEY])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert json.loads(result.stderr) == {"error": "could not reach Galaxy"}


def test_the_help_of_a_command_comes_from_its_docstring(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["connect", "--help"])

    assert result.exit_code == 0
    assert "Check that Galaxy is reachable and that your API key works." in result.output


def test_the_help_of_a_command_names_the_credential_environment_variables(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["connect", "--help"])

    assert f"[env: {URL_ENV}]" in result.output
    assert f"[env: {KEY_ENV}]" in result.output


def test_output_defaults_to_text(runner: CliRunner) -> None:
    command = command_returning(lambda: Report(title="A report", payload={"user": "tester"}))

    result = runner.invoke(command, [])

    assert result.exit_code == 0
    assert result.stdout == "A report\n  user: tester\n"


def test_output_json_prints_the_payload(runner: CliRunner) -> None:
    command = command_returning(lambda: Report(title="A report", payload={"user": "tester"}))

    result = runner.invoke(command, ["--output", "json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"user": "tester"}


def test_an_unknown_output_format_is_a_usage_error(runner: CliRunner) -> None:
    command = command_returning(lambda: Report(title="A report"))

    result = runner.invoke(command, ["-o", "yaml"])

    assert result.exit_code == 2


def test_a_raised_error_does_not_reach_the_user_as_a_traceback(runner: CliRunner) -> None:
    def fail() -> Report:
        raise RuntimeError("something broke")

    result = runner.invoke(command_returning(fail), [])

    assert result.exit_code == 1
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "Traceback" not in result.output
    assert "something broke" in result.stderr


def test_galaxy_command_registers_the_command_on_the_group() -> None:
    assert "connect" in cli.commands


def test_galaxy_command_gives_a_command_both_credential_flags() -> None:
    def report_nothing() -> Report:
        """Report nothing at all."""
        return Report(title="Nothing")

    command = galaxy_command(report_nothing)
    flags = {option for param in command.params for option in param.opts}

    assert {"--galaxy-url", "--galaxy-key", "-o", "--output"} <= flags
    assert command.name == "report-nothing"


def test_the_group_reports_its_version(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert result.output.startswith("nova, version ")


def test_main_runs_the_group(monkeypatch: pytest.MonkeyPatch) -> None:
    group = MagicMock(return_value="exit value")
    monkeypatch.setattr(cli_module, "cli", group)

    assert main() == "exit value"
    group.assert_called_once_with()


def test_main_is_the_entry_point_exported_by_the_package() -> None:
    import nova.galaxy.cli as package

    assert package.main is cli_module.main


def test_main_registers_the_commands_it_did_not_import_at_startup() -> None:
    """``main`` imports the commands itself, so a fresh interpreter still knows them."""
    entry_point = subprocess.run(
        [sys.executable, "-c", "from nova.galaxy.cli import main; main()", "connect", "--help"],
        capture_output=True,
        text=True,
    )

    assert entry_point.returncode == 0
    assert "Check that Galaxy is reachable and that your API key works." in entry_point.stdout


def test_the_group_help_describes_the_tool(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "Work with a Galaxy instance from the command-line." in result.output
    assert "connect" in result.output


def test_no_arguments_shows_the_usage(runner: CliRunner) -> None:
    result = runner.invoke(cli, [])

    assert result.exit_code == 2
    assert "Usage:" in result.output
