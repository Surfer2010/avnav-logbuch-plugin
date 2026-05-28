#!/usr/bin/env bash
set -euo pipefail

# AVNav Logbuch Plugin installer/updater
#
# Installs from:
# - extracted release ZIP: user-logbuch/tools/install_or_update.sh
# - git checkout: tools/install_or_update.sh
#
# It removes legacy plugin directories from the active AVNav plugin path.
# It does not delete logbook data files.

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

if ! command -v unzip >/dev/null 2>&1; then
    echo "ERROR: unzip is required."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "${SCRIPT_DIR}/../plugin.py" ]; then
    SOURCE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
    TOOLS_SOURCE_DIR="${SCRIPT_DIR}"
elif [ -d "${SCRIPT_DIR}/../logbuch" ] && [ -f "${SCRIPT_DIR}/../logbuch/plugin.py" ]; then
    SOURCE_DIR="$(cd "${SCRIPT_DIR}/../logbuch" && pwd)"
    TOOLS_SOURCE_DIR="${SCRIPT_DIR}"
else
    echo "ERROR: Could not find plugin source directory."
    echo "Expected either:"
    echo "  ${SCRIPT_DIR}/../plugin.py"
    echo "or:"
    echo "  ${SCRIPT_DIR}/../logbuch/plugin.py"
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

mkdir -p "${PLUGIN_PARENT_DIR}"
mkdir -p "${BACKUP_DIR}"

if [ -d "${TARGET_DIR}" ]; then
    BACKUP_PATH="${BACKUP_DIR}/logbuch.backup.${STAMP}"
    echo "Creating plugin backup: ${BACKUP_PATH}"
    cp -a "${TARGET_DIR}" "${BACKUP_PATH}"
else
    echo "No existing logbuch plugin directory found. Skipping logbuch backup."
fi

if [ -d "${PLUGIN_PARENT_DIR}/logbook" ]; then
if [ -d "${PLUGIN_PARENT_DIR}/user-logbook" ]; then

    LEGACY_ID_BACKUP="${BACKUP_DIR}/user-logbook.legacy.${STAMP}"

    echo "Moving legacy plugin-id directory to backup: ${LEGACY_ID_BACKUP}"

    mv "${PLUGIN_PARENT_DIR}/user-logbook" "${LEGACY_ID_BACKUP}"

fi

    LEGACY_BACKUP="${BACKUP_DIR}/logbook.legacy.${STAMP}"
    echo "Moving legacy plugin to backup: ${LEGACY_BACKUP}"
    mv "${PLUGIN_PARENT_DIR}/logbook" "${LEGACY_BACKUP}"
fi

for LEGACY_DISABLED in \
    "${PLUGIN_PARENT_DIR}"/logbook.disabled* \
    "${PLUGIN_PARENT_DIR}"/user-logbook.disabled*; do
    if [ -e "${LEGACY_DISABLED}" ]; then
        LEGACY_DISABLED_BACKUP="${BACKUP_DIR}/$(basename "${LEGACY_DISABLED}").${STAMP}"
        echo "Moving disabled legacy plugin to backup: ${LEGACY_DISABLED_BACKUP}"
        mv "${LEGACY_DISABLED}" "${LEGACY_DISABLED_BACKUP}"
    fi
done

if [ -f "${AVNAV_DATA_DIR}/avnav_server.xml" ]; then
    CONFIG_BACKUP="${BACKUP_DIR}/avnav_server.xml.backup.${STAMP}"
    echo "Creating config backup: ${CONFIG_BACKUP}"
    cp -a "${AVNAV_DATA_DIR}/avnav_server.xml" "${CONFIG_BACKUP}"
fi

rm -rf "${PLUGIN_PARENT_DIR}/logbook" 2>/dev/null || true

rm -rf "${PLUGIN_PARENT_DIR}/user-logbook" 2>/dev/null || true

rm -rf "${TARGET_DIR}"
mkdir -p "${TARGET_DIR}"

mkdir -p "${AVNAV_DATA_DIR}/overlays"
chmod 755 "${AVNAV_DATA_DIR}/overlays"

cp -a "${SOURCE_DIR}/." "${TARGET_DIR}/"

TOOLS_TARGET_DIR="${AVNAV_DATA_DIR}/logbook-tools"
echo "Installing tools to: ${TOOLS_TARGET_DIR}"
rm -rf "${TOOLS_TARGET_DIR}"
mkdir -p "${TOOLS_TARGET_DIR}"
cp -a "${TOOLS_SOURCE_DIR}/." "${TOOLS_TARGET_DIR}/"
chmod -R 755 "${TOOLS_TARGET_DIR}"

chmod -R 755 "${TARGET_DIR}"

echo "Checking Python syntax..."
python3 -m py_compile "${TARGET_DIR}/plugin.py"

if [ "${RESTART_AVNAV}" = "yes" ]; then
    echo "Restarting AVNav..."
    if command -v systemctl >/dev/null 2>&1; then
        sudo systemctl restart avnav
    else
        echo "WARNING: systemctl not found. Please restart AVNav manually."
    fi
else
    echo "Skipping AVNav restart because --no-restart was used."
fi

echo "Installation/update finished."
echo "Installed plugin.json:"
cat "${TARGET_DIR}/plugin.json"

echo ""
echo "Installed files:"
find "${TARGET_DIR}" -maxdepth 2 -type f | sort

echo ""
echo "Useful checks:"
echo "  find ${PLUGIN_PARENT_DIR} -maxdepth 2 -name plugin.json -print -exec cat {} \\;"
echo "  curl http://localhost:8080/plugins/user-logbuch/plugin.js | head"
echo "  curl http://localhost:8080/plugins/user-logbook/plugin.js | head"
echo ""
echo "Rollback example:"
echo "  rm -rf ${TARGET_DIR}"
echo "  cp -a ${BACKUP_DIR}/logbuch.backup.${STAMP} ${TARGET_DIR}"
echo "  sudo systemctl restart avnav"
