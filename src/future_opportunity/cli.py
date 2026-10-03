import typer

app = typer.Typer(help="Market-neutral arbitrage workbench")


@app.command()
def version() -> None:
    """Print the CLI version."""
    typer.echo("future-opportunity 0.1.0")


@app.command()
def quickstart(strategy: str = "funding-carry") -> None:
    """Show the safe V0 quickstart mode."""
    typer.echo(f"strategy={strategy} execution=paper live_orders=false")
