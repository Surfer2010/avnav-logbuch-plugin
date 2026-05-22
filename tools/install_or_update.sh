#!/usr/bin/env bash
set -euo pipefail

# AVNav Logbook Plugin installer/updater
#
# Purpose:
# - download plugin ZIP from GitHub
# - create backup of existing plugin
# - install/update plugin files
# - restart AVNav unless disabled
#
# Usage:
#   ./tools/install_or_update.sh
#   ./tools/install_or_update.sh --branch main
#   ./tools/install_or_update.sh --branch fix/responsive-overlay-input-button
#   ./tools/install_or_update.sh --target /home/pi/avnav/data/plugins/logbook
#   ./tools/install_or_update.sh --no-restart
#
# Notes:
# - This script is intended for AVNav systems without git.
# - It uses wget and unzip.
# - It does not delete logbook data files.

REPO_OWNER="Surfer2010"
REPO_NAME="avnav-logbuch-plugin"
BRANCH="main"
TARGET_DIR=""
RESTART_AVNAV="yes"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --target)
            TARGET_DIR="$2"
            shift 2
            ;;
        --no-restart)
            RESTART_AVNAV="no"
            shift 1
            ;;
        --help|-h)
            echo "Usage: $0 [--branch BRANCH] [--target TARGET_DIR] [--no-restart]"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

echo "AVNav Logbook Plugin installer/updater"
echo "Repository: ${REPO_OWNER}/${REPO_NAME}"
echo "Branch: ${BRANCH}"

if ! command -v wget >/dev/null 2>&1; then
    echo "ERROR: wget is required."
    exit 1
fi

if ! command -v unzip >/dev/null 2>&1; then
    echo "ERROR: unzip is required."
    exit 1
fi

# Detect AVNav data directory.
if [ -z "${TARGET_DIR}" ]; then
    if [ -d "/home/pi/avnav/data" ]; then
        AVNAV_DATA_DIR="/home/pi/avnav/data"
    elif [ -d "/var/lib/avnav" ]; then
        AVNAV_DATA_DIR="/var/lib/avnav"
    else
        echo "ERROR: Could not detect AVNav data directory."
        echo "Use --target /path/to/plugins/logbook"
        exit 1
    fi

    TARGET_DIR="${AVNAV_DATA_DIR}/plugins/logbook"
else
    AVNAV_DATA_DIR="$(dirname "$(dirname "${TARGET_DIR}")")"
fi

PLUGIN_PARENT_DIR="$(dirname "${TARGET_DIR}")"
BACKUP_DIR="${AVNAV_DATA_DIR}/plugin-backups"
STAMP="$(date +%F-%H%M%S)"
WORK_DIR="/tmp/avnav-logbook-update-${STAMP}"
ZIP_FILE="${WORK_DIR}/plugin.zip"

echo "AVNav data directory: ${AVNAV_DATA_DIR}"
echo "Target plugin directory: ${TARGET_DIR}"
echo "Backup directory: ${BACKUP_DIR}"

mkdir -p "${WORK_DIR}"
mkdir -p "${PLUGIN_PARENT_DIR}"
mkdir -p "${BACKUP_DIR}"

# Backup existing plugin, if present.
if [ -d "${TARGET_DIR}" ]; then
    BACKUP_PATH="${BACKUP_DIR}/logbook.backup.${STAMP}"
    echo "Creating backup: ${BACKUP_PATH}"
    cp -a "${TARGET_DIR}" "${BACKUP_PATH}"
else
    echo "No existing plugin directory found. Skipping plugin backup."
fi

# Backup AVNav config, if present.
if [ -f "${AVNAV_DATA_DIR}/avnav_server.xml" ]; then
    CONFIG_BACKUP="${BACKUP_DIR}/avnav_server.xml.backup.${STAMP}"
    echo "Creating config backup: ${CONFIG_BACKUP}"
    cp -a "${AVNAV_DATA_DIR}/avnav_server.xml" "${CONFIG_BACKUP}"
fi

DOWNLOAD_URL="https://codeload.github.com/${REPO_OWNER}/${REPO_NAME}/zip/refs/heads/${BRANCH}"

echo "Downloading: ${DOWNLOAD_URL}"
wget -O "${ZIP_FILE}" "${DOWNLOAD_URL}"

echo "Unpacking ZIP..."
unzip -q "${ZIP_FILE}" -d "${WORK_DIR}"

SOURCE_DIR="$(find "${WORK_DIR}" -maxdepth 3 -type d -path "*/logbook" | head -n 1)"

if [ -z "${SOURCE_DIR}" ]; then
    echo "ERROR: Could not find logbook directory inside downloaded ZIP."
    exit 1
fi

if [ ! -f "${SOURCE_DIR}/plugin.py" ]; then
    echo "ERROR: plugin.py not found in ${SOURCE_DIR}"
    exit 1
fi

echo "Installing from: ${SOURCE_DIR}"

rm -rf "${TARGET_DIR}"
mkdir -p "${TARGET_DIR}"
cp -a "${SOURCE_DIR}/." "${TARGET_DIR}/"

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
echo "Installed files:"
find "${TARGET_DIR}" -maxdepth 2 -type f | sort

echo ""
echo "Useful checks:"
echo "  tail -n 100 ${AVNAV_DATA_DIR}/log/avnav.log | grep -i logbook"
echo "  curl http://localhost:8080/plugins/user-logbook/plugin.js | head"
echo ""
echo "Rollback example:"
echo "  rm -rf ${TARGET_DIR}"
echo "  cp -a ${BACKUP_DIR}/logbook.backup.${STAMP} ${TARGET_DIR}"
echo "  sudo systemctl restart avnav"
