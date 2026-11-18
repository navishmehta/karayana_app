"""Management commands.  Usage:  uv run python -m app.cli seed"""

import logging

import typer

from app.core.database import SessionLocal
from app.db import seed

cli = typer.Typer(help="Smart Kirana management commands", no_args_is_help=True)


@cli.command("seed")
def seed_command() -> None:
    """Create the store, roles, permissions, admin, units, settings and starter categories."""
    logging.basicConfig(level=logging.INFO)
    with SessionLocal() as db:
        seed.run(db)
    typer.echo("Seed complete.")


@cli.command("refresh-stock")
def refresh_stock_command() -> None:
    """Nightly (00:05 IST): batches that expired at midnight stop counting as sellable."""
    from app.services.inventory.stock_cache import refresh_all_stock

    with SessionLocal() as db:
        count = refresh_all_stock(db)
    typer.echo(f"Refreshed stock for {count} products.")


@cli.command("version")
def version() -> None:
    typer.echo("Smart Kirana API 1.0.0")


if __name__ == "__main__":
    cli()
