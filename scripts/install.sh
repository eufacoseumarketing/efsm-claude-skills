#!/bin/bash
# Instala uma skill específica em ~/.claude/skills/
# Uso: ./scripts/install.sh nome-da-skill

set -e

SKILL_NAME="$1"
SKILLS_DIR="$(dirname "$0")/../skills"
TARGET_DIR="$HOME/.claude/skills"

if [ -z "$SKILL_NAME" ]; then
  echo "Uso: $0 <nome-da-skill>"
  echo ""
  echo "Skills disponíveis:"
  ls "$SKILLS_DIR"
  exit 1
fi

SKILL_FILE="$SKILLS_DIR/$SKILL_NAME/skill.md"

if [ ! -f "$SKILL_FILE" ]; then
  echo "Erro: skill '$SKILL_NAME' não encontrada em $SKILLS_DIR"
  exit 1
fi

mkdir -p "$TARGET_DIR"
cp "$SKILL_FILE" "$TARGET_DIR/$SKILL_NAME.md"
echo "Skill '$SKILL_NAME' instalada em $TARGET_DIR/$SKILL_NAME.md"
