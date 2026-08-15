"""
Testes de importação RAAS com múltiplos arquivos simultâneos (até 6).
"""


def _arquivo(nome: str, conteudo: bytes = b"linha qualquer sem registro valido\n"):
    return ("files", (nome, conteudo, "text/plain"))


def test_parse_exige_admin(client):
    resp = client.post("/api/importacao/parse", files=[_arquivo("a.txt")])
    assert resp.status_code == 401


def test_parse_aceita_multiplos_arquivos_e_agrega_resumo(auth_client):
    arquivos = [_arquivo("a.txt"), _arquivo("b.txt"), _arquivo("c.txt")]
    resp = auth_client.post("/api/importacao/parse", files=arquivos)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["arquivos"]) == 3
    assert [a["nome"] for a in data["arquivos"]] == ["a.txt", "b.txt", "c.txt"]
    assert data["resumo_geral"] == {
        "total_pacientes": 0, "total_procedimentos": 0,
        "total_profissionais": 0, "total_registros": 0,
    }


def test_parse_rejeita_mais_de_6_arquivos(auth_client):
    arquivos = [_arquivo(f"arq{i}.txt") for i in range(7)]
    resp = auth_client.post("/api/importacao/parse", files=arquivos)
    assert resp.status_code == 400


def test_parse_aceita_exatamente_6_arquivos(auth_client):
    arquivos = [_arquivo(f"arq{i}.txt") for i in range(6)]
    resp = auth_client.post("/api/importacao/parse", files=arquivos)
    assert resp.status_code == 200
    assert len(resp.json()["arquivos"]) == 6


def test_importar_multiplos_arquivos_agrega_stats(auth_client):
    arquivos = [_arquivo("a.txt"), _arquivo("b.txt")]
    resp = auth_client.post("/api/importacao/importar", files=arquivos)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["arquivos"]) == 2
    assert data["arquivos"][0]["nome"] == "a.txt"
    assert "stats" in data["arquivos"][0]
    assert data["stats_geral"] == {
        "pacientes_novos": 0, "pacientes_atualizados": 0, "profissionais_novos": 0,
        "procedimentos_novos": 0, "registros_novos": 0, "registros_ignorados": 0,
    }
