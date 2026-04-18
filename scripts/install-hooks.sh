#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK="$REPO_ROOT/.git/hooks/pre-commit"

cat > "$HOOK" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"

echo "→ syncing ethos images..."
python3 "$REPO_ROOT/scripts/sync-ethos.py"

echo "→ updating manifest..."
python3 "$REPO_ROOT/scripts/update-manifest.py"

git add "$REPO_ROOT/images/" "$REPO_ROOT/manifest.json"
EOF

chmod +x "$HOOK"
echo "pre-commit hook installed."
