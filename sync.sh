#!/bin/bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
mkdir -p software-development
cp -r ~/.hermes/profiles/coding/skills/software-development/* software-development/
cp -r ~/.hermes/profiles/coding/skills/yohsan-coding .
git add .
if git diff-index --quiet HEAD --; then
  exit 0
else
  git commit -m "chore: auto-sync coding skills $(date +'%Y-%m-%d %H:%M:%S')"
  git push origin main
  echo "Skill coding berhasil di-backup otomatis ke GitHub pada $(date +'%Y-%m-%d %H:%M:%S')."
fi
