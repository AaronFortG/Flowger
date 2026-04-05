import typer
from pydantic import ValidationError

from flowger.infrastructure.config import get_settings


def config() -> None:
    """Verify application configuration is valid."""
    try:
        get_settings()
        typer.echo("Configuration is valid.")
    except ValidationError as e:
        typer.secho("Configuration validation failed:", fg=typer.colors.RED)
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            typer.echo(f"  - {loc}: {error['msg']}")
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Configuration error: {e}", fg=typer.colors.RED)
        typer.echo("Run 'flowger config --help' or check your .env file.")
        raise typer.Exit(1)
