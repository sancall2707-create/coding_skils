#!/bin/bash
# PWA Readiness Verification Script
# Usage: ./verify-pwa-readiness.sh /path/to/laravel/app

set -e

APP_DIR="${1:-.}"
PUBLIC_DIR="$APP_DIR/public"

echo "=== PWA READINESS AUDIT ==="
echo "Target directory: $PUBLIC_DIR"
echo

# 1. Manifest Check
if [ -f "$PUBLIC_DIR/manifest.json" ]; then
    echo "✅ manifest.json exists"
    # Basic JSON validation
    if python3 -c "import json; json.load(open('$PUBLIC_DIR/manifest.json'))" 2>/dev/null; then
        echo "✅ manifest.json is valid JSON"
    else
        echo "❌ manifest.json is INVALID JSON"
        exit 1
    fi
else
    echo "❌ manifest.json MISSING"
    exit 1
fi

# 2. Service Worker Check
if [ -f "$PUBLIC_DIR/sw.js" ]; then
    echo "✅ sw.js exists"
    
    # Check for dangerous API caching
    if grep -q "cache\.put" "$PUBLIC_DIR/sw.js" && grep -q "/api/" "$PUBLIC_DIR/sw.js"; then
        echo "⚠️ WARNING: Potential API caching detected in sw.js! Verify security rules."
    else
        echo "✅ sw.js caching rules look secure"
    fi
else
    echo "❌ sw.js MISSING"
    exit 1
fi

# 3. Icons Check
if [ -d "$PUBLIC_DIR/icons" ] && [ "$(ls -A "$PUBLIC_DIR/icons")" ]; then
    echo "✅ icons directory exists and not empty"
else
    echo "⚠️ WARNING: icons directory missing or empty"
fi

# 4. File Permissions Check
MANIFEST_PERM=$(stat -c "%a" "$PUBLIC_DIR/manifest.json")
SW_PERM=$(stat -c "%a" "$PUBLIC_DIR/sw.js")

if [ "$MANIFEST_PERM" -ge "644" ] && [ "$SW_PERM" -ge "644" ]; then
    echo "✅ File permissions valid (manifest: $MANIFEST_PERM, sw: $SW_PERM)"
else
    echo "⚠️ File permissions may block web server (manifest: $MANIFEST_PERM, sw: $SW_PERM). Run: chmod 644 public/manifest.json public/sw.js"
fi

echo
echo "=== PWA READINESS AUDIT PASSED ==="
