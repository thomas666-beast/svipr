# download_page.py
from html import escape

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Svipr — {filename}</title>
<style>
:root {{
  --bg: #0a0e14; --fg: #c8d3e0; --accent: #7ee787;
  --dim: #4a5568; --border: #1f2937;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--bg); color: var(--fg);
  font-family: 'JetBrains Mono', monospace; font-size: 14px;
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh;
}}
.card {{
  max-width: 600px; width: 100%; padding: 32px;
  border: 1px solid var(--border);
}}
.label {{ color: var(--dim); font-size: 12px; text-transform: uppercase;
         letter-spacing: 0.05em; }}
.filename {{ font-size: 20px; color: var(--accent); margin: 8px 0 24px;
             word-break: break-all; }}
.meta {{ color: var(--dim); margin-bottom: 24px; }}
.btn {{
  display: inline-block; padding: 12px 24px; border: 1px solid var(--accent);
  color: var(--accent); text-decoration: none; transition: background 0.15s;
}}
.btn:hover {{ background: rgba(126, 231, 135, 0.1); }}
.curl {{
  margin-top: 24px; background: #000; padding: 12px;
  color: var(--dim); font-size: 12px; overflow-x: auto;
}}
.curl code {{ color: var(--fg); }}
</style>
</head>
<body>
<div class="card">
  <div class="label">svipr · encrypted temporary file</div>
  <div class="filename">{filename}</div>
  <div class="meta">{size}</div>
  <a class="btn" href="/download/{file_id}/raw">download</a>
  <div class="curl">
    <div># or via curl</div>
    <code>curl -O -J /download/{file_id}/raw</code>
  </div>
</div>
</body>
</html>"""


def render_download_page(file_id: str, filename: str, size: int | None) -> str:
    size_str = (
        f"{size} bytes" if size is not None else "unknown size"
    )
    return PAGE.format(
        file_id=escape(file_id),
        filename=escape(filename),
        size=escape(size_str),
    )

def render_download_page(
    file_id: str,
    filename: str,
    size: int | None,
    expires_at: int | None = None,
) -> str:
    if size is not None:
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{size / (1024 ** 3):.2f} GB"
    else:
        size_str = "unknown size"

    if expires_at is not None:
        import time
        remaining = expires_at - int(time.time())
        if remaining <= 0:
            expiry_str = "expired"
        elif remaining < 3600:
            expiry_str = f"expires in {remaining // 60} min"
        elif remaining < 86400:
            expiry_str = f"expires in {remaining // 3600} h"
        else:
            expiry_str = f"expires in {remaining // 86400} d"
        meta_line = f"{size_str} · {expiry_str}"
    else:
        meta_line = size_str

    return PAGE.format(
        file_id=escape(file_id),
        filename=escape(filename),
        size=escape(meta_line),
    )
