# EFSM Claude Skills

Coleção de skills do Claude Code para os colaboradores da EFSM.

## Estrutura

```
skills/
  nome-da-skill/
    SKILL.md      # Arquivo da skill (instalado em ~/.claude/commands/)
    README.md     # Documentação de uso
    examples/     # Exemplos de uso
scripts/
  install.sh      # Instala uma skill específica (macOS/Linux)
  install-all.sh  # Instala todas as skills (macOS/Linux)
  package.sh      # Empacota uma skill para distribuição (macOS/Linux)
  install.ps1     # Instala uma skill específica (Windows)
  install-all.ps1 # Instala todas as skills (Windows)
  package.ps1     # Empacota uma skill para distribuição (Windows)
packages/         # Skills empacotadas prontas para compartilhar
```

## Instalação

### macOS / Linux

#### Instalar uma skill específica

```bash
bash scripts/install.sh nome-da-skill
```

#### Instalar todas as skills

```bash
bash scripts/install-all.sh
```

### Windows (PowerShell)

#### Instalar uma skill específica

```powershell
.\scripts\install.ps1 nome-da-skill
```

#### Instalar todas as skills

```powershell
.\scripts\install-all.ps1
```

> **Nota:** se o PowerShell bloquear a execução, rode antes:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Distribuição

Para gerar um pacote `.zip` de uma skill para enviar a um colaborador:

**macOS / Linux**
```bash
bash scripts/package.sh nome-da-skill
```

**Windows**
```powershell
.\scripts\package.ps1 nome-da-skill
```

O colaborador recebe o `.zip`, extrai a pasta, e instala manualmente:

**macOS / Linux**
```bash
cp SKILL.md ~/.claude/commands/nome-da-skill.md
```

**Windows**
```powershell
Copy-Item SKILL.md "$env:USERPROFILE\.claude\commands\nome-da-skill.md"
```

## Skills disponíveis

| Skill | Descrição |
|-------|-----------|
| [exemplo-skill](skills/exemplo-skill/README.md) | Template de exemplo para criar novas skills |
| [efsm-copy](skills/efsm-copy/README.md) | Copywriting para Landing Pages, Meta Ads, artigos de blog e redes sociais |
| [efsm-crm](skills/efsm-crm/SKILL.md) | Processa o ZIP White Label do CRM fornecedor e gera a versão EFSM com identidade visual |
| [efsm-n8n](skills/efsm-n8n/SKILL.md) | Projeta, constrói e otimiza workflows de automação no n8n da EFSM |
| [gabs-design](skills/gabs-design/README.md) | Engenharia de prompt para IA generativa (Gemini, Firefly, DALL-E, Midjourney) |
