#!/usr/bin/env python3

from pathlib import Path

from exportlib.read_events import read_events
from exportlib.build_logbuch_document import build_document

from renderers.render_markdown import render_markdown
from renderers.render_html import render_html


def export(
    logbuch_dir,
    output_dir,
    start_date,
    end_date,
    formats=("markdown", "html"),
    title="Digitales Logbuch",
):
    """
    Exportiert Logbuchdaten in die gewünschten Ausgabeformate.

    Parameter:
        logbuch_dir : Verzeichnis mit den JSONL-Dateien
        output_dir  : Zielverzeichnis
        start_date  : datetime.date
        end_date    : datetime.date
        formats     : ("markdown", "html") oder Teilmenge davon
        title       : Dokumenttitel
    """

    events = read_events(
        logbuch_dir=logbuch_dir,
        start_date=start_date,
        end_date=end_date,
    )

    document = build_document(
        events,
        title=title,
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    written_files = []

    if "markdown" in formats:
        md_path = output_dir / "logbuch.md"

        md_path.write_text(
            render_markdown(document),
            encoding="utf-8",
        )

        written_files.append(md_path)

    if "html" in formats:
        html_path = output_dir / "logbuch.html"

        html_path.write_text(
            render_html(document),
            encoding="utf-8",
        )

        written_files.append(html_path)

    return written_files


__all__ = [
    "export",
]
