[CmdletBinding()]
param(
    [string]$PythonExecutable = "python"
)

$ErrorActionPreference = "Stop"
$projectDirectory = Split-Path -Parent $PSScriptRoot
$environmentDirectory = Join-Path $projectDirectory ".venv"
$environmentPython = Join-Path $environmentDirectory "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $environmentPython)) {
    & $PythonExecutable -m venv $environmentDirectory
}

& $environmentPython -m pip install --upgrade pip
& $environmentPython -m pip install --editable "${projectDirectory}[dev]"

Write-Host "Ambiente preparado em $environmentDirectory"
Write-Host "Execute: .\.venv\Scripts\python.exe -m conversor_folhas"
