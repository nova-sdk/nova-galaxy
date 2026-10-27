"""Command implementations for the CLI."""

from nova.galaxy.cli.cli import galaxy_command
from nova.galaxy.cli.report import Report
from nova.galaxy.connection import Connection


@galaxy_command
def connect(galaxy_url: str, galaxy_key: str) -> Report:
    """Check that Galaxy is reachable and that your API key works."""
    with Connection(galaxy_url, galaxy_key).connect() as connection:
        return Report(
            title="Connected to Galaxy",
            payload={
                "requested_url": galaxy_url,
                "resolved_url": connection.galaxy_url,
                "version": connection.get_version(),
                "user": connection.get_current_user(),
            },
        )
