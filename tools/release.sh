#!/bin/sh
set -eu

VERSION="${1:-}"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version>"
  echo "Example: $0 1.6.1"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

sed -i "s/\"version\": *\"[^\"]*\"/\"version\": \"$VERSION\"/" \
  "$ROOT/logbuch/plugin.json"

mkdir -p "$ROOT/dist/logbuch"

rsync -a --delete \
  "$ROOT/logbuch/" \
  "$ROOT/dist/logbuch/"

cd "$ROOT/dist"
rm -f "logbuch-v$VERSION.zip"
zip -qr "logbuch-v$VERSION.zip" logbuch

echo "Release package created:"
echo "$ROOT/dist/logbuch-v$VERSION.zip"

grep -n '"version"' "$ROOT/logbuch/plugin.json" "$ROOT/dist/logbuch/plugin.json"
