"""
Testes de autenticação e login.
"""


def test_login_page_get(client):
    """GET /login deve retornar a página de login."""
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "login" in resp.text.lower() or "Login" in resp.text


def test_login_sucesso(auth_client):
    """auth_client já faz login — verifica se a sessão está ativa."""
    resp = auth_client.get("/")
    assert resp.status_code == 200


def test_login_senha_errada(client):
    """Login com senha errada deve retornar 200 com mensagem de erro."""
    resp = client.post("/login", data={"username": "admin", "password": "wrong"})
    assert resp.status_code == 200
    assert "invál" in resp.text.lower() or "invalid" in resp.text.lower()


def test_login_inexistente(client):
    """Login com usuário inexistente."""
    resp = client.post("/login", data={"username": "ghost", "password": "ghost"})
    assert resp.status_code == 200
    assert "invál" in resp.text.lower() or "invalid" in resp.text.lower()


def test_logout(auth_client):
    """Logout deve redirecionar para /login."""
    resp = auth_client.get("/logout", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers.get("location", "")


def test_root_sem_login(client):
    """GET / sem sessão deve redirecionar para /login."""
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers.get("location", "")
