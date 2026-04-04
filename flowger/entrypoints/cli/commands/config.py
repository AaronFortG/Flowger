import typer

from flowger.infrastructure.config import get_settings


def config() -> None:
    """Verify application configuration is valid."""
    try:
        settings = get_settings()
        typer.echo("Configuration is valid.")
        typer.echo(f"Environment: {settings.enablebanking_environment}")
    except Exception as e:
        typer.secho(f"Configuration error: {e!r}", fg=typer.colors.RED)
        raise typer.Exit(1)
