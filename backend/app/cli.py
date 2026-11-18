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
    from datetime import datetime, time, timedelta

    from sqlalchemy import select

    from app.core.clock import store_now
    from app.core.constants import EXPIRY_DIGEST_WINDOW_MINUTES
    from app.enums.setting_key import SettingKey
    from app.models import Store
    from app.services.notifications.alerts import AlertService
    from app.services.notifications.push import deliver
    from app.services.settings_service import get_setting

    sent = 0
    with SessionLocal() as db:
        for store in db.scalars(select(Store).where(Store.is_active.is_(True))):
            hour, minute = map(int, str(get_setting(db, store.id, SettingKey.EXPIRY_DIGEST_TIME)).split(":"))
            now = store_now()
            due = datetime.combine(now.date(), time(hour, minute), tzinfo=now.tzinfo)
            if not force and not (due <= now < due + timedelta(minutes=EXPIRY_DIGEST_WINDOW_MINUTES)):
                continue
            messages = AlertService(db).expiry_digest(store.id)
            db.commit()
            deliver(db, messages)
            sent += len(messages)
    typer.echo(f"Expiry alerts done ({sent} push messages).")


@cli.command("version")
def version() -> None:
    typer.echo("Smart Kirana API 1.0.0")


if __name__ == "__main__":
    cli()
