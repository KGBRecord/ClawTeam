@echo off
setlocal EnableDelayedExpansion

:: ─── Colors and Tags ──────────────────────────────────────────────────────
set "GREEN=[OK]   "
set "YELLOW=[WARN] "
set "CYAN=[INFO] "
set "RED=[FAIL] "

set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%.."

echo.
echo   ==========================================
echo     ClawTeam-OpenClaw — Quick Setup (Win)
echo   ==========================================
echo.

:: ─── 1. Check Python ────────────────────────────────────────────────────
echo %CYAN% Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED% Python not found. Please install Python 3.10+ from Windows Store or python.org.
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo %GREEN% Python %PY_VER%

:: ─── 2. Check tmux ──────────────────────────────────────────────────────
echo %CYAN% Checking tmux...
tmux -V >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW% tmux not found. Windows users typically run 'subprocess' backend instead of tmux.
) else (
    echo %GREEN% tmux found.
)

:: ─── 3. Check Node.js & npx ────────────────────────────────────────────
echo %CYAN% Checking Node.js ^& npx...
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW% Node.js not found. Attempting to install via winget...
    winget install OpenJS.NodeJS.LTS -e --silent
    if !errorlevel! neq 0 (
        echo %RED% Failed to install Node.js automatically. Please manually install from nodejs.org for BMAD features.
    ) else (
        echo %GREEN% Node.js installed via winget. Please restart your terminal after this setup finishes.
    )
) else (
    for /f "tokens=*" %%a in ('node -v') do set NODE_VER=%%a
    echo %GREEN% Node.js !NODE_VER! ready
)

:: ─── 4. Create venv ─────────────────────────────────────────────────────
echo %CYAN% Setting up virtual environment...
if not exist "%REPO_ROOT%\.venv" (
    python -m venv "%REPO_ROOT%\.venv"
    echo %GREEN% Created .venv
) else (
    echo %GREEN% .venv already exists
)
call "%REPO_ROOT%\.venv\Scripts\activate.bat"
echo %GREEN% Activated .venv

:: ─── 5. Install ClawTeam ────────────────────────────────────────────────
echo %CYAN% Installing ClawTeam (editable)...
pip install -e "%REPO_ROOT%" --quiet
echo %GREEN% ClawTeam installed

:: ─── 6. ClawTeam config ─────────────────────────────────────────────────
echo %CYAN% Setting up ClawTeam config...
set "CLAWTEAM_DIR=%USERPROFILE%\.clawteam"
if not exist "%CLAWTEAM_DIR%" mkdir "%CLAWTEAM_DIR%"

if not exist "%CLAWTEAM_DIR%\config.json" (
    copy /Y "%REPO_ROOT%\docs\sample-config.json" "%CLAWTEAM_DIR%\config.json" >nul
    echo %GREEN% Config created at %CLAWTEAM_DIR%\config.json
) else (
    echo %GREEN% Config already exists at ~/.clawteam/config.json
)

:: ─── 6b. BMAD Bridge config ─────────────────────────────────────────────
echo %CYAN% Setting up BMAD Bridge config...
if not exist "%REPO_ROOT%\config.json" (
    copy /Y "%REPO_ROOT%\config.example.json" "%REPO_ROOT%\config.json" >nul
    echo %YELLOW% BMAD Bridge config created at root config.json. PLEASE UPDATE IT WITH YOUR API KEYS.
) else (
    echo %GREEN% BMAD Bridge config already exists at root config.json
)

:: ─── 7. OpenClaw skill ──────────────────────────────────────────────────
echo %CYAN% Setting up OpenClaw skill...
set "OC_SKILL_DIR=%USERPROFILE%\.openclaw\workspace\skills\clawteam"
set "OC_SKILL_SRC=%REPO_ROOT%\skills\openclaw\SKILL.md"

if exist "%OC_SKILL_SRC%" (
    if not exist "%OC_SKILL_DIR%" mkdir "%OC_SKILL_DIR%"
    copy /Y "%OC_SKILL_SRC%" "%OC_SKILL_DIR%\SKILL.md" >nul
    echo %GREEN% OpenClaw skill installed at %OC_SKILL_DIR%
) else (
    echo %YELLOW% OpenClaw skill source not found
)

:: ─── 8. OpenClaw exec-approvals ─────────────────────────────────────────
echo %CYAN% Configuring OpenClaw exec approvals...
set "APPROVALS=%USERPROFILE%\.openclaw\exec-approvals.json"
if exist "%APPROVALS%" (
    :: Inline Python to update JSON file securely
    python -c "import json, sys; f=sys.argv[1]; d=json.load(open(f)); d.setdefault('defaults',{})['security']='allowlist'; json.dump(d,open(f,'w'),indent=2)" "%APPROVALS%" 2>nul
    if !errorlevel! equ 0 (
        echo %GREEN% exec-approvals: security = allowlist
    ) else (
        echo %YELLOW% Could not update exec-approvals.json automatically
    )
    
    openclaw approvals allowlist add --agent "*" "*/clawteam" >nul 2>&1
    if !errorlevel! equ 0 (
        echo %GREEN% clawteam added to allowlist
    ) else (
        echo %YELLOW% Could not add to allowlist (openclaw might not be running)
    )
) else (
    echo %YELLOW% exec-approvals.json not found - run 'openclaw' once to initialize it.
)

:: ─── 9. Claude Code skill ──────────────────────────────────────────────
echo %CYAN% Setting up Claude Code skill...
set "CC_SKILL_DIR=%REPO_ROOT%\.claude\skills\clawteam"
set "CC_SKILL_SRC_DIR=%REPO_ROOT%\skills\clawteam"

if exist "%CC_SKILL_SRC_DIR%\SKILL.md" (
    if not exist "%CC_SKILL_DIR%" mkdir "%CC_SKILL_DIR%"
    copy /Y "%CC_SKILL_SRC_DIR%\SKILL.md" "%CC_SKILL_DIR%\SKILL.md" >nul
    if exist "%CC_SKILL_SRC_DIR%\references" (
        xcopy /E /I /Y "%CC_SKILL_SRC_DIR%\references" "%CC_SKILL_DIR%\references" >nul
    )
    echo %GREEN% Claude Code skill installed
) else (
    echo %YELLOW% Claude Code skill source not found
)

if exist "%REPO_ROOT%\docs\CLAUDE.md" (
    copy /Y "%REPO_ROOT%\docs\CLAUDE.md" "%REPO_ROOT%\CLAUDE.md" >nul
    echo %GREEN% CLAUDE.md copied to repo root
)

:: ─── 10. Verify ─────────────────────────────────────────────────────────
echo %CYAN% Verifying installation...
call clawteam --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%x in ('clawteam --version') do set CT_VERSION=%%x
    echo %GREEN% !CT_VERSION!
) else (
    echo %YELLOW% Warning: Unable to verify clawteam command. You may need to restart the terminal.
)

:: ─── Done ────────────────────────────────────────────────────────────────
echo.
echo   ==================================================
echo     ✅ Setup complete! ClawTeam is ready to use. 
echo   ==================================================
echo.
echo Next steps:
echo   1. call .venv\Scripts\activate
echo   2. clawteam config health
echo   3. clawteam team spawn-team demo -d "test" -n leader
echo.
