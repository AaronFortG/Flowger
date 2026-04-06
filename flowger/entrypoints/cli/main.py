"""Flowger Typer CLI entrypoint."""

import typer

from flowger.entrypoints.cli.commands.accounts import accounts
from flowger.entrypoints.cli.commands.authorize import authorize
from flowger.entrypoints.cli.commands.config import config
from flowger.entrypoints.cli.commands.daemon import daemon
from flowger.entrypoints.cli.commands.export import export
from flowger.entrypoints.cli.commands.login import login
from flowger.entrypoints.cli.commands.setup import setup
from flowger.entrypoints.cli.commands.sync import sync

app = typer.Typer(help="Flowger - Bank transaction synchronization utility.", no_args_is_help=True)

app.command()(config)
app.command()(setup)
app.command()(login)
app.command()(authorize)
app.command()(accounts)
app.command()(sync)
app.command()(export)
app.command()(daemon)

if __name__ == "__main__":
    app()
