@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

if not exist "logs" mkdir logs
set "BOOTLOG=logs\boot.log"
echo [%date% %time%] iniciar_servidor.bat iniciado >> "%BOOTLOG%"

echo ==============================================
echo   RAAS-CAPS - Iniciando servidor
echo ==============================================

if exist ".venv\Scripts\python.exe" goto :venv_pronto

rem Ambiente virtual ainda nao existe: precisamos de um "python" utilizavel
rem para cria-lo. A conta SYSTEM (usada pela tarefa de inicio automatico)
rem nao enxerga o PATH do usuario, entao tentamos primeiro o caminho
rem absoluto salvo por instalar_inicio_automatico.bat.
echo [%date% %time%] .venv nao existe, procurando python para cria-lo >> "%BOOTLOG%"
set "PYTHON_BOOTSTRAP=python"
if exist "python_path.txt" set /p PYTHON_BOOTSTRAP=<python_path.txt

"%PYTHON_BOOTSTRAP%" --version >nul 2>&1
if errorlevel 1 (
    echo [%date% %time%] ERRO: python nao encontrado ^(tentativa: %PYTHON_BOOTSTRAP%^) >> "%BOOTLOG%"
    echo [ERRO] Python nao foi encontrado.
    echo Instale o Python em https://python.org e marque a opcao
    echo "Add python.exe to PATH" durante a instalacao, depois rode
    echo este script uma vez manualmente antes de instalar o inicio
    echo automatico.
    pause
    exit /b 1
)

echo [1/4] Criando ambiente virtual...
"%PYTHON_BOOTSTRAP%" -m venv .venv
if errorlevel 1 (
    echo [%date% %time%] ERRO: falha ao criar o ambiente virtual >> "%BOOTLOG%"
    echo [ERRO] Falha ao criar o ambiente virtual. Veja logs\boot.log
    pause
    exit /b 1
)
echo [%date% %time%] ambiente virtual criado com sucesso >> "%BOOTLOG%"

:venv_pronto
set "PY=.venv\Scripts\python.exe"

echo [2/4] Verificando dependencias...
"%PY%" -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo [%date% %time%] AVISO: pip install terminou com erro >> "%BOOTLOG%"
) else (
    echo [%date% %time%] dependencias ok >> "%BOOTLOG%"
)

if not exist "secret.key" (
    echo [3/4] Gerando chave de seguranca...
    "%PY%" -c "import secrets;print(secrets.token_hex(32))" > secret.key
)
set /p SECRET_KEY=<secret.key

set "DATABASE_URL=sqlite:///./raas_caps.db"
set "DEBUG=false"

for /f "tokens=4" %%i in ('route print ^| find " 0.0.0.0"') do set LOCAL_IP=%%i

echo [4/4] Servidor iniciando em:
echo    - Neste computador: http://localhost:8000
if defined LOCAL_IP echo    - Na rede local:      http://%LOCAL_IP%:8000
echo.
echo Os logs ficam em logs\server.log ^(e logs\boot.log para diagnostico^)
echo Pressione Ctrl+C para parar.
echo ==============================================

echo [%date% %time%] chamando python main.py >> "%BOOTLOG%"
"%PY%" main.py >> "logs\server.log" 2>&1
echo [%date% %time%] python main.py encerrou (codigo %errorlevel%) >> "%BOOTLOG%"
