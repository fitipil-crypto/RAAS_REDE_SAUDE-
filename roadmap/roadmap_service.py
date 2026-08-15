"""
Serviço para gerenciamento do roadmap.
"""
from sqlalchemy.orm import Session
from roadmap.roadmap_model import RoadmapItem
from roadmap.roadmap_schema import RoadmapItemCriar, RoadmapItemAtualizar


class RoadmapService:

    @staticmethod
    def listar_todos(db: Session) -> list[RoadmapItem]:
        return db.query(RoadmapItem).order_by(RoadmapItem.order, RoadmapItem.created_at).all()

    @staticmethod
    def obter_por_id(db: Session, item_id: str) -> RoadmapItem | None:
        return db.query(RoadmapItem).filter(RoadmapItem.id == item_id).first()

    @staticmethod
    def criar(db: Session, data: RoadmapItemCriar) -> RoadmapItem:
        item = RoadmapItem(**data.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def atualizar(db: Session, item_id: str, data: RoadmapItemAtualizar) -> RoadmapItem | None:
        item = RoadmapService.obter_por_id(db, item_id)
        if not item:
            return None
        updates = data.model_dump(exclude_unset=True)
        for k, v in updates.items():
            setattr(item, k, v)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def deletar(db: Session, item_id: str) -> bool:
        item = RoadmapService.obter_por_id(db, item_id)
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True

    @staticmethod
    def toggle_done(db: Session, item_id: str) -> RoadmapItem | None:
        item = RoadmapService.obter_por_id(db, item_id)
        if not item:
            return None
        item.done = not item.done
        if item.done:
            item.status = "concluido"
        elif item.status == "concluido":
            item.status = "em_andamento"
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def inicializar_seeds(db: Session):
        """Popula o roadmap com itens iniciais se a tabela estiver vazia."""
        if db.query(RoadmapItem).count() > 0:
            return

        seeds = [
            {"title": "Exportação RAAS no formato SIA/SUS",
             "description": "Gerar arquivo de remessa no formato CNES/SIA compatível com o DATASUS para registros RAAS (Atenção Psicossocial).",
             "status": "em_andamento", "priority": "alta", "order": 1},
            {"title": "Geração de arquivo BPA Individualizado",
             "description": "Exportar BPA Individualizado (ABP AI) no layout oficial SIGTAP/DATASUS com campos obrigatórios e validações.",
             "status": "planejado", "priority": "alta", "order": 2},
            {"title": "Geração de arquivo BPA Consolidado",
             "description": "Exportar BPA Consolidado (ABP AC) agrupando produções ambulatoriais no layout oficial.",
             "status": "planejado", "priority": "alta", "order": 3},
            {"title": "Importação de procedimentos SIGTAP",
             "description": "Importar tabela de procedimentos SIGTAP (.txt/.dbf) para cadastro automático de procedimentos com códigos e nomes oficiais.",
             "status": "planejado", "priority": "media", "order": 4},
            {"title": "Validação de campos conforme manual SIA/SUS",
             "description": "Implementar validações de campos (CNS, CID, CBO, CNES) conforme regras do manual técnico do SIA/SUS.",
             "status": "em_andamento", "priority": "media", "order": 5},
            {"title": "Dashboard com indicadores CAPS",
             "description": "Dashboard com gráficos de produção mensal, perfil de usuários, procedimentos mais realizados e indicadores CAPS.",
             "status": "em_andamento", "priority": "media", "order": 6},
            {"title": "Relatórios de produtividade mensal",
             "description": "Relatórios detalhados de produtividade por profissional, procedimento e período, com exportação PDF/Excel.",
             "status": "planejado", "priority": "media", "order": 7},
            {"title": "Backup automático agendado",
             "description": "Backup automático do banco SQLite em intervalos configuráveis, com retenção e notificação por e-mail.",
             "status": "planejado", "priority": "baixa", "order": 8},
            {"title": "Controle de acesso por perfil",
             "description": "Refinar permissões: admin (total), operador (CRUD), visualizador (apenas leitura) em todos os módulos.",
             "status": "concluido", "priority": "media", "order": 9, "done": True},
            {"title": "Categorias de procedimentos conforme RAAS",
             "description": "Categorias oficiais (RAAS Atenção Psicossocial, BPA Individualizado, BPA Consolidado) com validação no schema e dropdown no frontend.",
             "status": "concluido", "priority": "alta", "order": 10, "done": True},
            {"title": "Integração Cloudflare Tunnel",
             "description": "Acesso seguro externo via Cloudflare Tunnel com túnel nomeado e token, integrado ao Docker Compose.",
             "status": "concluido", "priority": "media", "order": 11, "done": True},
            {"title": "Containerização Docker",
             "description": "Dockerfile e docker-compose.yml com SQLite, volumes de persistência e serviço cloudflared.",
             "status": "concluido", "priority": "alta", "order": 12, "done": True},
            {"title": "CNPJ alfanumérico",
             "description": "Suporte ao novo formato de CNPJ alfanumérico (14 caracteres) em validações, frontend e exportação.",
             "status": "concluido", "priority": "media", "order": 13, "done": True},
            {"title": "Migrações automáticas de banco de dados",
             "description": "Sistema de migrações automáticas (ALTER TABLE ADD COLUMN) ao adicionar novas colunas nos modelos.",
             "status": "concluido", "priority": "alta", "order": 14, "done": True},
        ]

        for s in seeds:
            item = RoadmapItem(**s)
            db.add(item)
        db.commit()
        print(f"[ROADMAP] {len(seeds)} itens iniciais criados")
