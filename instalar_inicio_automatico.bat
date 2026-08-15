@echo off
net session >nul 2>&1
if errorlevel 1 (
    echo Este instalador precisa ser executado como Administrador.
    echo Solicitando elevacao...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

setlocal
cd /d "%~dp0"

set "TASK_NAME=RAAS-CAPS"
set "SCRIPT_PATH=%~dp0iniciar_servidor.bat"

echo ==============================================
echo   RAAS-CAPS - Instalando inicio automatico
echo ==============================================

echo [1/3] Localizando o Python instalado...
if exist ".venv\Scripts\python.exe" goto :python_ok

for /f "delims=" %%p in ('where python 2^>nul') do (
    echo %%p> python_path.txt
    goto :python_ok
)

echo [ERRO] Python nao encontrado no PATH desta conta.
echo Rode iniciar_servidor.bat manualmente pelo menos uma vez
echo antes de instalar o inicio automatico.
pause
exit /b 1

:python_ok

echo [2/3] Registrando tarefa agendada (inicia com o Windows)...
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
schtasks /create /tn "%TASK_NAME%" /tr "\"%SCRIPT_PATH%\"" /sc onstart /ru SYSTEM /rl highest /f
if errorlevel 1 (
    echo [ERRO] Falha ao criar a tarefa agendada.
    pause
    exit /b 1
)

echo [3/3] Liberando a porta 8000 no Firewall do Windows...
netsh advfirewall firewall delete rule name="RAAS-CAPS" >nul 2>&1
netsh advfirewall firewall add rule name="RAAS-CAPS" dir=in action=allow protocol=TCP localport=8000 >nul

echo.
echo ==============================================
echo Concluido! O RAAS-CAPS vai iniciar sozinho toda
echo vez que este computador for ligado, mesmo sem
echo ninguem fazer login.
echo.
echo Para iniciar agora, sem reiniciar o PC, rode:
echo    iniciar_servidor.bat
echo.
echo Para desativar o inicio automatico, rode:
echo    desinstalar_inicio_automatico.bat
echo ==============================================
pause
