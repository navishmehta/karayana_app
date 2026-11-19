"""Demo shop for local testing (`python -m app.cli seed-demo`). Plain data only — the logic is in app/db/demo.py.

Prices are in rupees. Shelf life is in days (None = no expiry tracking). Daily demand is the average number
of units sold per day; the simulation varies it randomly but reproducibly.
"""

from dataclasses import dataclass
from typing import Final

from app.enums.permission import Permission

DEMO_DAYS: Final = 30  # how much stock history to create
DEMO_RANDOM_SEED: Final = 2026  # same seed -> same demo shop every time
DEMO_PASSWORD: Final = "Demo@1234"  # password for every demo seller (local testing only)
RUN_OUT_AFTER_DAY: Final = 10  # products that stop being delivered early end up out of stock
RUN_LOW_AFTER_DAY: Final = 24  # ...and these, stopped later, end up low on stock

STORE_DETAILS: Final = {
    "tagline": "Fresh groceries & daily needs since 1998",
    "phone": "9876543210",
    "whatsapp": "9876543210",
    "address": "Shop 12, Main Bazaar, Model Town, Ludhiana, Punjab 141002",
    "hours": "7:30 AM – 9:30 PM, all days",
}


@dataclass(frozen=True)
class DemoSeller:
    name: str
    email: str
    phone: str
    locale: str
    permissions: tuple[Permission, ...]
    active: bool = True


P = Permission
DEMO_SELLERS: Final = (
    DemoSeller(  # trusted shop manager: almost everything, including costs and reports
        "Gurpreet Singh",
        "gurpreet@demo.test",
        "9812345601",
        "pa",
        (
            P.DASHBOARD_VIEW,
            P.PRODUCTS_VIEW,
            P.PRODUCTS_UPDATE,
            P.CATEGORIES_VIEW,
            P.CATEGORIES_CREATE,
            P.CATEGORIES_UPDATE,
            P.PRICING_VIEW_PURCHASE,
            P.PRICING_VIEW_SELLING,
            P.PRICING_UPDATE_SELLING,
            P.STOCK_VIEW,
            P.STOCK_UPDATE,
            P.EXPIRY_VIEW,
            P.EXPIRY_UPDATE,
            P.REPORTS_VIEW,
            P.REPORTS_EXPORT,
        ),
    ),
    DemoSeller(  # counter staff: sees selling prices and moves stock, never sees costs
        "Aman Kumar",
        "aman@demo.test",
        "9812345602",
        "en",
        (P.PRODUCTS_VIEW, P.PRICING_VIEW_SELLING, P.STOCK_VIEW, P.STOCK_UPDATE, P.EXPIRY_VIEW),
    ),
    DemoSeller(  # helper who only looks things up
        "Simran Kaur",
        "simran@demo.test",
        "9812345603",
        "pa",
        (P.PRODUCTS_VIEW, P.STOCK_VIEW),
    ),
    DemoSeller(  # left the shop: account switched off, history kept
        "Rohit Sharma",
        "rohit@demo.test",
        "9812345604",
        "en",
        (P.PRODUCTS_VIEW, P.STOCK_VIEW, P.STOCK_UPDATE),
        active=False,
    ),
)


@dataclass(frozen=True)
class DemoProduct:
    name: str
    category: str  # English category name from seed_data.CATEGORIES
    unit: str  # unit short name from seed_data.UNITS
    brand: str | None
    selling: float
    mrp: float | None
    cost: float
    shelf_life: int | None  # days; None = not tracked
    demand: float  # average units sold per day
    restock: float  # quantity received per delivery
    min_stock: float
    offer: float | None = None  # offer price, running for the next week
    featured: bool = False
    hidden: bool = False  # not shown to customers
    stop_restocking_after: int | None = None  # simulation day after which deliveries stop (runs low / out)
    description: str | None = None


