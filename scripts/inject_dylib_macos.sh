#!/bin/bash
# inject_dylib_macos.sh
# Injects AMPrem.dylib into a patched AlightMotion binary.
# 
# Usage:
#   1. Place this script in the repo root
#   2. Place the patched binary at: extracted/Payload/AlightMotion.app/AlightMotion
#   3. Make sure AMPrem.dylib is in Frameworks/
#   4. Run: ./scripts/inject_dylib_macos.sh
#
# Or with custom paths:
#   INJECT_BINARY=/path/to/AlightMotion ./scripts/inject_dylib_macos.sh
#
# After injection, repack the IPA:
#   cd extracted && zip -qr ../UltraMotion_Patched.ipa Payload/

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BINARY="${INJECT_BINARY:-$REPO_DIR/extracted/Payload/AlightMotion.app/AlightMotion}"
DYLIB_PATH="@rpath/AMPrem.dylib"

echo "=== AMPrem Dylib Injector ==="
echo "Binary: $BINARY"

# Check binary exists
if [ ! -f "$BINARY" ]; then
    echo "ERROR: Binary not found at $BINARY"
    echo "Set INJECT_BINARY env var or place binary at the default path."
    exit 1
fi

# Get insert_dylib
if command -v insert_dylib &>/dev/null; then
    INSERT_DYLIB="insert_dylib"
else
    INSERT_DYLIB="/tmp/insert_dylib"
    if [ ! -f "$INSERT_DYLIB" ]; then
        echo "Downloading insert_dylib..."
        curl -L -o "$INSERT_DYLIB" https://github.com/Tyilo/insert_dylib/releases/latest/download/insert_dylib
        chmod +x "$INSERT_DYLIB"
    fi
fi

# Backup
cp "$BINARY" "${BINARY}.bak"
echo "Backup: ${BINARY}.bak"

# Check current ncmds
echo "Before: $(otool -l "$BINARY" 2>/dev/null | grep -c "LC_LOAD_DYLIB" || echo "?") LC_LOAD_DYLIB entries"

# Inject
"$INSERT_DYLIB" --inplace --all-yes "$DYLIB_PATH" "$BINARY"

echo "After: $(otool -l "$BINARY" | grep -c "LC_LOAD_DYLIB") LC_LOAD_DYLIB entries"
echo "AMPrem.dylib in load commands:"
otool -L "$BINARY" | grep AMPrem || echo "WARNING: AMPrem.dylib not found in load commands!"

echo ""
echo "=== Done ==="
echo "Binary injected successfully."
echo "Next step: repack IPA"
echo "  cd extracted && zip -qr ../UltraMotion_Patched.ipa Payload/"
