import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def fake_predict_image(bytes_io):
    return {"prediction":"normal","confidence":0.95}

@pytest.fixture(autouse=True)
def patch_predict(monkeypatch):
    from app.services import data_service
    monkeypatch.setattr(data_service, "predict_image", lambda f: {"prediction":"normal","confidence":0.99})

def test_upload_image_success(tmp_path):
    file_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 1000
    files = {"file": ("test.png", io.BytesIO(file_content), "image/png")}
    resp = client.post("/upload/image", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["prediction"]["prediction"] == "normal"
