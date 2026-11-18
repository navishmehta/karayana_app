"""Starter data. These become normal rows the admin can edit or delete — nothing here is hard-coded in app logic."""

from typing import Final

# (name, short name, allows decimal quantities)
UNITS: Final = [
    ("Piece", "pcs", False),
    ("Kilogram", "kg", True),
    ("Gram", "g", True),
    ("Litre", "L", True),
    ("Millilitre", "ml", True),
    ("Packet", "pkt", False),
    ("Box", "box", False),
    ("Dozen", "dozen", False),
    ("Bottle", "btl", False),
]

# English name -> Punjabi name
CATEGORIES: Final = {
    "Grocery": "ਕਰਿਆਨਾ",
    "Dairy": "ਡੇਅਰੀ",
    "Snacks": "ਸਨੈਕਸ",
    "Cold Drinks": "ਠੰਢੇ ਪੀਣ ਵਾਲੇ",
    "Personal Care": "ਨਿੱਜੀ ਦੇਖਭਾਲ",
    "Household": "ਘਰੇਲੂ ਸਾਮਾਨ",
    "Bakery": "ਬੇਕਰੀ",
    "Spices": "ਮਸਾਲੇ",
    "Cleaning Products": "ਸਫ਼ਾਈ ਦਾ ਸਾਮਾਨ",
    "Stationery": "ਸਟੇਸ਼ਨਰੀ",
}
