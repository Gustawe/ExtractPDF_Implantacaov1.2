[CmdletBinding()]
param(
    [switch]$SkipTests,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$projectDirectory = Split-Path -Parent $PSScriptRoot
$pythonExecutable = Join-Path $projectDirectory ".venv\Scripts\python.exe"
$iconGenerator = Join-Path $PSScriptRoot "generate-icon.py"
$versionInfoGenerator = Join-Path $PSScriptRoot "generate-version-info.py"
$launcherPath = Join-Path $projectDirectory "launcher.py"
$iconPath = Join-Path $projectDirectory "src\conversor_folhas\resources\app.ico"
$noticesPath = Join-Path $projectDirectory "THIRD_PARTY_NOTICES.md"
$versionInfoPath = Join-Path $projectDirectory "build\version_info.txt"
$distDirectory = Join-Path $projectDirectory "dist"
$workDirectory = Join-Path $projectDirectory "build\pyinstaller"
$specDirectory = Join-Path $projectDirectory "build"
$installerScript = Join-Path $projectDirectory "installer\ConversorFolhas.iss"

if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw "Ambiente não encontrado. Execute scripts\setup-dev.ps1 primeiro."
}

Push-Location $projectDirectory
try {
    if (-not $SkipTests) {
        & $pythonExecutable -m pytest
        if ($LASTEXITCODE -ne 0) {
            throw "Os testes falharam com código $LASTEXITCODE."
        }
    }

    & $pythonExecutable $iconGenerator
    if ($LASTEXITCODE -ne 0) {
        throw "Não foi possível gerar o ícone do aplicativo."
    }

    $applicationVersion = & $pythonExecutable -c "from conversor_folhas import __version__; print(__version__)"
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($applicationVersion)) {
        throw "Não foi possível identificar a versão do aplicativo."
    }
    $applicationVersion = $applicationVersion.Trim()

    & $pythonExecutable $versionInfoGenerator
    if ($LASTEXITCODE -ne 0) {
        throw "Não foi possível gerar os metadados do executável."
    }

    & $pythonExecutable -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --onedir `
        --name "ConversorFolhas" `
        --icon $iconPath `
        --version-file $versionInfoPath `
        --add-data "${iconPath};conversor_folhas/resources" `
        --distpath $distDirectory `
        --workpath $workDirectory `
        --specpath $specDirectory `
        --exclude-module pytest `
        --exclude-module pytestqt `
        --exclude-module tkinter `
        $launcherPath
    if ($LASTEXITCODE -ne 0) {
        throw "O empacotamento falhou com código $LASTEXITCODE."
    }

    $applicationDirectory = Join-Path $distDirectory "ConversorFolhas"
    $applicationExecutable = Join-Path $applicationDirectory "ConversorFolhas.exe"
    if (-not (Test-Path -LiteralPath $applicationExecutable)) {
        throw "O executável esperado não foi gerado: $applicationExecutable"
    }

    # A interface usa textos próprios em português e não instala QTranslator.
    # Portanto, os catálogos multilíngues incluídos pelo hook do Qt são inativos.
    $qtTranslations = Join-Path $applicationDirectory "_internal\PySide6\translations"
    if (Test-Path -LiteralPath $qtTranslations) {
        $resolvedApplicationDirectory = (Resolve-Path -LiteralPath $applicationDirectory).Path
        $resolvedTranslations = (Resolve-Path -LiteralPath $qtTranslations).Path
        if (-not $resolvedTranslations.StartsWith(
            "$resolvedApplicationDirectory\",
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            throw "Diretório de traduções fora do pacote gerado."
        }
        Remove-Item -LiteralPath $resolvedTranslations -Recurse -Force
    }
    Copy-Item -LiteralPath $noticesPath -Destination $applicationDirectory -Force

    $distBytes = (Get-ChildItem -LiteralPath $applicationDirectory -File -Recurse |
        Measure-Object -Property Length -Sum).Sum
    Write-Host ("Aplicativo gerado: {0:N1} MB" -f ($distBytes / 1MB))

    if ($SkipInstaller) {
        return
    }

    $compilerCandidates = @(
        (Get-Command "ISCC.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
        (Join-Path ${env:LOCALAPPDATA} "Programs\Inno Setup 6\ISCC.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
        (Join-Path ${env:ProgramFiles} "Inno Setup 6\ISCC.exe")
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique

    $compiler = $compilerCandidates | Select-Object -First 1
    if (-not $compiler) {
        throw "Inno Setup 6 não encontrado. Instale-o ou use -SkipInstaller."
    }

    & $compiler "/DAppVersion=$applicationVersion" $installerScript
    if ($LASTEXITCODE -ne 0) {
        throw "A criação do instalador falhou com código $LASTEXITCODE."
    }

    $installerPath = Join-Path $projectDirectory "installer\output\Conversor-de-Folhas-Setup-$applicationVersion.exe"
    if (-not (Test-Path -LiteralPath $installerPath)) {
        throw "O instalador esperado não foi gerado: $installerPath"
    }

    $installerFile = Get-Item -LiteralPath $installerPath
    $installerHash = Get-FileHash -LiteralPath $installerPath -Algorithm SHA256
    Write-Host ("Instalador gerado: {0:N1} MB" -f ($installerFile.Length / 1MB))
    Write-Host "SHA-256: $($installerHash.Hash)"
}
finally {
    Pop-Location
}
