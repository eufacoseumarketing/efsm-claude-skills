# EFSM Claude Skills

Coleção de skills do Claude Code para os colaboradores da EFSM.

## Estrutura

```
skills/
  nome-da-skill/
    skill.md      # Arquivo da skill (instalado em ~/.claude/skills/)
    README.md     # Documentação de uso
    examples/     # Exemplos de uso
scripts/
  install.sh      # Instala uma skill específica
  install-all.sh  # Instala todas as skills
  package.sh      # Empacota uma skill para distribuição
packages/         # Skills empacotadas prontas para compartilhar
```

## Instalação

### Instalar uma skill específica

```bash
bash scripts/install.sh nome-da-skill
```

### Instalar todas as skills

```bash
bash scripts/install-all.sh
```

## Distribuição

Para gerar um pacote `.zip` de uma skill para enviar a um colaborador:

```bash
bash scripts/package.sh nome-da-skill
```

O colaborador recebe o `.zip`, extrai, e roda:

```bash
cp skill.md ~/.claude/skills/nome-da-skill.md
```

## Skills disponíveis

| Skill | Descrição |
|-------|-----------|
| [exemplo-skill](skills/exemplo-skill/README.md) | Template de exemplo para criar novas skills |
| [efsm-copy](skills/efsm-copy/README.md) | Copywriting para Landing Pages, Meta Ads, artigos de blog e redes sociais |
