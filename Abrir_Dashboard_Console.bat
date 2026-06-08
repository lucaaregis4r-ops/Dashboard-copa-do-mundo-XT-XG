@echo off
setlocal
cd /d "%~dp0"
set "PORT_FILE=dist\WorldCupActionFlowConsole\_internal\dashboard_port.txt"
if exist "%PORT_FILE%" del "%PORT_FILE%" >nul 2>&1

if exist "dist\WorldCupActionFlowConsole\WorldCupActionFlowConsole_fixed.exe" (
    start "" "dist\WorldCupActionFlowConsole\WorldCupActionFlowConsole_fixed.exe"
    call :open_when_ready
    exit /b %errorlevel%
)

if exist "dist\WorldCupActionFlowConsole\WorldCupActionFlowConsole_prod.exe" (
    start "" "dist\WorldCupActionFlowConsole\WorldCupActionFlowConsole_prod.exe"
    call :open_when_ready
    exit /b %errorlevel%
)

if exist "dist\WorldCupActionFlowConsole\WorldCupActionFlowConsole.exe" (
    start "" "dist\WorldCupActionFlowConsole\WorldCupActionFlowConsole.exe"
    call :open_when_ready
    exit /b %errorlevel%
)

echo Executavel de console nao encontrado em dist\WorldCupActionFlowConsole\WorldCupActionFlowConsole.exe
echo Rode primeiro: python build_exe.py
pause
exit /b 1

:open_when_ready
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$basePort = 8501;" ^
    "$port = $basePort;" ^
    "$portFile = '%PORT_FILE%';" ^
    "$deadline = (Get-Date).AddSeconds(45);" ^
    "$scanAfter = (Get-Date).AddSeconds(10);" ^
    "while ((Get-Date) -lt $deadline) {" ^
    "  if (Test-Path -LiteralPath $portFile) {" ^
    "    $candidate = (Get-Content -LiteralPath $portFile -ErrorAction SilentlyContinue | Select-Object -First 1);" ^
    "    if ($candidate -match '^\d+$') { $port = $candidate }" ^
    "  } else {" ^
    "    if ((Get-Date) -lt $scanAfter) { Start-Sleep -Milliseconds 500; continue }" ^
    "    $readyPorts = @();" ^
    "    for ($candidatePort = $basePort; $candidatePort -lt ($basePort + 25); $candidatePort++) {" ^
    "      try {" ^
    "        $resp = Invoke-WebRequest -UseBasicParsing -Uri ('http://127.0.0.1:' + $candidatePort + '/_stcore/health') -TimeoutSec 1;" ^
    "        if ($resp.StatusCode -eq 200) { $readyPorts += $candidatePort }" ^
    "      } catch {}" ^
    "    }" ^
    "    if ($readyPorts.Count -gt 0) { $port = ($readyPorts | Sort-Object -Descending | Select-Object -First 1) }" ^
    "  }" ^
    "  try {" ^
    "    $resp = Invoke-WebRequest -UseBasicParsing -Uri ('http://127.0.0.1:' + $port + '/_stcore/health') -TimeoutSec 2;" ^
    "    if ($resp.StatusCode -eq 200) {" ^
    "      Set-Content -LiteralPath $portFile -Value $port -Encoding ASCII -ErrorAction SilentlyContinue;" ^
    "      Start-Process ('http://127.0.0.1:' + $port);" ^
    "      exit 0" ^
    "    }" ^
    "  } catch {}" ^
    "  Start-Sleep -Milliseconds 500" ^
    "}" ^
    "exit 1"
exit /b %errorlevel%
