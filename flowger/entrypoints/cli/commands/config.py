import typer

from flowger.infrastructure.config import get_settings


def config() -> None:
    """Verify application configuration is valid."""
    try:
        get_settings()
        typer.echo("Configuration is valid.")
    except Exception as e:
        typer.secho(f"Configuration error: {e!r}", fg=typer.colors.RED)
        raise typer.Exit(1)
