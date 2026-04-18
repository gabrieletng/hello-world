#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK="$REPO_ROOT/.git/hooks/pre-commit"

# Minimal hook — staging is handled by sync.sh
cat > "$HOOK" << 'EOF'
#!/usr/bin/env bash
exit 0
EOF

chmod +x "$HOOK"
echo "pre-commit hook installed."
