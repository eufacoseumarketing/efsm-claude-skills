# Instala todas as skills em ~/.claude/commands/
# Uso: .\scripts\install-all.ps1

$ScriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDir  = Join-Path $ScriptsDir "..\skills"

Get-ChildItem $SkillsDir -Directory | ForEach-Object {
    $skillName = $_.Name
    & "$ScriptsDir\install.ps1" $skillName
}

Write-Host ""
Write-Host "Todas as skills instaladas com sucesso."
