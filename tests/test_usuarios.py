"""
Testes do módulo de usuários.
"""


def test_listar_usuarios(auth_client):
    """GET /api/usuarios/ deve listar usuários."""
    resp = auth_client.get("/api/usuarios/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any(u["username"] == "admin" for u in data)


def test_criar_usuario(auth_client):
    """POST /api/usuarios/ deve criar um usuário."""
    resp = auth_client.post("/api/usuarios/", json={
        "username": "operador1",
        "name": "Operador Teste",
        "role": "operador",
        "password": "senha123",
        "active": True,
    })
    assert resp.status_code == 200
    assert resp.json()["username"] == "operador1"


def test_criar_usuario_duplicado(auth_client):
    """POST /api/usuarios/ com username duplicado deve retornar 400."""
    auth_client.post("/api/usuarios/", json={
        "username": "dupuser",
        "name": "User 1",
        "role": "operador",
        "password": "senha123",
        "active": True,
    })
    resp = auth_client.post("/api/usuarios/", json={
        "username": "dupuser",
        "name": "User 2",
        "role": "operador",
        "password": "senha456",
        "active": True,
    })
    assert resp.status_code == 400


def test_deletar_usuario(auth_client):
    """DELETE /api/usuarios/{id} deve excluir usuário."""
    create = auth_client.post("/api/usuarios/", json={
        "username": "tempuser",
        "name": "Temp",
        "role": "coordenador",
        "password": "temp123",
        "active": True,
    })
    uid = create.json()["id"]
    resp = auth_client.delete(f"/api/usuarios/{uid}")
    assert resp.status_code == 200


def test_nao_deletar_proprio_usuario(auth_client):
    """DELETE do próprio usuário deve retornar 400."""
    users = auth_client.get("/api/usuarios/").json()
    admin_id = next(u["id"] for u in users if u["username"] == "admin")
    resp = auth_client.delete(f"/api/usuarios/{admin_id}")
    assert resp.status_code == 400


def test_alterar_senha(auth_client):
    """POST /api/usuarios/{id}/senha deve alterar a senha."""
    users = auth_client.get("/api/usuarios/").json()
    admin_id = next(u["id"] for u in users if u["username"] == "admin")
    resp = auth_client.post(f"/api/usuarios/{admin_id}/senha", json={
        "current_password": "admin",
        "new_password": "nova123",
        "confirm_password": "nova123",
    })
    assert resp.status_code == 200


def test_alterar_senha_errada(auth_client):
    """POST /api/usuarios/{id}/senha com senha atual errada deve retornar 400."""
    users = auth_client.get("/api/usuarios/").json()
    admin_id = next(u["id"] for u in users if u["username"] == "admin")
    resp = auth_client.post(f"/api/usuarios/{admin_id}/senha", json={
        "current_password": "errada",
        "new_password": "nova123",
        "confirm_password": "nova123",
    })
    assert resp.status_code == 400
