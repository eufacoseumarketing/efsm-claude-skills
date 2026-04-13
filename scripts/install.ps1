# Instala uma skill específica em ~/.claude/commands/
# Uso: .\scripts\install.ps1 nome-da-skill

param(
    [Parameter(Mandatory=$false)]
    [string]$SkillName
)

$ScriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDir  = Join-Path $ScriptsDir "..\skills"
$TargetDir  = Join-Path $env:USERPROFILE ".claude\commands"

if (-not $SkillName) {
    Write-Host "Uso: .\scripts\install.ps1 <nome-da-skill>"
    Write-Host ""
    Write-Host "Skills disponíveis:"
    Get-ChildItem $SkillsDir -Directory | Select-Object -ExpandProperty Name
    exit 1
}

$SkillFile = Join-Path $SkillsDir "$SkillName\SKILL.md"

if (-not (Test-Path $SkillFile)) {
    Write-Error "Erro: skill '$SkillName' não encontrada em $SkillsDir"
    exit 1
}

if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir | Out-Null
}

Copy-Item $SkillFile (Join-Path $TargetDir "$SkillName.md")
Write-Host "Skill '$SkillName' instalada em $TargetDir\$SkillName.md"
