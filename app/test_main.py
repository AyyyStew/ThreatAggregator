from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


# Note I know these tests are not good tests, but they do show me what endpoints break when changes are made.
# Tests need to added to mock and verify data. For this pet project though, I do not care to.
def test_home_200():
    response = client.get("/")
    assert response.status_code == 200


def test_view_200():
    response = client.get("/view")
    assert response.status_code == 200


def test_download_200():
    response = client.get("/download")
    assert response.status_code == 200
