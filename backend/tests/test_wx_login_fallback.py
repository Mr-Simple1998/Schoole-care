from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_wx_login_fallback_uses_stable_device_id():
    auth = (ROOT / "app" / "routers" / "auth.py").read_text(encoding="utf-8")
    store = (ROOT.parent / "weapp" / "src" / "stores" / "user.js").read_text(encoding="utf-8")
    openid = (ROOT.parent / "weapp" / "src" / "utils" / "openid.js").read_text(encoding="utf-8")
    assert "export function getWxDeviceId()" in openid
    assert "device_id: getWxDeviceId()" in store
    assert "device_id: str | None = None" in auth
    assert "def _wx_openid(code: str, device_id: str | None = None)" in auth
    assert "return device_id or code" in auth
