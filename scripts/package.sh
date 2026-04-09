#!/bin/bash
# Empacota uma skill em um .zip para distribuição
# Uso: ./scripts/package.sh nome-da-skill

set -e

SKILL_NAME="$1"
SKILLS_DIR="$(dirname "$0")/../skills"
PACKAGES_DIR="$(dirname "$0")/../packages"

if [ -z "$SKILL_NAME" ]; then
  echo "Uso: $0 <nome-da-skill>"
  echo ""
  echo "Skills disponíveis:"
  ls "$SKILLS_DIR"
  exit 1
fi

SKILL_DIR="$SKILLS_DIR/$SKILL_NAME"

if [ ! -d "$SKILL_DIR" ]; then
  echo "Erro: skill '$SKILL_NAME' não encontrada em $SKILLS_DIR"
  exit 1
fi

mkdir -p "$PACKAGES_DIR"
OUTPUT="$PACKAGES_DIR/$SKILL_NAME.zip"

cd "$SKILLS_DIR"
zip -r "$OUTPUT" "$SKILL_NAME/"
echo "Pacote gerado: $OUTPUT"
