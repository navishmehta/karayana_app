"""Fixed technical constants used across the codebase (not environment-specific)."""

from typing import Final

API_V1_PREFIX: Final = "/api/v1"

# Money in rupees and paise; quantity allows loose items such as 1.250 kg.
MONEY_PRECISION: Final = 12
MONEY_DECIMALS: Final = 2
QUANTITY_PRECISION: Final = 12
QUANTITY_DECIMALS: Final = 3

# Dates: the API uses ISO formats; people see DD-MM-YYYY.
API_DATE_FORMAT: Final = "%Y-%m-%d"
DISPLAY_DATE_FORMAT: Final = "%d-%m-%Y"

DEFAULT_STORE_SLUG: Final = "main"

# Authentication
JWT_ALGORITHM: Final = "HS256"
TOKEN_TYPE: Final = "Bearer"
REFRESH_TOKEN_BYTES: Final = 48
RATE_LIMIT_WINDOW_SECONDS: Final = 60
DEVICE_NAME_MAX_LENGTH: Final = 100
DEVICE_TOKEN_MAX_LENGTH: Final = 255

# Indian mobile number: 10 digits starting 6-9.
PHONE_PATTERN: Final = r"^[6-9]\d{9}$"

DEFAULT_PER_PAGE: Final = 20
MAX_PER_PAGE: Final = 100

# String column lengths reused by models and request schemas.
NAME_MAX_LENGTH: Final = 120
EMAIL_MAX_LENGTH: Final = 191
PHONE_MAX_LENGTH: Final = 15
LOCALE_MAX_LENGTH: Final = 5
