#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIRECTORY="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
USER_HOME_DIRECTORY="${HOME:?Home directory is not set}"
PET_DIRECTORY="$USER_HOME_DIRECTORY/.codex/pets/yain-ivan"

mkdir -p "$PET_DIRECTORY"
cp "$SOURCE_DIRECTORY/pet.json" "$SOURCE_DIRECTORY/spritesheet.webp" "$PET_DIRECTORY/"

printf 'Yain Ivan installed at: %s\n' "$PET_DIRECTORY"
printf 'Refresh the Codex pet picker or restart the app.\n'
