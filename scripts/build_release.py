#!/usr/bin/env python3

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


REQUIRED_PLUGIN_FILES = (
    "plugin.py",
    "plugin.js",
    "plugin.mjs",
    "plugin.css",
    "plugin.json",
    "index.html",
)

REQUIRED_TOOL_FILES = (
    "export_range_html.py",
    "export_range_kmz.py",
    "export_daily_html.py",
    "export_trip_kmz.py",
    "export_additional_kmz.py",
)

FORBIDDEN_PARTS = (
    "__pycache__",
    ".git",
)

FORBIDDEN_SUFFIXES = (
    ".pyc",
    ".pyo",
    ".bak",
    "~",
)


def should_copy(path: Path) -> bool:
    parts = set(path.parts)

    if any(part in parts for part in FORBIDDEN_PARTS):
        return False

    name = path.name

    if any(name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
        return False

    if ".before-" in name:
        return False

    return True


def copy_tree_filtered(source: Path, destination: Path) -> None:
    for path in source.rglob("*"):
        relative = path.relative_to(source)

        if not should_copy(relative):
            continue

        target = destination / relative

        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def validate_source(
    repository: Path,
    expected_version: str,
) -> None:
    plugin = repository / "logbuch"
    tools = repository / "tools"

    for filename in REQUIRED_PLUGIN_FILES:
        path = plugin / filename

        if not path.is_file():
            raise RuntimeError(
                f"Erforderliche Plugin-Datei fehlt: {path}"
            )

    for filename in REQUIRED_TOOL_FILES:
        path = tools / filename

        if not path.is_file():
            raise RuntimeError(
                f"Erforderliches Exportskript fehlt: {path}"
            )

    for directory in ("exportlib", "renderers"):
        path = tools / directory

        if not path.is_dir():
            raise RuntimeError(
                f"Erforderliches Werkzeugverzeichnis fehlt: {path}"
            )

    plugin_json = json.loads(
        (plugin / "plugin.json").read_text(encoding="utf-8")
    )

    actual_version = str(plugin_json.get("version") or "")

    if actual_version != expected_version:
        raise RuntimeError(
            f"plugin.json-Version {actual_version!r}, "
            f"erwartet {expected_version!r}"
        )

    plugin_mjs = (
        plugin / "plugin.mjs"
    ).read_text(encoding="utf-8")

    expected_line = (
        f'var LOGBUCH_VERSION = "{expected_version}";'
    )

    if expected_line not in plugin_mjs:
        raise RuntimeError(
            "Sichtbare Overlay-Version stimmt nicht"
        )

    plugin_js = (
        plugin / "plugin.js"
    ).read_text(encoding="utf-8")

    expected_import = (
        f'import("./plugin.mjs?v={expected_version}")'
    )

    if expected_import not in plugin_js:
        raise RuntimeError(
            "Legacy-Cache-Buster fehlt oder hat falsche Version"
        )


def validate_archive(
    archive: Path,
    expected_version: str,
) -> None:
    required = [
        "logbuch/plugin.py",
        "logbuch/plugin.js",
        "logbuch/plugin.mjs",
        "logbuch/plugin.css",
        "logbuch/plugin.json",
        "logbuch/index.html",
    ]

    required.extend(
        f"logbuch/tools/{filename}"
        for filename in REQUIRED_TOOL_FILES
    )

    required.extend(
        (
            "logbuch/tools/exportlib/",
            "logbuch/tools/renderers/",
        )
    )

    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        name_set = set(names)

        for name in required:
            if name.endswith("/"):
                if not any(
                    candidate.startswith(name)
                    for candidate in names
                ):
                    raise RuntimeError(
                        f"Verzeichnis fehlt im ZIP: {name}"
                    )
            elif name not in name_set:
                raise RuntimeError(
                    f"Datei fehlt im ZIP: {name}"
                )

        forbidden = [
            name for name in names
            if "__pycache__" in name
            or name.endswith(".pyc")
            or name.endswith(".pyo")
            or ".before-" in name
        ]

        if forbidden:
            raise RuntimeError(
                "Unzulässige ZIP-Inhalte: "
                + ", ".join(forbidden[:10])
            )

        plugin_json = json.loads(
            zf.read(
                "logbuch/plugin.json"
            ).decode("utf-8")
        )

        if str(plugin_json.get("version")) != expected_version:
            raise RuntimeError(
                "Falsche Version im Release-ZIP"
            )

        plugin_mjs = zf.read(
            "logbuch/plugin.mjs"
        ).decode("utf-8")

        if (
            f'var LOGBUCH_VERSION = "{expected_version}";'
            not in plugin_mjs
        ):
            raise RuntimeError(
                "Sichtbare Overlay-Version fehlt im ZIP"
            )

        plugin_js = zf.read(
            "logbuch/plugin.js"
        ).decode("utf-8")

        if (
            f'import("./plugin.mjs?v={expected_version}")'
            not in plugin_js
        ):
            raise RuntimeError(
                "Legacy-Cache-Buster fehlt im ZIP"
            )


def build(
    repository: Path,
    archive: Path,
    checksum: Path,
    version: str,
) -> None:
    validate_source(repository, version)

    archive.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="avnav-logbuch-release-"
    ) as temporary:
        root = Path(temporary)
        package = root / "logbuch"
        package.mkdir(parents=True)

        copy_tree_filtered(
            repository / "logbuch",
            package,
        )

        tools_target = package / "tools"
        tools_target.mkdir(parents=True)

        copy_tree_filtered(
            repository / "tools",
            tools_target,
        )

        if archive.exists():
            archive.unlink()

        with zipfile.ZipFile(
            archive,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as zf:
            for path in sorted(package.rglob("*")):
                relative = path.relative_to(root)

                if path.is_dir():
                    zf.writestr(
                        str(relative).rstrip("/") + "/",
                        "",
                    )
                else:
                    zf.write(path, relative)

    validate_archive(archive, version)

    digest = hashlib.sha256(
        archive.read_bytes()
    ).hexdigest()

    checksum.write_text(
        f"{digest}  {archive.name}\n",
        encoding="utf-8",
    )

    print(f"Release-ZIP: {archive}")
    print(f"SHA256: {digest}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Erstellt ein vollständiges AVNav-Logbuch-Release."
        )
    )

    parser.add_argument(
        "--version",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--checksum",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    repository = Path(__file__).resolve().parent.parent

    build(
        repository=repository,
        archive=args.output.resolve(),
        checksum=args.checksum.resolve(),
        version=args.version,
    )


if __name__ == "__main__":
    main()
