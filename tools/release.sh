#!/bin/sh
set -eu

VERSION="${1:-}"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version>"
  echo "Example: $0 1.9.0"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST_ROOT="$ROOT/dist"
PACKAGE_ROOT="$DIST_ROOT/logbuch"
PACKAGE_TOOLS="$PACKAGE_ROOT/tools"
ZIP_FILE="$DIST_ROOT/logbuch-v$VERSION.zip"

sed -i "s/\"version\": *\"[^\"]*\"/\"version\": \"$VERSION\"/" \
  "$ROOT/logbuch/plugin.json"

rm -rf "$PACKAGE_ROOT"
mkdir -p "$PACKAGE_ROOT"

rsync -a --delete \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  --exclude "*.bak*" \
  --exclude "*.before-*" \
  --exclude "*.before.*" \
  "$ROOT/logbuch/" \
  "$PACKAGE_ROOT/"

mkdir -p "$PACKAGE_TOOLS"

rsync -a --delete \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  --exclude "*.bak*" \
  --exclude "*.before-*" \
  --exclude "*.before.*" \
  --exclude "test_*.py" \
  --exclude "release.sh" \
  "$ROOT/tools/" \
  "$PACKAGE_TOOLS/"

sed -i "s/var LOGBUCH_VERSION = \"[^\"]*\";/var LOGBUCH_VERSION = \"$VERSION\";/" \
  "$ROOT/logbuch/plugin.mjs" \
  "$PACKAGE_ROOT/plugin.mjs"

if grep -RIn --exclude-dir="__pycache__" -E "__[A-Z0-9_]*VERSION[A-Z0-9_]*__" "$PACKAGE_ROOT"; then
  echo "ERROR: unresolved version placeholder found" >&2
  exit 1
fi

chmod +x "$PACKAGE_TOOLS/install_or_update.sh"
chmod +x "$PACKAGE_TOOLS/export_additional_kmz.py"
chmod +x "$PACKAGE_TOOLS/export_trip_kmz.py"
chmod +x "$PACKAGE_TOOLS/export_daily_html.py"

cd "$DIST_ROOT"
rm -f "$ZIP_FILE"
zip -qr "$ZIP_FILE" logbuch

echo "Release package created:"
echo "$ZIP_FILE"

grep -n '"version"' \
  "$ROOT/logbuch/plugin.json" \
  "$PACKAGE_ROOT/plugin.json"

grep -n "LOGBUCH_VERSION" "$PACKAGE_ROOT/plugin.mjs" || true
ls -lh "$ZIP_FILE"
