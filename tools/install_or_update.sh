#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR=""
RESTART_AVNAV="yes"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --target)
            TARGET_DIR="$2"
            shift 2
            ;;
        --no-restart)
            RESTART_AVNAV="no"
            shift 1
            ;;
        --help|-h)
            echo "Usage: $0 [--target TARGET_DIR] [--no-restart]"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

echo "AVNav Logbuch Plugin installer/updater"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "${SCRIPT_DIR}/../plugin.py" ]; then
    SOURCE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
    TOOLS_SOURCE_DIR="${SCRIPT_DIR}"
elif [ -d "${SCRIPT_DIR}/../logbuch" ] && [ -f "${SCRIPT_DIR}/../logbuch/plugin.py" ]; then
    SOURCE_DIR="$(cd "${SCRIPT_DIR}/../logbuch" && pwd)"
    TOOLS_SOURCE_DIR="${SCRIPT_DIR}"
else
    echo "ERROR: Could not find plugin source directory."
    exit 1
fi

if [ -z "${TARGET_DIR}" ]; then
    DETECTED_DATA_DIR="$(journalctl -u avnav -n 100 --no-pager 2>/dev/null | sed -n 's/.*datadir=\([^ ,]*\).*/\1/p' | tail -n 1)"

    if [ -n "${DETECTED_DATA_DIR}" ] && [ -d "${DETECTED_DATA_DIR}" ]; then
        AVNAV_DATA_DIR="${DETECTED_DATA_DIR}"
    elif [ -d "/home/pi/avnav/data" ]; then
        AVNAV_DATA_DIR="/home/pi/avnav/data"
    elif [ -d "/var/lib/avnav" ]; then
        AVNAV_DATA_DIR="/var/lib/avnav"
    else
        echo "ERROR: Could not detect AVNav data directory."
        echo "Use --target /path/to/plugins/logbuch"
        exit 1
    fi

    TARGET_DIR="${AVNAV_DATA_DIR}/plugins/logbuch"
else
    AVNAV_DATA_DIR="$(dirname "$(dirname "${TARGET_DIR}")")"
fi

PLUGIN_PARENT_DIR="$(dirname "${TARGET_DIR}")"
BACKUP_DIR="${AVNAV_DATA_DIR}/plugin-backups"
STAMP="$(date +%Y%m%d-%H%M%S)"

echo "AVNav data directory: ${AVNAV_DATA_DIR}"
echo "Target plugin directory: ${TARGET_DIR}"
echo "Source plugin directory: ${SOURCE_DIR}"
echo "Tools source directory: ${TOOLS_SOURCE_DIR}"
echo "Backup directory: ${BACKUP_DIR}"

EXISTING_VERSION=""
FORCE_LEGACY_VERSION="no"
if [ -f "${TARGET_DIR}/plugin.json" ]; then
    EXISTING_VERSION="$(python3 - "${TARGET_DIR}/plugin.json" <<'PY_VERSION'
import json
import sys
try:
    with open(sys.argv[1], "r", encoding="utf-8") as handle:
        print(json.load(handle).get("version", ""))
except Exception:
    print("")
PY_VERSION
)"
    if python3 - "${EXISTING_VERSION}" <<'PY_CHECK'
import sys
try:
    parts = [int(value) for value in sys.argv[1].split(".")[:2]]
    while len(parts) < 2:
        parts.append(0)
    raise SystemExit(0 if tuple(parts) <= (1, 9) else 1)
except Exception:
    raise SystemExit(1)
PY_CHECK
    then
        FORCE_LEGACY_VERSION="yes"
    fi
fi

mkdir -p "${PLUGIN_PARENT_DIR}"
mkdir -p "${BACKUP_DIR}"

if [ -d "${TARGET_DIR}" ]; then
    BACKUP_PATH="${BACKUP_DIR}/logbuch.backup.${STAMP}"
    echo "Creating plugin backup: ${BACKUP_PATH}"
    cp -a "${TARGET_DIR}" "${BACKUP_PATH}"
fi

if [ -f "${AVNAV_DATA_DIR}/avnav_server.xml" ]; then
    CONFIG_BACKUP="${BACKUP_DIR}/avnav_server.xml.backup.${STAMP}"
    echo "Creating config backup: ${CONFIG_BACKUP}"
    cp -a "${AVNAV_DATA_DIR}/avnav_server.xml" "${CONFIG_BACKUP}"
fi

rm -rf "${TARGET_DIR}"
mkdir -p "${TARGET_DIR}"

mkdir -p "${AVNAV_DATA_DIR}/overlays"
chmod 755 "${AVNAV_DATA_DIR}/overlays"

cp -a "${SOURCE_DIR}/." "${TARGET_DIR}/"

TOOLS_TARGET_DIR="${AVNAV_DATA_DIR}/logbuch-tools"
echo "Installing tools to: ${TOOLS_TARGET_DIR}"
rm -rf "${TOOLS_TARGET_DIR}"
mkdir -p "${TOOLS_TARGET_DIR}"
cp -a "${TOOLS_SOURCE_DIR}/." "${TOOLS_TARGET_DIR}/"
chmod -R 755 "${TOOLS_TARGET_DIR}"

chmod -R 755 "${TARGET_DIR}"

echo "Checking Python syntax..."
python3 -m py_compile "${TARGET_DIR}/plugin.py" "${TARGET_DIR}/migration.py"

MIGRATED="$(python3 - "${TARGET_DIR}" "${AVNAV_DATA_DIR}" "${PLUGIN_PARENT_DIR}" "${FORCE_LEGACY_VERSION}" <<'PY_MIGRATE'
import sys
sys.path.insert(0, sys.argv[1])
from migration import migrate

force = sys.argv[4] == "yes"
changed = migrate(
    sys.argv[2],
    plugin_parent_dir=sys.argv[3],
    force_legacy_version=force,
    logger=print,
)
print("yes" if changed else "no")
PY_MIGRATE
)"
MIGRATED="$(printf '%s\n' "${MIGRATED}" | tail -n 1)"

if [ "${MIGRATED}" = "yes" ] && [ -n "${BACKUP_PATH:-}" ] && [ -d "${BACKUP_PATH}" ]; then
    echo "Removing temporary legacy plugin backup: ${BACKUP_PATH}"
    rm -rf "${BACKUP_PATH}"
fi

if [ "${MIGRATED}" = "yes" ] && [ "${RESTART_AVNAV}" = "yes" ]; then
    echo "Restarting AVNav once after migration..."
    if command -v systemctl >/dev/null 2>&1; then
        systemctl restart avnav
    elif command -v service >/dev/null 2>&1; then
        service avnav restart
    else
        echo "WARNING: no supported service manager found for the one-time restart."
    fi
elif [ "${MIGRATED}" = "yes" ]; then
    echo "Migration completed; restart suppressed by --no-restart."
else
    echo "No migration required; AVNav restart skipped."
fi

echo "Installation/update finished."
cat "${TARGET_DIR}/plugin.json"

echo ""
echo "Useful checks:"
echo "  find ${PLUGIN_PARENT_DIR} -maxdepth 2 -name plugin.json -print -exec cat {} \\;"
echo "  curl http://localhost:8080/plugins/logbuch/plugin.js | head"
echo "  curl http://localhost:8080/plugins/user-logbuch/plugin.js | head"
