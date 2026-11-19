"""Builds a realistic demo shop for local testing:  uv run python -m app.cli seed-demo

It runs the last 30 days of a kirana store through the real services (products, deliveries, sales, damage,
count corrections, expiry write-offs, nightly stock refresh), so stock, the ledger, alerts, notifications
and the activity log are all consistent — exactly what the app would have produced.

To give the history real dates, each step runs "at" a past moment: the app's clock functions are pointed
at that moment and MySQL's session clock (SET TIMESTAMP) makes database timestamps match.
Never runs in production, and only fills a shop that has no products yet.
"""

import io
import random
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import Connection, func, select, text
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.core import clock
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.demo_data import (
    DELETED_PRODUCT,
    DEMO_DAYS,
    DEMO_PASSWORD,
    DEMO_PRODUCTS,
    DEMO_RANDOM_SEED,
    DEMO_SELLERS,
    STORE_DETAILS,
    DemoProduct,
)
from app.enums.role import Role
from app.enums.setting_key import SettingKey
from app.enums.stock import StockReason
from app.models import Brand, Category, Product, ProductBatch, Unit, User
from app.models import Role as RoleModel
from app.services.audit import AuditLogger, RequestContext
from app.services.catalogue.brand_unit_service import BrandService
from app.services.catalogue.product_service import ProductService
from app.services.inventory.fefo import is_expired
from app.services.inventory.inventory_service import InventoryService
from app.services.inventory.stock_cache import refresh_all_stock
from app.services.seller_service import SellerService
from app.services.settings_service import SettingsService

# Times of day (store time) for each kind of activity.
SETUP_TIME = time(7, 0)
NIGHTLY_TIME = time(0, 5)
DELIVERY_TIME = time(8, 30)
OPEN_HOUR, CLOSE_HOUR = 9, 21
WRITE_OFF_EVERY_DAYS = 5
WRITE_OFF_STOP_DAYS = 6  # the last write-off is this many days ago, so some expired stock is still on the shelf
COUNT_CHECK_EVERY_DAYS = 7
DAMAGE_CHANCE = 0.03
PERISHABLE_DAYS = 7  # shelf life up to this counts as perishable (frequent small deliveries)
FORMER_SELLER_LEAVES_ON_DAY = 10
COST_VARIATION = 0.03  # each delivery's cost price varies by up to ±3%
NO_PHOTO_EVERY = 6  # every 6th product has no photo, to show the placeholder
DEMO_CONTEXT = RequestContext(ip_address="127.0.0.1", user_agent="seed-demo")

_CLOCK_FUNCTIONS = ("utc_now", "store_now", "store_today")


class DemoError(RuntimeError):
    pass


@contextmanager
def _at(db: Session, moment: datetime) -> Iterator[None]:
    """Run code as if it were `moment` (naive UTC): app clock functions and database NOW() both move."""
    aware = moment.replace(tzinfo=UTC)
    originals = {name: getattr(clock, name) for name in _CLOCK_FUNCTIONS}
    fakes: dict[str, Callable[[], Any]] = {
        "utc_now": lambda: moment,
        "store_now": lambda: aware.astimezone(clock.store_tz()),
        "store_today": lambda: aware.astimezone(clock.store_tz()).date(),
    }
    patched = []
    for module in list(sys.modules.values()):  # services import the functions directly, so patch every copy
        if not getattr(module, "__name__", "").startswith("app"):
            continue
        for name in _CLOCK_FUNCTIONS:
            if getattr(module, name, None) is originals[name]:
                setattr(module, name, fakes[name])
                patched.append((module, name))
    db.execute(text("SET TIMESTAMP = :ts"), {"ts": aware.timestamp()})
    try:
        yield
    finally:
        for module, name in patched:
            setattr(module, name, originals[name])
        db.execute(text("SET TIMESTAMP = DEFAULT"))


def _moment(day: date, at: time) -> datetime:
    """Store-time day + time → naive UTC."""
    return datetime.combine(day, at, tzinfo=clock.store_tz()).astimezone(UTC).replace(tzinfo=None)


