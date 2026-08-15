# RAAS-CAPS — Sistema de Gestão de Atendimentos Psicossociais

Sistema full-stack para gestão de RAAS (Relatório de Atividades Ambulatoriais) do CAPS (Centro de Atenção Psicossocial), baseado na arquitetura modular do projeto Fluxi.

## Tecnologias

- **Backend:** FastAPI, SQLAlchemy, SQLite
- **Frontend:** Jinja2, HTML5, CSS3, JavaScript ES6+
- **Auth:** Session-based com bcrypt (passlib)
- **Validação:** Pydantic v2

## Arquitetura

```
saude_raas/
├── main.py                      # FastAPI app + rotas principais
├── database.py                  # SQLAlchemy setup
├── logging_config.py            # Configuração de logging
├── requirements.txt             # Dependências
├── .env.example                 # Template de configuração
├── usuario/                     # Módulo de usuários e auth
├── paciente/                    # Módulo de pacientes
├── profissional/                # Módulo de profissionais
├── procedimento/                # Módulo de procedimentos
├── registro/                    # Módulo de registros RAAS
├── config/                      # Módulo de configurações
├── importacao/                  # Importação de arquivos RAAS
├── exportacao/                  # Exportação DATASUS/CSV
├── relatorio/                   # Relatórios e estatísticas
├── backup/                      # Backup e restauração
├── templates/                   # Templates Jinja2
│   ├── base.html               # Layout base com sidebar
│   ├── login.html              # Tela de login
│   ├── dashboard.html          # Dashboard
│   ├── pacientes.html          # Gestão de pacientes
│   ├── profissionais.html      # Gestão de profissionais
│   ├── procedimentos.html      # Gestão de procedimentos
│   ├── registros.html          # Registros RAAS
│   ├── exportacao.html         # Exportação
│   ├── relatorios.html         # Relatórios
│   ├── configuracoes.html      # Configurações
│   ├── importar.html           # Importação RAAS
│   ├── backup.html             # Backup
│   └── acesso.html             # Controle de acesso
├── static/
│   ├── css/style.css           # Estilos globais
│   └── js/                     # Scripts por página
└── raas-caps.jsx.V04.27.fev2026.jsx  # Original React (referência)
```

## Padrão de Módulo

Cada módulo segue a arquitetura:
- `__init__.py` — Inicialização
- `model.py` — Modelo SQLAlchemy
- `schema.py` — Schemas Pydantic
- `service.py` — Lógica de negócio
- `router.py` — API REST (`/api/...`)
- `frontend_router.py` — Rotas de página (`/pagina`)

## Funcionalidades

- **Dashboard:** Visão geral com estatísticas
- **Pacientes:** CRUD completo com tabs (Identificação, Endereço, Clínico/Social)
- **Profissionais:** CRUD com busca e ativação/desativação
- **Procedimentos:** CRUD com códigos SIGTAP
- **Registros RAAS:** Atendimentos por competência mensal
- **Exportação:** Arquivo DATASUS (Reg 01/15/16) e CSV
- **Importação:** Parse e importação de arquivos RAAS com preview
- **Relatórios:** Top profissionais, procedimentos e atendimentos mensais
- **Configurações:** Dados do estabelecimento para exportação
- **Backup:** Exportar/importar todos os dados em JSON
- **Controle de Acesso:** Usuários com roles (admin, operador, visualizador)

## Instalação

```bash
# Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env

# Executar
python main.py
# ou
uvicorn main:app --reload --port 8000
```

## Rodando como servidor na rede local (Windows)

Para deixar o RAAS-CAPS disponível para outros computadores da rede do
trabalho, sem precisar abrir terminal nem digitar comandos:

1. Copie a pasta do projeto para o computador que vai ser o servidor (ex:
   `C:\RAAS-CAPS`). É preciso ter o [Python](https://python.org) instalado
   nesse computador (marque "Add python.exe to PATH" na instalação).
2. Dê **dois cliques em `iniciar_servidor.bat`** para testar — na primeira
   vez ele cria o ambiente virtual, instala as dependências e mostra o
   endereço de rede (`http://SEU-IP:8000`) para acessar de outros PCs.
3. Para o servidor iniciar sozinho toda vez que o computador ligar (mesmo
   sem login), clique com o botão direito em `instalar_inicio_automatico.bat`
   e escolha **"Executar como administrador"**. Isso também libera a porta
   8000 no Firewall do Windows para acesso pela rede.

Scripts disponíveis:
- `iniciar_servidor.bat` — inicia o servidor manualmente.
- `instalar_inicio_automatico.bat` — registra o início automático com o Windows.
- `desinstalar_inicio_automatico.bat` — remove o início automático.
- `parar_servidor.bat` — encerra o servidor em execução.

Os logs ficam em `logs\server.log` (saída da aplicação) e `logs\boot.log`
(registro de cada etapa da inicialização — use este para diagnosticar caso
o início automático não suba o servidor). A chave de segurança da aplicação
é gerada uma única vez em `secret.key` (não compartilhe esse arquivo).

**Se o início automático não funcionar:** abra o Agendador de Tarefas
(`taskschd.msc`), clique com o botão direito na tarefa `RAAS-CAPS` e escolha
"Executar" — isso simula o início automático sem precisar reiniciar o PC.
Depois confira `logs\boot.log` para ver em qual etapa parou.

## Credenciais Padrão

- Usuário: `admin`
- Senha: `admin`

## Roadmap

- [x] Análise do JSX original
- [x] Estrutura de diretórios e arquivos base
- [x] Módulo de usuários e autenticação
- [x] Módulo de pacientes
- [x] Módulo de profissionais
- [x] Módulo de procedimentos
- [x] Módulo de registros RAAS
- [x] Módulo de configurações
- [x] Módulo de importação RAAS
- [x] Módulo de exportação RAAS
- [x] Módulo de relatórios
- [x] Módulo de backup
- [x] Templates Jinja2
- [x] CSS e JavaScript
- [ ] Testes automatizados
- [ ] Excluir dados em lote (frontend)
- [ ] Validações avançadas de CNS/CPF
