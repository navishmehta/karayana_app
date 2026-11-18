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

# Catalogue
SKU_PREFIX: Final = "SK-"
SKU_PAD_LENGTH: Final = 6
MAX_PRICE: Final = 9_999_999.99  # fits DECIMAL(12,2)
MAX_QUANTITY: Final = 999_999.999  # fits DECIMAL(12,3)
MAX_SEARCH_LENGTH: Final = 100
PRODUCT_NAME_MAX_LENGTH: Final = 191
CODE_MAX_LENGTH: Final = 64  # SKU / barcode
DESCRIPTION_MAX_LENGTH: Final = 5000
NOTES_MAX_LENGTH: Final = 2000

# Inventory
IDEMPOTENCY_KEY_MAX_LENGTH: Final = 64
MAX_BATCHES_PER_WRITE_OFF: Final = 100
BATCH_NUMBER_MAX_LENGTH: Final = 64
EXPIRY_LOOKAHEAD_MAX_DAYS: Final = 365

# Images: uploads are re-encoded to WebP (also removes EXIF/GPS and anything hidden in the file).
MEDIA_URL_PATH: Final = "/media"
IMAGE_MAX_UPLOAD_BYTES: Final = 5 * 1024 * 1024
IMAGE_MAX_PIXELS: Final = 40_000_000  # decompression-bomb guard
IMAGE_ALLOWED_FORMATS: Final = frozenset({"JPEG", "PNG", "WEBP"})
IMAGE_FULL_WIDTH: Final = 1200
IMAGE_THUMB_WIDTH: Final = 400
IMAGE_WEBP_QUALITY: Final = 80
MAX_IMAGES_PER_PRODUCT: Final = 6

# Indian mobile number: 10 digits starting 6-9.
PHONE_PATTERN: Final = r"^[6-9]\d{9}$"

DEFAULT_PER_PAGE: Final = 20
MAX_PER_PAGE: Final = 100

# String column lengths reused by models and request schemas.
NAME_MAX_LENGTH: Final = 120
EMAIL_MAX_LENGTH: Final = 191
PHONE_MAX_LENGTH: Final = 15
LOCALE_MAX_LENGTH: Final = 5