def _decimal(value: float, places: str = "0.01") -> Decimal:
    return Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def _photo(product: DemoProduct, colour: tuple[int, int, int]) -> UploadFile:
    """A simple packshot-style image: coloured background, white label with the product name."""
    size = 800
    image = Image.new("RGB", (size, size), colour)
    draw = ImageDraw.Draw(image)
    light = tuple(min(255, c + 45) for c in colour)
    draw.ellipse([-200, -260, 620, 560], fill=light)
    draw.rounded_rectangle([110, 230, 690, 610], radius=48, fill=(255, 255, 255))
    brand_font = ImageFont.load_default(size=40)
    name_font = ImageFont.load_default(size=54)
    if product.brand:
        draw.text((size / 2, 300), product.brand.upper(), font=brand_font, fill=colour, anchor="mm")
    words, lines = product.name.replace(product.brand or "", "").split(), [""]
    for word in words:
        candidate = f"{lines[-1]} {word}".strip()
        if draw.textlength(candidate, font=name_font) > 520 and lines[-1]:
            lines.append(word)
        else:
            lines[-1] = candidate
    for i, line in enumerate(lines[:3]):
        draw.text((size / 2, 400 + i * 66), line, font=name_font, fill=(30, 40, 35), anchor="mm")
    out = io.BytesIO()
    image.save(out, "JPEG", quality=88)
    out.seek(0)
    return UploadFile(file=out, filename="demo.jpg")


CATEGORY_COLOURS = {
    "Dairy": (59, 130, 246),
    "Grocery": (180, 120, 40),
    "Snacks": (234, 88, 12),
    "Cold Drinks": (190, 24, 60),
    "Personal Care": (124, 58, 237),
    "Household": (13, 148, 136),
    "Bakery": (202, 138, 4),
    "Spices": (185, 28, 28),
    "Cleaning Products": (22, 163, 74),
    "Stationery": (37, 99, 235),
}


