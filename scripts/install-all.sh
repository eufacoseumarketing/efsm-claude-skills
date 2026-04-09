#!/bin/bash
# Instala todas as skills em ~/.claude/skills/
# Uso: ./scripts/install-all.sh

set -e

SCRIPTS_DIR="$(dirname "$0")"
SKILLS_DIR="$SCRIPTS_DIR/../skills"

for skill_dir in "$SKILLS_DIR"/*/; do
  skill_name="$(basename "$skill_dir")"
  bash "$SCRIPTS_DIR/install.sh" "$skill_name"
done

echo ""
echo "Todas as skills instaladas com sucesso."
