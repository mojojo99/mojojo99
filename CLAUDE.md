# mojojo99 — Claude Code Skills

Personal Claude Code slash-command library.

## PPTX Skills

| Command | Description |
|---|---|
| `/pptx-create <topic>` | Generate a new `.pptx` from a topic or outline |
| `/pptx-read <file.pptx>` | Extract and summarise all slide content |
| `/pptx-edit <file.pptx> -- <instruction>` | Edit slides with plain-English instructions |
| `/pptx-export <file.pptx> [pdf\|png] [dir]` | Export to PDF or per-slide PNGs |

## Dependencies

The PPTX skills rely on:
- **python-pptx** (`pip install python-pptx`) — reading and writing PPTX
- **LibreOffice** (`soffice`) or **unoconv** — PDF/PNG export only

All skills auto-install `python-pptx` on first run if it is not already present.
