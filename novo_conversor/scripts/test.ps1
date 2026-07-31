[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectDirectory = Split-Path -Parent $PSScriptRoot
$pythonExecutable = Join-Path $projectDirectory ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw "Ambiente não encontrado. Execute scripts\setup-dev.ps1 primeiro."
}

Push-Location $projectDirectory
try {
    & $pythonExecutable -m pytest
    if ($LASTEXITCODE -ne 0) {
        throw "Os testes falharam com código $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

