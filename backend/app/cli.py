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


@cli.command("send-expiry-alerts")
def send_expiry_alerts_command(
    force: bool = typer.Option(False, "--force", help="Send now instead of waiting for the store's alert time"),
) -> None:
    """Cron: run every 15 minutes. Sends the daily expiry summary once, at the time set in store settings."""
    with SessionLocal() as db:
        sent = send_expiry_alerts(db, force=force)
    typer.echo(f"Expiry alerts done ({sent} push messages).")


def send_expiry_alerts(db, *, force: bool) -> int:  # noqa: ANN001
    from sqlalchemy import select

    from app.core.clock import store_now
    from app.core.constants import EXPIRY_DIGEST_WINDOW_MINUTES
    from app.enums.setting_key import SettingKey
    from app.models import Store
    from app.services.notifications.alerts import AlertService, is_digest_due
    from app.services.notifications.push import deliver
    from app.services.settings_service import get_setting

    sent = 0
    for store in db.scalars(select(Store).where(Store.is_active.is_(True))).all():
        digest_time = str(get_setting(db, store.id, SettingKey.EXPIRY_DIGEST_TIME))
        if not force and not is_digest_due(store_now(), digest_time, EXPIRY_DIGEST_WINDOW_MINUTES):
            continue
        messages = AlertService(db).expiry_digest(store.id)
        db.commit()
        deliver(db, messages)
        sent += len(messages)
    return sent


@cli.command("version")
def version() -> None:
    typer.echo("Smart Kirana API 1.0.0")


if __name__ == "__main__":
    cli()
