"""
Testes do middleware de rate limiting.
"""


def test_login_rate_limit(client):
    """5 tentativas de login erradas devem bloquear a 6ª."""
    for i in range(5):
        resp = client.post("/login", data={"username": "admin", "password": "wrong"})
        assert resp.status_code == 200

    resp = client.post("/login", data={"username": "admin", "password": "wrong"})
    assert resp.status_code == 429
    assert "Muitas tentativas" in resp.text


def test_api_rate_limit(auth_client):
    """60 requisições GET /api/pacientes devem funcionar; a 61ª deve bloquear."""
    for i in range(60):
        resp = auth_client.get("/api/pacientes/")
        assert resp.status_code == 200

    resp = auth_client.get("/api/pacientes/")
    assert resp.status_code == 429


def test_rate_limit_nao_afeta_get_login(client):
    """GET /login não deve ser rate limited (apenas POST)."""
    for i in range(10):
        resp = client.get("/login")
        assert resp.status_code == 200
