#!/bin/sh
# À lancer UNE fois par chaque membre après le clone : sh scripts/install-hooks.sh
set -e
chmod +x hooks/commit-msg
git config core.hooksPath hooks
echo "Hook commit-msg installé : les lignes Co-authored-by Claude seront retirées."
