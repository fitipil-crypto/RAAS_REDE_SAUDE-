"""
Testes do módulo de pacientes.
"""


def test_criar_paciente(auth_client):
    """POST /api/pacientes/ deve criar um paciente."""
    resp = auth_client.post("/api/pacientes/", json={
        "name": "João da Silva",
        "cns": "123456789012345",
        "gender": "M",
        "race": "01",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "João da Silva"
    assert data["cns"] == "123456789012345"


def test_listar_pacientes(auth_client):
    """GET /api/pacientes/ deve listar pacientes."""
    auth_client.post("/api/pacientes/", json={"name": "Maria Santos"})
    resp = auth_client.get("/api/pacientes/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any(p["name"] == "Maria Santos" for p in data)


def test_obter_paciente(auth_client):
    """GET /api/pacientes/{id} deve retornar um paciente específico."""
    create = auth_client.post("/api/pacientes/", json={"name": "Carlos Souza"})
    pid = create.json()["id"]
    resp = auth_client.get(f"/api/pacientes/{pid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Carlos Souza"


def test_obter_paciente_inexistente(auth_client):
    """GET /api/pacientes/{id} com ID inexistente deve retornar 404."""
    resp = auth_client.get("/api/pacientes/uuid-inexistente")
    assert resp.status_code == 404


def test_atualizar_paciente(auth_client):
    """PUT /api/pacientes/{id} deve atualizar o paciente."""
    create = auth_client.post("/api/pacientes/", json={"name": "Pedro Lima"})
    pid = create.json()["id"]
    resp = auth_client.put(f"/api/pacientes/{pid}", json={"name": "Pedro Lima Jr"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Pedro Lima Jr"


def test_deletar_paciente(auth_client):
    """DELETE /api/pacientes/{id} deve excluir o paciente."""
    create = auth_client.post("/api/pacientes/", json={"name": "Ana Costa"})
    pid = create.json()["id"]
    resp = auth_client.delete(f"/api/pacientes/{pid}")
    assert resp.status_code == 200
    resp = auth_client.get(f"/api/pacientes/{pid}")
    assert resp.status_code == 404


def test_criar_paciente_sem_auth(client):
    """POST /api/pacientes/ sem autenticação deve retornar 401."""
    resp = client.post("/api/pacientes/", json={"name": "Teste"})
    assert resp.status_code == 401


def test_cpf_invalido_rejeitado(auth_client):
    """CPF com dígito verificador inválido deve ser rejeitado."""
    resp = auth_client.post("/api/pacientes/", json={
        "name": "Teste CPF",
        "cpf": "11111111111",
    })
    assert resp.status_code == 422


def test_cpf_valido_aceito(auth_client):
    """CPF válido deve ser aceito."""
    resp = auth_client.post("/api/pacientes/", json={
        "name": "Teste CPF Válido",
        "cpf": "52998224725",
    })
    assert resp.status_code == 200
    assert resp.json()["cpf"] == "52998224725"


def test_buscar_municipios_sem_auth(client):
    resp = client.get("/api/pacientes/municipios/buscar?q=sao+paulo")
    assert resp.status_code == 401


def test_buscar_municipios_prioriza_prefixo(auth_client):
    resp = auth_client.get("/api/pacientes/municipios/buscar?q=sao+paulo")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["nome"] == "São Paulo"
    assert data[0]["uf"] == "SP"
    assert data[0]["codigo"] == "355030"


def test_buscar_municipios_filtra_por_uf(auth_client):
    resp = auth_client.get("/api/pacientes/municipios/buscar?q=sao+carlos&uf=SP")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert all(m["uf"] == "SP" for m in data)


def test_buscar_municipios_ignora_acento_e_caixa(auth_client):
    resp = auth_client.get("/api/pacientes/municipios/buscar?q=SAO CARLOS")
    assert resp.status_code == 200
    nomes = [m["nome"] for m in resp.json()]
    assert "São Carlos" in nomes


def test_buscar_municipios_query_curta_retorna_vazio(auth_client):
    resp = auth_client.get("/api/pacientes/municipios/buscar?q=s")
    assert resp.status_code == 422  # min_length=2


def test_resolver_municipio_por_codigo(auth_client):
    """Pacientes importados via RAAS têm municipality_code mas nunca tiveram
    city/state digitados; esse endpoint resolve o código pro nome/UF."""
    resp = auth_client.get("/api/pacientes/municipios/codigo/354140")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nome"] == "Presidente Prudente"
    assert data["uf"] == "SP"


def test_resolver_municipio_codigo_invalido(auth_client):
    resp = auth_client.get("/api/pacientes/municipios/codigo/000000")
    assert resp.status_code == 404


def test_resolver_municipio_sem_auth(client):
    resp = client.get("/api/pacientes/municipios/codigo/354140")
    assert resp.status_code == 401
