@echo off
net session >nul 2>&1
if errorlevel 1 (
    echo Solicitando elevacao...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo Removendo inicio automatico do RAAS-CAPS...
schtasks /delete /tn "RAAS-CAPS" /f
netsh advfirewall firewall delete rule name="RAAS-CAPS"

echo Concluido. O servidor nao vai mais iniciar sozinho com o Windows.
echo (Use parar_servidor.bat para encerrar um servidor que ja esteja rodando.)
pause
