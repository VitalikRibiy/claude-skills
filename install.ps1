# install.ps1 — Bootstrap the Claude Skills library on Windows
# Run from PowerShell: .\install.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoUrl   = "https://VitaliiRibii@dev.azure.com/VitaliiRibii/claude-skills/_git/claude-skills"
$InstallDir = "$env:USERPROFILE\claude-skills"

function Write-Step($msg) { Write-Host "`n  $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red; exit 1 }

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "  Claude Skills — Windows Bootstrap" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# ── 1. Check Python ────────────────────────────────────────────────────────────
Write-Step "Checking Python..."
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Fail "Python not found.`n  Install from: https://www.python.org/downloads/`n  Minimum version: Python 3.10"
}
$pyVersion = & python --version 2>&1
Write-Ok $pyVersion

# ── 2. Check Git ──────────────────────────────────────────────────────────────
Write-Step "Checking Git..."
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Fail "Git not found.`n  Install from: https://git-scm.com/download/win"
}
$gitVersion = & git --version
Write-Ok $gitVersion

# ── 3. Clone or update the repo ───────────────────────────────────────────────
Write-Step "Setting up repository at $InstallDir..."

if (Test-Path (Join-Path $InstallDir ".git")) {
    Write-Host "  Repository exists — pulling latest..." -ForegroundColor Yellow
    Push-Location $InstallDir
    & git pull --quiet
    Pop-Location
    Write-Ok "Repository updated"
} else {
    if (Test-Path $InstallDir) {
        Write-Fail "Directory exists but is not a git repo: $InstallDir`n  Remove it and retry."
    }
    Write-Host "  Cloning repository..." -ForegroundColor Yellow
    & git clone $RepoUrl $InstallDir --quiet
    Write-Ok "Repository cloned to $InstallDir"
}

# ── 4. Install Python dependencies ────────────────────────────────────────────
Write-Step "Installing Python dependencies..."
Push-Location $InstallDir
& python -m pip install packaging pyyaml --quiet
Pop-Location
Write-Ok "packaging, pyyaml installed"

# ── 5. Install agent-orchestrator (pulls all 6 skills) ────────────────────────
Write-Step "Installing agent-orchestrator skill (and all dependencies)..."
Push-Location $InstallDir
$result = & python skillman.py install agent-orchestrator 2>&1
$exitCode = $LASTEXITCODE
Pop-Location

if ($exitCode -ne 0) {
    Write-Host $result -ForegroundColor Red
    Write-Fail "skill installation failed"
}

Write-Host $result

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Location:  $InstallDir" -ForegroundColor White
Write-Host ""
Write-Host "  To use the skill, open Claude Code and say:" -ForegroundColor White
Write-Host "    'Avengers assemble'" -ForegroundColor Yellow
Write-Host ""
Write-Host "  To update later:" -ForegroundColor White
Write-Host "    cd $InstallDir" -ForegroundColor Yellow
Write-Host "    python skillman.py update" -ForegroundColor Yellow
Write-Host ""
