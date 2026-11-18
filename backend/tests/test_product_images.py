from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import IMAGE_FULL_WIDTH, IMAGE_THUMB_WIDTH, MAX_IMAGES_PER_PRODUCT
from app.enums.permission import Permission
from app.models import ProductImage
from tests.helpers import admin_headers, create_seller, image_bytes, make_product, seller_headers


def _upload(client: TestClient, product_id: int, headers: dict, content: bytes | None = None):
    files = {"image": ("photo.jpg", content if content is not None else image_bytes(), "image/jpeg")}
    return client.post(f"/api/v1/products/{product_id}/images", files=files, headers=headers)


def _stored(path: str) -> Image.Image:
    return Image.open(Path(get_settings().media_root) / path)


def test_first_image_is_main_and_files_are_resized_webp(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client)

    images = _upload(client, product.id, headers).json()["data"]["images"]
    assert images[0]["is_primary"] is True
    images = _upload(client, product.id, headers).json()["data"]["images"]
    assert [i["is_primary"] for i in images] == [True, False]

    image = seeded_db.get(ProductImage, images[0]["id"])
    full, thumb = _stored(image.path), _stored(image.thumb_path)
    assert full.format == "WEBP" and full.width == IMAGE_FULL_WIDTH
    assert thumb.width == IMAGE_THUMB_WIDTH
    assert "exif" not in full.info


def test_image_limit(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client)
    for _ in range(MAX_IMAGES_PER_PRODUCT):
        assert _upload(client, product.id, headers, image_bytes(300, 300)).status_code == 201
    response = _upload(client, product.id, headers, image_bytes(300, 300))
    assert response.status_code == 422
    assert response.json()["code"] == "IMAGE_LIMIT_REACHED"


def test_make_main_and_delete_promotes_next(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client)
    first = _upload(client, product.id, headers).json()["data"]["images"][0]["id"]
    second = _upload(client, product.id, headers).json()["data"]["images"][1]["id"]

    images = client.patch(f"/api/v1/products/{product.id}/images/{second}", json={"is_primary": True}, headers=headers)
    assert images.json()["data"]["images"][0]["id"] == second

    path = seeded_db.get(ProductImage, second).path
    assert client.delete(f"/api/v1/products/{product.id}/images/{second}", headers=headers).status_code == 204
    seeded_db.expire_all()
    assert seeded_db.get(ProductImage, first).is_primary is True
    assert not (Path(get_settings().media_root) / path).exists()


def test_image_of_another_product_cannot_be_reached(client: TestClient, seeded_db: Session) -> None:
    mine, other = make_product(seeded_db), make_product(seeded_db)
    headers = admin_headers(client)
    foreign_id = _upload(client, other.id, headers).json()["data"]["images"][0]["id"]
    assert client.delete(f"/api/v1/products/{mine.id}/images/{foreign_id}", headers=headers).status_code == 404


def test_fake_or_unsupported_images_are_rejected(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client)
    assert _upload(client, product.id, headers, b"<?php echo 'hi'; ?>").json()["code"] == "INVALID_IMAGE"

    gif = BytesIO()
    Image.new("RGB", (10, 10)).save(gif, format="GIF")
    assert _upload(client, product.id, headers, gif.getvalue()).json()["code"] == "INVALID_IMAGE"


def test_upload_needs_edit_permission(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = seller_headers(client, create_seller(seeded_db, [Permission.PRODUCTS_VIEW]))
    assert _upload(client, product.id, headers).status_code == 403
