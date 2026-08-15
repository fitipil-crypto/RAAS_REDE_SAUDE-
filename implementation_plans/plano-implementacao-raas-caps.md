# Plano de Implementação — RAAS-CAPS

**Data:** 2026-02-04  
**Versão:** 1.0  
**Status:** Concluído

## Objetivo

Implementar o sistema RAAS-CAPS como aplicação FastAPI full-stack, convertendo o frontend React (JSX) para uma arquitetura server-side com Jinja2, seguindo o padrão modular do projeto Fluxi.

## Decisões Arquiteturais

1. **FastAPI + Jinja2** ao invés de React — renderização server-side, sem necessidade de build frontend
2. **SQLAlchemy + SQLite** — ORM com banco leve, fácil migração para PostgreSQL
3. **Session-based auth** — cookies de sessão com `itsdangerous`, senhas com bcrypt
4. **Padrão modular** — cada entidade (paciente, profissional, etc.) é um módulo independente com model, schema, service, router e frontend_router
5. **Pydantic v2** — validação de dados com schemas tipados

## Módulos Implementados

| Módulo | Model | Schema | Service | API Router | Frontend Router | Template |
|--------|-------|--------|---------|------------|-----------------|----------|
| usuario | ✓ | ✓ | ✓ | ✓ | ✓ | acesso.html |
| paciente | ✓ | ✓ | ✓ | ✓ | ✓ | pacientes.html |
| profissional | ✓ | ✓ | ✓ | ✓ | ✓ | profissionais.html |
| procedimento | ✓ | ✓ | ✓ | ✓ | ✓ | procedimentos.html |
| registro | ✓ | ✓ | ✓ | ✓ | ✓ | registros.html |
| config | ✓ | ✓ | ✓ | ✓ | ✓ | configuracoes.html |
| importacao | — | — | ✓ | ✓ | ✓ | importar.html |
| exportacao | — | — | ✓ | ✓ | ✓ | exportacao.html |
| relatorio | — | — | ✓ | ✓ | ✓ | relatorios.html |
| backup | — | — | ✓ | ✓ | ✓ | backup.html |

## Arquivos Criados

- `main.py` — App FastAPI com startup, login/logout e registro de routers
- `database.py` — SQLAlchemy engine, session e criar_tabelas
- `logging_config.py` — Configuração de logging
- `requirements.txt` — Dependências Python
- `.env.example` — Template de configuração
- 10 módulos com `__init__.py`, cada um com model/schema/service/router/frontend_router
- 12 templates Jinja2 (base, login, dashboard, pacientes, profissionais, procedimentos, registros, exportacao, relatorios, configuracoes, importar, backup, acesso)
- CSS global (`static/css/style.css`)
- 7 arquivos JS (`static/js/`)

## Impacto na Documentação

- `README.md` criado com visão geral, arquitetura e roadmap
- `implementation_plans/` criado com este plano
- `tasks/` criado com lista de tarefas
