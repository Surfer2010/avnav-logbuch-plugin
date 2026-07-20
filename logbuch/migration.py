from __future__ import absolute_import

import json
import os
import shutil
import subprocess
import threading
import time


OLD_LOWER = "log" + "book"
OLD_TITLE = "Log" + "book"
OLD_UPPER = "LOG" + "BOOK"
NEW_LOWER = "logbuch"
MARKER_NAME = ".logbuch-migration-v2-complete"


def _replace_name(value):
    return (
        value.replace(OLD_TITLE, "Logbuch")
        .replace(OLD_UPPER, "LOGBUCH")
        .replace(OLD_LOWER, NEW_LOWER)
        .replace("log" + "-book", NEW_LOWER)
        .replace("log" + "_book", NEW_LOWER)
    )


def _version_is_legacy(version):
    try:
        parts = [int(part) for part in str(version).split(".")[:2]]
        while len(parts) < 2:
            parts.append(0)
        return tuple(parts) <= (1, 9)
    except Exception:
        return False


def read_plugin_version(plugin_dir):
    try:
        with open(os.path.join(plugin_dir, "plugin.json"), "r", encoding="utf-8") as handle:
            return str(json.load(handle).get("version", ""))
    except Exception:
        return ""


def _iter_jsonl(root):
    if not os.path.isdir(root):
        return []
    result = []
    for current, _dirs, files in os.walk(root):
        for filename in files:
            if filename.lower().endswith(".jsonl"):
                result.append(os.path.join(current, filename))
    return sorted(result)


def _remove_path(path):
    if os.path.islink(path) or os.path.isfile(path):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def migration_required(base_dir, plugin_parent_dir=None, force_legacy_version=False):
    marker = os.path.join(base_dir, MARKER_NAME)
    if os.path.exists(marker):
        return False
    if force_legacy_version:
        return True

    legacy_names = [OLD_LOWER, "user-" + OLD_LOWER, OLD_LOWER + "-tools"]
    candidates = [os.path.join(base_dir, name) for name in legacy_names]
    if plugin_parent_dir:
        candidates.extend(os.path.join(plugin_parent_dir, name) for name in legacy_names[:2])
    if any(os.path.exists(path) for path in candidates):
        return True

    new_data_dir = os.path.join(base_dir, NEW_LOWER)
    return any(OLD_LOWER in os.path.basename(path).lower() for path in _iter_jsonl(new_data_dir))


def migrate(base_dir, plugin_parent_dir=None, force_legacy_version=False, logger=None):
    log = logger or (lambda message: None)
    marker = os.path.join(base_dir, MARKER_NAME)
    if os.path.exists(marker):
        return False

    required = migration_required(base_dir, plugin_parent_dir, force_legacy_version)
    if not required:
        with open(marker, "w", encoding="utf-8") as handle:
            handle.write("migration check for 2.x completed\n")
        log("Migration marker created without legacy changes: %s" % marker)
        return False

    new_data_dir = os.path.join(base_dir, NEW_LOWER)
    os.makedirs(new_data_dir, exist_ok=True)

    legacy_roots = [
        os.path.join(base_dir, OLD_LOWER),
        os.path.join(base_dir, "user-" + OLD_LOWER),
    ]
    if plugin_parent_dir:
        legacy_roots.extend([
            os.path.join(plugin_parent_dir, OLD_LOWER),
            os.path.join(plugin_parent_dir, "user-" + OLD_LOWER),
        ])

    seen = set()
    for root in legacy_roots:
        real_root = os.path.realpath(root)
        if real_root in seen:
            continue
        seen.add(real_root)
        for source in _iter_jsonl(root):
            target_name = _replace_name(os.path.basename(source))
            target = os.path.join(new_data_dir, target_name)
            log("Migrating JSONL: %s -> %s" % (source, target))
            os.replace(source, target)

    for source in _iter_jsonl(new_data_dir):
        filename = os.path.basename(source)
        target_name = _replace_name(filename)
        if target_name != filename:
            target = os.path.join(os.path.dirname(source), target_name)
            log("Renaming JSONL: %s -> %s" % (source, target))
            os.replace(source, target)

    removal_candidates = [
        os.path.join(base_dir, OLD_LOWER),
        os.path.join(base_dir, "user-" + OLD_LOWER),
        os.path.join(base_dir, OLD_LOWER + "-tools"),
    ]
    if plugin_parent_dir:
        removal_candidates.extend([
            os.path.join(plugin_parent_dir, OLD_LOWER),
            os.path.join(plugin_parent_dir, "user-" + OLD_LOWER),
        ])

    for path in removal_candidates:
        if os.path.exists(path) or os.path.islink(path):
            log("Removing legacy path: %s" % path)
            _remove_path(path)

    backup_dir = os.path.join(base_dir, "plugin-backups")
    if os.path.isdir(backup_dir):
        for name in os.listdir(backup_dir):
            candidate = os.path.join(backup_dir, name)
            remove_candidate = OLD_LOWER in name.lower()

            if not remove_candidate and os.path.isdir(candidate):
                for current, dirs, files in os.walk(candidate):
                    if any(OLD_LOWER in item.lower() for item in dirs + files):
                        remove_candidate = True
                        break

            if remove_candidate:
                log("Removing legacy plugin backup: %s" % candidate)
                _remove_path(candidate)

    with open(marker, "w", encoding="utf-8") as handle:
        handle.write("migration to 2.x completed\n")
    log("Migration marker created: %s" % marker)
    return True


def restart_avnav_once(logger=None, delay_seconds=1):
    log = logger or (lambda message: None)

    def _restart():
        time.sleep(delay_seconds)
        commands = (["systemctl", "restart", "avnav"], ["service", "avnav", "restart"])
        for command in commands:
            try:
                completed = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if completed.returncode == 0:
                    log("AVNav restarted after one-time migration")
                    return
            except Exception:
                continue
        log("WARNING: automatic AVNav restart after migration failed")

    thread = threading.Thread(target=_restart, name="logbuch-migration-restart")
    thread.daemon = True
    thread.start()
