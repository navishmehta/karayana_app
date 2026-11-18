from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field


def test_health_returns_ok_with_store_time(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["time"].endswith("+05:30")


def test_unknown_route_uses_uniform_error_shape(client: TestClient) -> None:
    response = client.get("/api/v1/nope")
    assert response.status_code == 404
    assert response.json() == {"message": "The requested item was not found.", "code": "NOT_FOUND"}
    assert response.headers["content-language"] == "en"


def test_errors_are_translated_to_punjabi(client: TestClient) -> None:
    response = client.get("/api/v1/nope", headers={"Accept-Language": "pa-IN,pa;q=0.9,en;q=0.5"})
    assert response.json()["message"] == "ਮੰਗੀ ਗਈ ਚੀਜ਼ ਨਹੀਂ ਮਿਲੀ।"
    assert response.headers["content-language"] == "pa"


def test_unsupported_language_falls_back_to_english(client: TestClient) -> None:
    response = client.get("/api/v1/nope", headers={"Accept-Language": "fr"})
    assert response.headers["content-language"] == "en"


def test_method_not_allowed(client: TestClient) -> None:
    response = client.post("/api/v1/health")
    assert response.status_code == 405
    assert response.json()["code"] == "METHOD_NOT_ALLOWED"


def _app_with_extra_routes(client: TestClient) -> TestClient:
    router = APIRouter()

    class Payload(BaseModel):
        name: str = Field(max_length=5)
        email: str

    @router.post("/echo")
    def echo(payload: Payload) -> Payload:
        return payload

    @router.get("/boom")
    def boom() -> None:
        raise RuntimeError("secret internal detail")

    client.app.include_router(router, prefix="/api/v1/test")
    return client


def test_validation_errors_are_per_field_and_translated(client: TestClient) -> None:
    client = _app_with_extra_routes(client)

    response = client.post("/api/v1/test/echo", json={"name": "toolongname"}, headers={"Accept-Language": "pa"})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_FAILED"
    assert body["errors"]["email"] == ["ਈਮੇਲ ਭਰਨਾ ਲਾਜ਼ਮੀ ਹੈ।"]
    assert body["errors"]["name"] == ["ਨਾਮ 5 ਅੱਖਰਾਂ ਤੋਂ ਲੰਬਾ ਨਹੀਂ ਹੋ ਸਕਦਾ।"]


def test_unhandled_errors_hide_internal_details(client: TestClient) -> None:
    client = _app_with_extra_routes(client)

    response = client.get("/api/v1/test/boom")

    assert response.status_code == 500
    assert response.json() == {"message": "Something went wrong. Please try again.", "code": "SERVER_ERROR"}
