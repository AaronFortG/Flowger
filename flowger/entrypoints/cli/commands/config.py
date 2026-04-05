import typer

from flowger.infrastructure.config import get_settings


def config() -> None:
    """Verify application configuration is valid."""
    try:
        get_settings()
        typer.echo("Configuration is valid.")
    except Exception:
        typer.secho(
            "Configuration error: One or more required environment variables "
            "are missing or invalid.",
            fg=typer.colors.RED,
        )
        typer.echo("Run 'flowger config --help' or check your .env file.")
        raise typer.Exit(1)
