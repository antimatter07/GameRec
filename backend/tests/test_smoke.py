def test_app_importable():
    from app.main import app
    assert app is not None


def test_routers_registered():
    from app.main import app
    routes = [r.path for r in app.routes]
    assert any("/api" in r for r in routes)
