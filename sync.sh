#!/bin/bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
cp -r ~/.hermes/profiles/coding/skills/software-development/* software-development/
cp -r ~/.hermes/profiles/coding/skills/yohsan-coding .
git add .
if git diff-index --quiet HEAD --; then
  echo "Tidak ada perubahan skill."
else
  git commit -m "chore: sync coding skills $(date +'%Y-%m-%d %H:%M:%S')"
  git push
fi
