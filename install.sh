#!/usr/bin/env bash
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

echo "Building Vision release binary..."
cd "$REPO_DIR"
cargo build --release -p hubd

WRAPPER="$BIN_DIR/vision"
rm -f "$BIN_DIR/vision"
cat <<WRAPPER_EOF > "$WRAPPER"
#!/usr/bin/env bash
REPO_DIR="$REPO_DIR"

cd "\$REPO_DIR"
if [ \$# -eq 0 ]; then
    # Kill any stale daemon instances on port 8085 to avoid conflicts
    fuser -k 8085/tcp 2>/dev/null || true
    pkill -f "detect_service.py" 2>/dev/null || true
    pkill -f "target/release/hubd" 2>/dev/null || true
    pkill -f "target/debug/hubd" 2>/dev/null || true
    sleep 0.5

    echo "⚡ Starting ESP32-S3 Vision Hub on http://127.0.0.1:8085..."
    (sleep 1; if command -v xdg-open >/dev/null 2>&1; then xdg-open http://127.0.0.1:8085 >/dev/null 2>&1; fi) &
    exec ./target/release/hubd
else
    exec ./target/release/hubd "\$@"
fi
WRAPPER_EOF

chmod +x "$WRAPPER"

echo "✓ Installed vision wrapper to $WRAPPER"
echo "✦ You can now launch Vision from anywhere by simply typing: vision"
