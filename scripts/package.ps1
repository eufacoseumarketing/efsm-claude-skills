# Empacota uma skill em um .zip para distribuição
# Uso: .\scripts\package.ps1 nome-da-skill

param(
    [Parameter(Mandatory=$false)]
    [string]$SkillName
)

$ScriptsDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDir   = Join-Path $ScriptsDir "..\skills"
$PackagesDir = Join-Path $ScriptsDir "..\packages"

if (-not $SkillName) {
    Write-Host "Uso: .\scripts\package.ps1 <nome-da-skill>"
    Write-Host ""
    Write-Host "Skills disponíveis:"
    Get-ChildItem $SkillsDir -Directory | Select-Object -ExpandProperty Name
    exit 1
}

$SkillDir = Join-Path $SkillsDir $SkillName

if (-not (Test-Path $SkillDir)) {
    Write-Error "Erro: skill '$SkillName' não encontrada em $SkillsDir"
    exit 1
}

if (-not (Test-Path $PackagesDir)) {
    New-Item -ItemType Directory -Path $PackagesDir | Out-Null
}

$Output = Join-Path $PackagesDir "$SkillName.zip"

# Remove ZIP anterior para evitar arquivos obsoletos
if (Test-Path $Output) {
    Remove-Item $Output
}

Compress-Archive -Path "$SkillDir\*" -DestinationPath $Output
Write-Host "Pacote gerado: $Output"
