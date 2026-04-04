"""Flowger Typer CLI entrypoint."""

import typer

from flowger.entrypoints.cli.commands.accounts import accounts
from flowger.entrypoints.cli.commands.authorize import authorize
from flowger.entrypoints.cli.commands.config import config
from flowger.entrypoints.cli.commands.export import export
from flowger.entrypoints.cli.commands.login import login
from flowger.entrypoints.cli.commands.sync_transactions import sync_transactions

app = typer.Typer(help="Flowger - Bank transaction synchronization utility.", no_args_is_help=True)

app.command()(config)
app.command()(login)
app.command()(authorize)
app.command()(accounts)
app.command()(sync_transactions)
app.command()(export)

if __name__ == "__main__":
    app()
