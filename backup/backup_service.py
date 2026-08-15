"""
Serviço para backup e restauração.
"""
import json
from sqlalchemy.orm import Session

from paciente.paciente_service import PacienteService
from paciente.paciente_schema import PacienteCriar
from profissional.profissional_service import ProfissionalService
from profissional.profissional_schema import ProfissionalCriar
from procedimento.procedimento_service import ProcedimentoService
from procedimento.procedimento_schema import ProcedimentoCriar
from registro.registro_service import RegistroService
from registro.registro_schema import RegistroCriar
from config.config_service import ConfigService


class BackupService:

    @staticmethod
    def criar_backup(db: Session) -> dict:
        """Gera um dict com todos os dados do sistema para backup."""
        config = ConfigService.get_config_estabelecimento(db)

        pacientes = PacienteService.listar_todos(db)
        profissionais = ProfissionalService.listar_todos(db)
        procedimentos = ProcedimentoService.listar_todos(db)
        registros = RegistroService.listar_todos(db)

        return {
            "version": "4.27",
            "created_at": __import__("datetime").datetime.now().isoformat(),
            "config": config,
            "patients": [
                {c.name: getattr(p, c.name) for c in p.__table__.columns}
                for p in pacientes
            ],
            "professionals": [
                {c.name: getattr(p, c.name) for c in p.__table__.columns}
                for p in profissionais
            ],
            "procedures": [
                {c.name: getattr(p, c.name) for c in p.__table__.columns}
                for p in procedimentos
            ],
            "records": [
                {c.name: getattr(r, c.name) for c in r.__table__.columns}
                for r in registros
            ],
        }

    @staticmethod
    def restaurar_backup(db: Session, data: dict) -> dict:
        """Restaura dados a partir de um backup."""
        log = []

        # Limpar dados existentes
        PacienteService.deletar_todos(db)
        ProfissionalService.deletar_todos(db)
        ProcedimentoService.deletar_todos(db)
        RegistroService.deletar_todos(db)
        log.append("Dados existentes limpos")

        # Restaurar configurações
        if "config" in data:
            ConfigService.atualizar_varios(db, data["config"])
            log.append("Configurações restauradas")

        # Restaurar pacientes
        id_map_pat = {}
        for p in data.get("patients", []):
            old_id = p.pop("id", None)
            p.pop("created_at", None)
            p.pop("updated_at", None)
            pac = PacienteService.criar(db, PacienteCriar(**{
                k: v for k, v in p.items() if v is not None
            }))
            if old_id:
                id_map_pat[old_id] = pac.id
        log.append(f"{len(id_map_pat)} pacientes restaurados")

        # Restaurar profissionais
        id_map_prof = {}
        for p in data.get("professionals", []):
            old_id = p.pop("id", None)
            p.pop("created_at", None)
            p.pop("updated_at", None)
            prof = ProfissionalService.criar(db, ProfissionalCriar(**{
                k: v for k, v in p.items() if v is not None
            }))
            if old_id:
                id_map_prof[old_id] = prof.id
        log.append(f"{len(id_map_prof)} profissionais restaurados")

        # Restaurar procedimentos
        id_map_proc = {}
        for p in data.get("procedures", []):
            old_id = p.pop("id", None)
            p.pop("created_at", None)
            p.pop("updated_at", None)
            proc = ProcedimentoService.criar(db, ProcedimentoCriar(**{
                k: v for k, v in p.items() if v is not None
            }))
            if old_id:
                id_map_proc[old_id] = proc.id
        log.append(f"{len(id_map_proc)} procedimentos restaurados")

        # Restaurar registros
        cnt_reg = 0
        for r in data.get("records", []):
            r.pop("id", None)
            r.pop("created_at", None)
            r.pop("updated_at", None)
            r["patient_id"] = id_map_pat.get(r["patient_id"], r["patient_id"])
            if r.get("professional_id"):
                r["professional_id"] = id_map_prof.get(r["professional_id"], r["professional_id"])
            r["procedure_id"] = id_map_proc.get(r["procedure_id"], r["procedure_id"])
            try:
                RegistroService.criar(db, RegistroCriar(**{
                    k: v for k, v in r.items() if v is not None
                }))
                cnt_reg += 1
            except Exception:
                pass
        log.append(f"{cnt_reg} registros RAAS restaurados")

        return {"log": log, "success": True}
