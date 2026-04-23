from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


def write_image_html_report(
    path: Path,
    *,
    title: str,
    header: dict[str, Any],
    summary: dict[str, Any],
    items: list[dict[str, Any]],
    skipped_items: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "file-merge-tool/image-html-report/v1",
        "header": header,
        "summary": summary,
        "items": [_manifest_item(item) for item in items],
        "skipped_items": skipped_items,
        "warnings": warnings,
    }
    html = _render_html(title=title, manifest=manifest, items=items)
    path.write_text(html, encoding="utf-8", newline="\n")
    return path


def _render_html(*, title: str, manifest: dict[str, Any], items: list[dict[str, Any]]) -> str:
    cards = "\n".join(_render_card(item) for item in items)
    manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="ja">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(title)}</title>
    <style>
      :root {{
        --bg: #f2f3f2;
        --ink: #151514;
        --muted: #5f574b;
        --surface: #fffdf8;
        --line: #d8cbb2;
        --gold: #76551d;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        background: var(--bg);
        color: var(--ink);
        font-family: "Yu Gothic", "Yu Gothic UI", "Segoe UI", sans-serif;
      }}
      header {{
        padding: 28px 32px 18px;
        border-bottom: 1px solid var(--line);
        background: var(--surface);
      }}
      h1 {{
        margin: 0;
        font-family: Georgia, "Times New Roman", "Yu Mincho", serif;
        font-size: 36px;
        font-weight: 500;
      }}
      .summary {{
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 14px;
        color: var(--muted);
      }}
      main {{
        display: grid;
        gap: 16px;
        padding: 24px 32px 40px;
      }}
      .image-item {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(260px, 340px);
        gap: 18px;
        border: 1px solid var(--line);
        background: var(--surface);
        padding: 16px;
      }}
      figure {{ margin: 0; display: grid; gap: 10px; }}
      img {{
        width: 100%;
        max-height: 78vh;
        object-fit: contain;
        background: #fff;
        border: 1px solid var(--line);
      }}
      figcaption {{ color: var(--gold); font-weight: 600; overflow-wrap: anywhere; }}
      dl {{ margin: 0; display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 8px 12px; }}
      dt {{ color: var(--muted); }}
      dd {{ margin: 0; overflow-wrap: anywhere; }}
      @media (max-width: 820px) {{
        header, main {{ padding-left: 18px; padding-right: 18px; }}
        .image-item {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <header>
      <h1>{escape(title)}</h1>
      <div class="summary">
        <span>Items: {escape(str(manifest["summary"].get("item_count", 0)))}</span>
        <span>Skipped: {escape(str(manifest["summary"].get("skipped_count", 0)))}</span>
        <span>Warnings: {escape(str(manifest["summary"].get("warning_count", 0)))}</span>
      </div>
    </header>
    <main>
{cards}
    </main>
    <script type="application/json" id="merge-manifest">{manifest_json}</script>
  </body>
</html>
"""


def _render_card(item: dict[str, Any]) -> str:
    sensitivity = item.get("sensitivity", {})
    classified = "sensitive" if sensitivity.get("classified") else "normal"
    return f"""      <article class="image-item" id="{escape(str(item["id"]))}" data-relative-path="{escape(str(item["relative_path"]))}">
        <figure>
          <img src="{escape(str(item["data_uri"]), quote=True)}" alt="{escape(str(item["relative_path"]))}" loading="lazy" />
          <figcaption>{escape(str(item["relative_path"]))}</figcaption>
        </figure>
        <dl>
          <dt>Absolute path</dt><dd>{escape(str(item["absolute_path"]))}</dd>
          <dt>Modified</dt><dd>{escape(str(item.get("modified_at") or ""))}</dd>
          <dt>Image</dt><dd>{escape(str(item["width"]))} x {escape(str(item["height"]))} px</dd>
          <dt>Bytes</dt><dd>{escape(str(item["file_size_bytes"]))}</dd>
          <dt>MIME</dt><dd>{escape(str(item["mime_type"]))}</dd>
          <dt>Sensitivity</dt><dd>{escape(classified)}</dd>
        </dl>
      </article>"""


def _manifest_item(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if key != "data_uri"}