class DemoShop:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditLogger(db, DEMO_CONTEXT)
        self.rng = random.Random(DEMO_RANDOM_SEED)
        self.admin = self._admin()
        self.today = clock.store_today()
        self.start = self.today - timedelta(days=DEMO_DAYS)
        self.inventory = InventoryService(db, self.audit)
        self.products: dict[str, tuple[DemoProduct, Product]] = {}
        self.sellers: dict[str, User] = {}

    # --- Entry point ------------------------------------------------------------------------------

    def build(self) -> dict[str, int]:
        if self.db.scalar(select(func.count(Product.id)).where(Product.store_id == self.admin.store_id)):
            raise DemoError("This shop already has products. seed-demo only fills an empty shop.")

        with _at(self.db, _moment(self.start, SETUP_TIME)):
            self._store_details()
            self._sellers()
            self._catalogue()
            for spec, product in self.products.values():
                self._deliver(product, spec, self.start, self.admin)

        for offset in range(1, DEMO_DAYS):
            self._simulate_day(offset, self.start + timedelta(days=offset))

        # Back to real time: tonight's stock refresh and today's expiry summary, as the scheduled jobs would.
        refresh_all_stock(self.db)
        from app.cli import send_expiry_alerts

        send_expiry_alerts(self.db, force=True)
        return {"products": len(self.products), "sellers": len(self.sellers), "days": DEMO_DAYS}

    # --- Setup ------------------------------------------------------------------------------------

    def _admin(self) -> User:
        admin = self.db.scalar(select(User).join(User.role).where(RoleModel.name == Role.ADMIN).order_by(User.id))
        if admin is None:
            raise DemoError("No admin found. Run `python -m app.cli seed` first.")
        return admin

    def _store_details(self) -> None:
        keys = {
            "tagline": SettingKey.STORE_TAGLINE,
            "phone": SettingKey.STORE_PHONE,
            "whatsapp": SettingKey.STORE_WHATSAPP,
            "address": SettingKey.STORE_ADDRESS,
            "hours": SettingKey.STORE_HOURS,
        }
        SettingsService(self.db, self.audit).update(self.admin, {keys[k]: v for k, v in STORE_DETAILS.items()})

    def _sellers(self) -> None:
        service = SellerService(self.db, self.audit)
        for spec in DEMO_SELLERS:
            data = {"name": spec.name, "email": spec.email, "phone": spec.phone, "locale": spec.locale}
            seller = service.create(self.admin, data | {"password": DEMO_PASSWORD}, list(spec.permissions))
            self.sellers[spec.email] = seller

    def _catalogue(self) -> None:
        store_id = self.admin.store_id
        categories = {c.name: c.id for c in self.db.scalars(select(Category).where(Category.store_id == store_id))}
        units = {u.short_name: u.id for u in self.db.scalars(select(Unit))}
        brands: dict[str, int] = {
            b.name: b.id for b in self.db.scalars(select(Brand).where(Brand.store_id == store_id))
        }
        brand_service, product_service = BrandService(self.db, self.audit), ProductService(self.db, self.audit)

        for index, spec in enumerate((*DEMO_PRODUCTS, DELETED_PRODUCT)):
            if spec.brand and spec.brand not in brands:
                brands[spec.brand] = brand_service.create(self.admin, {"name": spec.brand}).id
            data: dict[str, Any] = {
                "name": spec.name,
                "category_id": categories[spec.category],
                "unit_id": units[spec.unit],
                "brand_id": brands.get(spec.brand) if spec.brand else None,
                "selling_price": _decimal(spec.selling),
                "mrp": _decimal(spec.mrp) if spec.mrp else None,
                "purchase_price": _decimal(spec.cost),
                "min_stock_level": _decimal(spec.min_stock, "0.001"),
                "track_expiry": spec.shelf_life is not None,
                "show_expiry_to_customers": spec.shelf_life is not None,
                "is_featured": spec.featured,
                "is_visible_to_customers": not spec.hidden,
                "description": spec.description or f"{spec.name}. Genuine product, stored fresh at our shop.",
            }
            if spec.offer:
                data |= {
                    "offer_price": _decimal(spec.offer),
                    "offer_starts_at": self.today - timedelta(days=2),
                    "offer_ends_at": self.today + timedelta(days=7),
                }
            product = product_service.create(self.admin, data)
            if index % NO_PHOTO_EVERY != NO_PHOTO_EVERY - 1:
                product_service.add_image(self.admin, product, _photo(spec, CATEGORY_COLOURS[spec.category]))
            if spec is DELETED_PRODUCT:
                product_service.delete(self.admin, product)
            else:
                self.products[spec.name] = (spec, product)

    # --- One day in the shop -----------------------------------------------------------------------

    def _simulate_day(self, offset: int, day: date) -> None:
        with _at(self.db, _moment(day, NIGHTLY_TIME)):
            refresh_all_stock(self.db, self.admin.store_id)  # what the 00:05 cron job does

        manager, cashier, former = (self.sellers[s.email] for s in DEMO_SELLERS if s.email != "simran@demo.test")
        if offset == FORMER_SELLER_LEAVES_ON_DAY:
            with _at(self.db, _moment(day, SETUP_TIME)):
                SellerService(self.db, self.audit).set_active(self.admin, former, False)

        with _at(self.db, _moment(day, DELIVERY_TIME)):
            for spec, product in self.products.values():
                if self._needs_delivery(spec, product, offset):
                    self._deliver(product, spec, day, self.rng.choice([self.admin, manager]))

        counter_staff = [cashier, manager] if offset >= FORMER_SELLER_LEAVES_ON_DAY else [cashier, former]
        for spec, product in self.products.values():
            self._sell(spec, product, day, self.rng.choice(counter_staff))
            if spec.shelf_life and spec.shelf_life <= PERISHABLE_DAYS and self.rng.random() < DAMAGE_CHANCE:
                self._damage(product, day, manager, StockReason.SPOILED)
            elif spec.unit == "btl" and self.rng.random() < DAMAGE_CHANCE / 2:
                self._damage(product, day, manager, StockReason.BROKEN)

        if offset % COUNT_CHECK_EVERY_DAYS == 0:
            for _spec, product in self.rng.sample(list(self.products.values()), 3):
                self._count_check(product, day, manager)
        if offset % WRITE_OFF_EVERY_DAYS == 0 and offset <= DEMO_DAYS - WRITE_OFF_STOP_DAYS:
            self._write_off(day)

    def _needs_delivery(self, spec: DemoProduct, product: Product, offset: int) -> bool:
        if spec.stop_restocking_after is not None and offset >= spec.stop_restocking_after:
            return False
        self.db.refresh(product)
        level = spec.demand * 2.5 if spec.shelf_life and spec.shelf_life <= PERISHABLE_DAYS else spec.min_stock * 1.5
        return product.sellable_stock < _decimal(level, "0.001")

    def _deliver(self, product: Product, spec: DemoProduct, day: date, user: User) -> None:
        cost = spec.cost * (1 + self.rng.uniform(-COST_VARIATION, COST_VARIATION))
        data: dict[str, Any] = {
            "product_id": product.id,
            "quantity": _decimal(spec.restock, "0.001"),
            "purchase_price": _decimal(cost),
            "reason": StockReason.PURCHASE,
        }
        if spec.shelf_life:
            data["expiry_date"] = day + timedelta(days=spec.shelf_life)
            data["manufacturing_date"] = day - timedelta(days=1)
        self.inventory.stock_in(user, data, key=None)

    def _sell(self, spec: DemoProduct, product: Product, day: date, user: User) -> None:
        wanted = spec.demand * self.rng.uniform(0.3, 1.7)
        quantity = round(wanted * 2) / 2 if product.unit.allows_decimal else round(wanted)
        available = sum((b.quantity_remaining for b in self._batches(product) if not is_expired(b, day)), Decimal(0))
        quantity_dec = min(_decimal(quantity, "0.001"), available)
        if quantity_dec <= 0:
            return
        at = time(self.rng.randint(OPEN_HOUR, CLOSE_HOUR - 1), self.rng.randint(0, 59))
        with _at(self.db, _moment(day, at)):
            reason = StockReason.SOLD_MANUALLY if self.rng.random() > 0.03 else StockReason.PERSONAL_USE
            data = {"product_id": product.id, "quantity": quantity_dec, "reason": reason}
            self.inventory.stock_out(user, data, key=None)

    def _damage(self, product: Product, day: date, user: User, reason: StockReason) -> None:
        batch = next((b for b in self._batches(product) if b.quantity_remaining >= 1), None)
        if batch is None:
            return
        with _at(self.db, _moment(day, time(CLOSE_HOUR, 15))):
            data = {
                "batch_id": batch.id,
                "quantity": Decimal(1),
                "reason": reason,
                "notes": "Found while arranging the shelf.",
            }
            self._try(lambda: self.inventory.damage(user, data, key=None))

    def _count_check(self, product: Product, day: date, user: User) -> None:
        batch = next((b for b in self._batches(product) if b.quantity_remaining >= 3), None)
        if batch is None:
            return
        step = Decimal("0.5") if product.unit.allows_decimal else Decimal(1)
        counted = batch.quantity_remaining + step * self.rng.choice([-2, -1, 1])
        with _at(self.db, _moment(day, time(CLOSE_HOUR, 30))):
            data = {"batch_id": batch.id, "counted_quantity": counted, "notes": "Weekly shelf count."}
            self._try(lambda: self.inventory.adjust(user, data, key=None))

    def _write_off(self, day: date) -> None:
        expired = self.db.scalars(
            select(ProductBatch.id).where(
                ProductBatch.store_id == self.admin.store_id,
                ProductBatch.quantity_remaining > 0,
                ProductBatch.expiry_date < day,
            )
        ).all()
        if expired:
            with _at(self.db, _moment(day, time(CLOSE_HOUR, 45))):
                notes = "Removed from the shelf and thrown away."
                self._try(lambda: self.inventory.write_off_expired(self.admin, list(expired), notes, key=None))

    # --- Helpers ----------------------------------------------------------------------------------

    def _batches(self, product: Product) -> list[ProductBatch]:
        return list(self.db.scalars(select(ProductBatch).where(ProductBatch.product_id == product.id)))

    def _try(self, action: Callable[[], Any]) -> None:
        """Rare simulated moves that the shop's rules refuse are simply skipped, as a real person would."""
        try:
            action()
        except AppError:
            self.db.rollback()


def build_demo_shop(connection: Connection) -> dict[str, int]:
    if get_settings().is_production:
        raise DemoError("seed-demo never runs in production.")
    # One connection for the whole run, so the database clock set by SET TIMESTAMP stays in effect.
    with Session(bind=connection, autoflush=False, expire_on_commit=False) as db:
        return DemoShop(db).build()
