@echo off
setlocal
cd /d "%~dp0"

set "PORT=%WORLD_CUP_DASHBOARD_PORT%"
if "%PORT%"=="" set "PORT=8501"

set "WINDOW_EXE=dist\WorldCupActionFlow\WorldCupActionFlow.exe"
set "CONSOLE_EXE=dist\WorldCupActionFlowConsole\WorldCupActionFlowConsole.exe"
set "WINDOW_PORT_FILE=dist\WorldCupActionFlow\_internal\dashboard_port.txt"
set "CONSOLE_PORT_FILE=dist\WorldCupActionFlowConsole\_internal\dashboard_port.txt"
set "ROOT_PORT_FILE=dashboard_port.txt"

call :launch_window_build
if not errorlevel 1 goto :open_browser

echo Falha ao iniciar pelo executavel de janela. Tentando modo de console...
call :launch_console_build
if not errorlevel 1 goto :open_browser

echo Falha ao iniciar pelos executaveis empacotados. Tentando launcher Python...
call :launch_python
if not errorlevel 1 goto :open_browser

echo Nao foi possivel iniciar o dashboard.
echo Verifique se as dependencias foram instaladas com: pip install -r requirements.txt
pause
exit /b 1

:launch_window_build
if not exist "%WINDOW_EXE%" exit /b 1
if exist "%WINDOW_PORT_FILE%" del "%WINDOW_PORT_FILE%" >nul 2>&1
start "" "%WINDOW_EXE%"
call :wait_for_server "%WINDOW_PORT_FILE%"
exit /b %errorlevel%

:launch_console_build
if not exist "%CONSOLE_EXE%" exit /b 1
if exist "%CONSOLE_PORT_FILE%" del "%CONSOLE_PORT_FILE%" >nul 2>&1
start "" "%CONSOLE_EXE%"
call :wait_for_server "%CONSOLE_PORT_FILE%"
exit /b %errorlevel%

:launch_python
where python >nul 2>&1
if not errorlevel 1 (
    if exist "%ROOT_PORT_FILE%" del "%ROOT_PORT_FILE%" >nul 2>&1
    start "" cmd /c python launcher_console.py
    call :wait_for_server "%ROOT_PORT_FILE%"
    exit /b %errorlevel%
)

where py >nul 2>&1
if not errorlevel 1 (
    if exist "%ROOT_PORT_FILE%" del "%ROOT_PORT_FILE%" >nul 2>&1
    start "" cmd /c py -3 launcher_console.py
    call :wait_for_server "%ROOT_PORT_FILE%"
    exit /b %errorlevel%
)

exit /b 1

:wait_for_server
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$portFile = '%~1';" ^
    "$basePort = [int]'%PORT%';" ^
    "$port = $basePort;" ^
    "$deadline = (Get-Date).AddSeconds(45);" ^
    "$scanAfter = (Get-Date).AddSeconds(10);" ^
    "while ((Get-Date) -lt $deadline) {" ^
    "  if ($portFile -and (Test-Path -LiteralPath $portFile)) {" ^
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
    "      if ($portFile) { Set-Content -LiteralPath $portFile -Value $port -Encoding ASCII -ErrorAction SilentlyContinue }" ^
    "      exit 0" ^
    "    }" ^
    "  } catch {}" ^
    "  Start-Sleep -Milliseconds 500" ^
    "}" ^
    "exit 1"
exit /b %errorlevel%

:open_browser
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$port = '%PORT%';" ^
    "$files = @('%WINDOW_PORT_FILE%', '%CONSOLE_PORT_FILE%', '%ROOT_PORT_FILE%');" ^
    "foreach ($file in $files) {" ^
    "  if (Test-Path -LiteralPath $file) {" ^
    "    $candidate = (Get-Content -LiteralPath $file -ErrorAction SilentlyContinue | Select-Object -First 1);" ^
    "    if ($candidate -match '^\d+$') { $port = $candidate; break }" ^
    "  }" ^
    "}" ^
    "Start-Process ('http://127.0.0.1:' + $port)"
exit /b 0
