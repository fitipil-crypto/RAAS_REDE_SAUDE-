"""
Serviço para gerenciamento de configurações.
"""
from sqlalchemy.orm import Session
from config.config_model import Configuracao
from config.config_schema import ConfiguracaoCriar, ConfiguracaoAtualizar


UF_IBGE = {
    "11": "Rondônia", "12": "Acre", "13": "Amazonas", "14": "Roraima",
    "15": "Pará", "16": "Amapá", "17": "Tocantins",
    "21": "Maranhão", "22": "Piauí", "23": "Ceará", "24": "Rio Grande do Norte",
    "25": "Paraíba", "26": "Pernambuco", "27": "Alagoas", "28": "Sergipe",
    "29": "Bahia", "31": "Minas Gerais", "32": "Espírito Santo",
    "33": "Rio de Janeiro", "35": "São Paulo",
    "41": "Paraná", "42": "Santa Catarina", "43": "Rio Grande do Sul",
    "50": "Mato Grosso do Sul", "51": "Mato Grosso", "52": "Goiás",
    "53": "Distrito Federal",
}

CONFIG_PADRAO = {
    "uf_code": ("35", "string", "Código UF (2 dígitos)", "estabelecimento"),
    "cnes_code": ("0000000", "string", "Código CNES (7 dígitos)", "estabelecimento"),
    "organ_name": ("CAPS MUNICIPAL", "string", "Nome do Órgão", "estabelecimento"),
    "organ_code": ("CAPS01", "string", "Sigla do Órgão", "estabelecimento"),
    "cnpj": ("", "string", "CNPJ (alfanumérico)", "estabelecimento"),
    "destination_organ": ("SECRETARIA MUNICIPAL DE SAUDE", "string", "Órgão de Destino", "estabelecimento"),
    "destination_indicator": ("M", "string", "Indicador de Destino (E=Estadual, M=Municipal)", "estabelecimento"),
    "versao": ("02.31", "string", "Versão do layout RAAS (ex: 02.31, 04.27)", "estabelecimento"),
    "bdversao": ("", "string", "Versão do BDSIA (vazio = competência + 'a')", "estabelecimento"),
    "default_city": ("", "string", "Cidade padrão para novos pacientes", "pacientes"),
    "default_state": ("", "string", "UF padrão para novos pacientes", "pacientes"),
    "default_municipality_code": ("", "string", "Código IBGE padrão para novos pacientes", "pacientes"),
}


class ConfigService:

    @staticmethod
    def inicializar_config_padrao(db: Session):
        """Cria configurações padrão se não existirem."""
        for chave, (valor, tipo, descricao, categoria) in CONFIG_PADRAO.items():
            existing = db.query(Configuracao).filter(Configuracao.chave == chave).first()
            if not existing:
                config = Configuracao(
                    chave=chave,
                    valor=valor,
                    tipo=tipo,
                    descricao=descricao,
                    categoria=categoria,
                    editavel=True,
                )
                db.add(config)
        db.commit()

    @staticmethod
    def listar_todas(db: Session) -> list[Configuracao]:
        return db.query(Configuracao).order_by(Configuracao.categoria, Configuracao.chave).all()

    @staticmethod
    def listar_por_categoria(db: Session, categoria: str) -> list[Configuracao]:
        return db.query(Configuracao).filter(Configuracao.categoria == categoria).all()

    @staticmethod
    def obter_por_chave(db: Session, chave: str) -> Configuracao | None:
        return db.query(Configuracao).filter(Configuracao.chave == chave).first()

    @staticmethod
    def obter_valor(db: Session, chave: str, default: str = None) -> str:
        config = ConfigService.obter_por_chave(db, chave)
        return config.valor if config else default

    @staticmethod
    def criar(db: Session, data: ConfiguracaoCriar) -> Configuracao:
        config = Configuracao(**data.model_dump())
        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def atualizar(db: Session, chave: str, data: ConfiguracaoAtualizar) -> Configuracao | None:
        config = ConfigService.obter_por_chave(db, chave)
        if not config:
            return None
        if data.valor is not None:
            config.valor = data.valor
        if data.descricao is not None:
            config.descricao = data.descricao
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def atualizar_varios(db: Session, valores: dict[str, str]) -> dict:
        """Atualiza várias configurações de uma vez."""
        result = {}
        for chave, valor in valores.items():
            config = ConfigService.obter_por_chave(db, chave)
            if config:
                config.valor = valor
                result[chave] = "atualizado"
            else:
                config = Configuracao(
                    chave=chave,
                    valor=valor,
                    tipo="string",
                    categoria="estabelecimento",
                    editavel=True,
                )
                db.add(config)
                result[chave] = "criado"
        db.commit()
        return result

    @staticmethod
    def deletar(db: Session, chave: str) -> bool:
        config = ConfigService.obter_por_chave(db, chave)
        if not config:
            return False
        db.delete(config)
        db.commit()
        return True

    @staticmethod
    def get_config_estabelecimento(db: Session) -> dict:
        """Retorna todas as configurações do estabelecimento como dict."""
        result = {}
        for chave, (valor_default, _, _, _) in CONFIG_PADRAO.items():
            result[chave] = ConfigService.obter_valor(db, chave, valor_default)
        return result
