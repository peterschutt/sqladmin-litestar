from typing import Generator

import pytest
from litestar import Litestar, Request, Response
from litestar.response import Redirect
from litestar.testing import TestClient

from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from tests.common import sync_engine as engine


class CustomBackend(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        if form["username"] != "a":
            return False

        request.session.update({"token": "amin"})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        request.cookies.clear()
        return True

    async def authenticate(self, request: Request) -> bool | Response:
        if "token" in request.session:
            return Redirect(request.url_for("admin:login"), status_code=302)
        return False


app = Litestar()
authentication_backend = CustomBackend(secret_key="1234567891234561")
admin = Admin(app=app, engine=engine, authentication_backend=authentication_backend)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app=app, base_url="http://testserver") as c:
        yield c


def test_access_logion_required_views(client: TestClient) -> None:
    response = client.get("/admin/")
    assert response.url == "http://testserver/admin/login"

    response = client.get("/admin/users/list")
    assert response.url == "http://testserver/admin/login"


def test_login_failure(client: TestClient) -> None:
    response = client.post("/admin/login", data={"username": "x", "password": "b"})

    assert response.status_code == 400
    assert response.url == "http://testserver/admin/login"


def test_login(client: TestClient) -> None:
    response = client.post("/admin/login", data={"username": "a", "password": "b"})

    assert len(response.cookies) == 1
    assert response.status_code == 200


def test_logout(client: TestClient) -> None:
    response = client.get("/admin/logout")

    assert len(response.cookies) == 0
    assert response.status_code == 200
    assert response.url == "http://testserver/admin/login"
