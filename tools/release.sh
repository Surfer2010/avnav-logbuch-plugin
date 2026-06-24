#!/bin/sh
set -eu

VERSION="${1:-}"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version>"
  echo "Example: $0 1.6.2"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

sed -i "s/\"version\": *\"[^\"]*\"/\"version\": \"$VERSION\"/" \
  "$ROOT/logbuch/plugin.json"

mkdir -p "$ROOT/dist/logbuch"

rsync -a --delete \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  --exclude "*.bak*" \
  "$ROOT/logbuch/" \
  "$ROOT/dist/logbuch/"

sed -i "s/v__LOGBUCH_VERSION__/v$VERSION/g" \
  "$ROOT/dist/logbuch/plugin.js"

mkdir -p "$ROOT/dist/logbuch/tools"
cp "$ROOT/tools/install_or_update.sh" "$ROOT/dist/logbuch/tools/install_or_update.sh"
chmod +x "$ROOT/dist/logbuch/tools/install_or_update.sh"

cd "$ROOT/dist"
rm -f "logbuch-v$VERSION.zip"
zip -qr "logbuch-v$VERSION.zip" logbuch

echo "Release package created:"
echo "$ROOT/dist/logbuch-v$VERSION.zip"

grep -n '"version"' "$ROOT/logbuch/plugin.json" "$ROOT/dist/logbuch/plugin.json"
grep -n "logbuchVersion" "$ROOT/dist/logbuch/plugin.js"
ls -lh "$ROOT/dist/logbuch-v$VERSION.zip"