D = DemoProduct
DEMO_PRODUCTS: Final = (
    # Dairy: short shelf life, daily deliveries
    D("Amul Taaza Toned Milk 1L", "Dairy", "pcs", "Amul", 66, 68, 61, 3, 18, 40, 15, featured=True),
    D("Amul Gold Full Cream Milk 500ml", "Dairy", "pcs", "Amul", 34, 35, 31, 3, 12, 30, 10),
    D("Verka Paneer 200g", "Dairy", "pcs", "Verka", 90, 95, 76, 6, 4, 15, 5, featured=True),
    D(
        "Amul Butter 500g",
        "Dairy",
        "pcs",
        "Amul",
        285,
        290,
        262,
        120,
        1.2,
        12,
        6,
        offer=275,
        stop_restocking_after=RUN_LOW_AFTER_DAY,
    ),
    D("Mother Dairy Dahi 400g", "Dairy", "pcs", "Mother Dairy", 50, 52, 43, 7, 5, 18, 6),
    D(
        "Amul Cheese Slices 200g",
        "Dairy",
        "pkt",
        "Amul",
        145,
        150,
        128,
        90,
        0.6,
        8,
        4,
        stop_restocking_after=RUN_OUT_AFTER_DAY,
    ),
    D("Verka Lassi 200ml", "Dairy", "btl", "Verka", 20, 20, 16, 10, 4, 24, 8),
    # Grocery staples (sold loose by weight or packed)
    D(
        "Aashirvaad Whole Wheat Atta 5kg",
        "Grocery",
        "pcs",
        "Aashirvaad",
        245,
        280,
        214,
        120,
        1.5,
        15,
        5,
        offer=229,
        featured=True,
    ),
    D("India Gate Basmati Rice", "Grocery", "kg", "India Gate", 120, 140, 98, None, 3.5, 50, 10),
    D(
        "Tata Sampann Toor Dal",
        "Grocery",
        "kg",
        "Tata Sampann",
        165,
        180,
        142,
        None,
        1.8,
        20,
        5,
        offer=155,
        stop_restocking_after=RUN_OUT_AFTER_DAY,
    ),
    D("Moong Dal (loose)", "Grocery", "kg", None, 130, None, 108, None, 1.2, 20, 5),
    D("Fortune Sunflower Oil 1L", "Grocery", "btl", "Fortune", 155, 175, 138, 270, 2.5, 24, 8, featured=True),
    D("Tata Salt 1kg", "Grocery", "pkt", "Tata", 28, 28, 23, None, 3, 40, 10),
    D("Madhur Sugar", "Grocery", "kg", "Madhur", 48, None, 41, None, 4, 50, 10),
    D(
        "Saffola Gold Oil 1L",
        "Grocery",
        "btl",
        "Saffola",
        210,
        235,
        188,
        270,
        0.8,
        12,
        4,
        stop_restocking_after=RUN_LOW_AFTER_DAY,
    ),
    D(
        "Kabuli Chana (loose)",
        "Grocery",
        "kg",
        None,
        140,
        None,
        115,
        None,
        0.8,
        15,
        4,
        hidden=True,
        description="Back-room stock, sold on request only.",
    ),
    # Snacks
    D("Haldiram's Aloo Bhujia 400g", "Snacks", "pkt", "Haldiram's", 105, 110, 88, 120, 2, 25, 8, featured=True),
    D("Lay's Classic Salted 52g", "Snacks", "pkt", "Lay's", 20, 20, 16, 60, 6, 60, 20),
    D("Kurkure Masala Munch 90g", "Snacks", "pkt", "Kurkure", 20, 20, 16, 60, 5, 50, 15),
    D("Parle-G Biscuits 800g", "Snacks", "pkt", "Parle", 90, 95, 79, 180, 1.5, 20, 6),
    D("Britannia Good Day Cashew 200g", "Snacks", "pkt", "Britannia", 40, 45, 34, 150, 2, 24, 8, offer=36),
    D(
        "Bikaji Bhujia Sev 400g",
        "Snacks",
        "pkt",
        "Bikaji",
        98,
        105,
        82,
        120,
        0.8,
        12,
        4,
        stop_restocking_after=RUN_LOW_AFTER_DAY,
    ),
    # Cold drinks
    D(
        "Coca-Cola 750ml",
        "Cold Drinks",
        "btl",
        "Coca-Cola",
        40,
        45,
        34,
        150,
        3,
        36,
        12,
        stop_restocking_after=RUN_OUT_AFTER_DAY,
    ),
    D("Thums Up 2L", "Cold Drinks", "btl", "Thums Up", 95, 100, 82, 150, 1.5, 18, 6, offer=85, featured=True),
    D("Sprite 750ml", "Cold Drinks", "btl", "Sprite", 40, 45, 34, 150, 2, 30, 10),
    D("Frooti Mango Drink 600ml", "Cold Drinks", "btl", "Frooti", 35, 38, 29, 120, 2.5, 30, 10),
    D("Bisleri Water 1L", "Cold Drinks", "btl", "Bisleri", 20, 20, 14, 365, 6, 60, 20),
    D("Red Bull Energy Drink 250ml", "Cold Drinks", "pcs", "Red Bull", 125, 125, 108, 365, 0.5, 12, 4),
    # Personal care
    D("Dove Cream Beauty Bar 100g", "Personal Care", "pcs", "Dove", 58, 62, 49, None, 1.5, 24, 8),
    D("Colgate Strong Teeth 200g", "Personal Care", "pcs", "Colgate", 115, 125, 98, None, 1, 18, 6),
    D(
        "Head & Shoulders Shampoo 180ml",
        "Personal Care",
        "btl",
        "Head & Shoulders",
        199,
        215,
        172,
        None,
        0.5,
        10,
        3,
        offer=185,
        stop_restocking_after=RUN_LOW_AFTER_DAY,
    ),
    D("Dettol Handwash Refill 750ml", "Personal Care", "pcs", "Dettol", 99, 109, 84, None, 0.7, 12, 4),
    D("Gillette Guard Razor", "Personal Care", "pcs", "Gillette", 30, 30, 24, None, 0.4, 20, 5),
    # Household
    D("Harpic Toilet Cleaner 500ml", "Household", "btl", "Harpic", 98, 105, 84, None, 0.6, 12, 4),
    D("Good Knight Gold Flash Refill", "Household", "pcs", "Good Knight", 85, 89, 72, None, 0.8, 15, 5),
    D("Mangaldeep Agarbatti", "Household", "pkt", "Mangaldeep", 50, 50, 40, None, 1, 20, 6),
    D("Duracell AA Batteries (2)", "Household", "pkt", "Duracell", 110, 120, 92, None, 0.3, 10, 3),
    # Bakery: very short shelf life
    D("Britannia Brown Bread 400g", "Bakery", "pcs", "Britannia", 55, 60, 46, 4, 3, 12, 4, featured=True),
    D("Harvest Gold White Bread 400g", "Bakery", "pcs", "Harvest Gold", 45, 50, 38, 4, 4, 15, 5),
    D("Rusk Toast 300g", "Bakery", "pkt", "Britannia", 60, 65, 50, 90, 1, 15, 5),
    D("Pav (6 pcs)", "Bakery", "pkt", None, 30, None, 22, 3, 2.5, 10, 4),
    # Spices
    D("MDH Garam Masala 100g", "Spices", "pkt", "MDH", 88, 92, 74, 365, 0.6, 15, 5),
    D("Everest Turmeric Powder 200g", "Spices", "pkt", "Everest", 72, 78, 60, 365, 0.7, 15, 5),
    D("Catch Red Chilli Powder 200g", "Spices", "pkt", "Catch", 80, 86, 66, 365, 0.6, 15, 5),
    D("Jeera (loose)", "Spices", "kg", None, 520, None, 440, None, 0.15, 3, 1),
    # Cleaning
    D(
        "Vim Dishwash Bar 300g",
        "Cleaning Products",
        "pcs",
        "Vim",
        35,
        38,
        29,
        None,
        2,
        30,
        10,
        stop_restocking_after=RUN_OUT_AFTER_DAY,
    ),
    D("Surf Excel Easy Wash 1kg", "Cleaning Products", "pkt", "Surf Excel", 140, 150, 120, None, 0.8, 15, 5),
    D(
        "Lizol Floor Cleaner 975ml",
        "Cleaning Products",
        "btl",
        "Lizol",
        199,
        219,
        170,
        None,
        0.4,
        8,
        3,
        stop_restocking_after=RUN_LOW_AFTER_DAY,
    ),
    D("Scotch-Brite Scrub Pad (3)", "Cleaning Products", "pkt", "Scotch-Brite", 55, 60, 45, None, 0.6, 12, 4),
    # Stationery
    D("Classmate Notebook 172 pages", "Stationery", "pcs", "Classmate", 60, 65, 48, None, 0.8, 20, 6),
    D("Reynolds Ball Pen (pack of 5)", "Stationery", "pkt", "Reynolds", 50, 50, 38, None, 0.5, 10, 3),
    D("Fevicol MR 50g", "Stationery", "pcs", "Fevicol", 25, 25, 19, None, 0.3, 10, 3),
)

# A product the admin deleted (to try "Deleted" / restore later).
DELETED_PRODUCT: Final = D("Old Stock Chocolate Bar", "Snacks", "pcs", "Cadbury", 20, 20, 15, None, 0, 0, 0)
