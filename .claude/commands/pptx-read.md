Read and summarise the content of an existing PowerPoint (.pptx) file.

## Usage
```
/pptx-read <path-to-file.pptx>
```

## What this does

1. Resolve `$ARGUMENTS` as the path to a `.pptx` file (absolute or relative to cwd).
2. Install `python-pptx` if not present (`pip install python-pptx`).
3. Open the file with `python_pptx.Presentation` and extract:
   - Total slide count.
   - For every slide: slide number, title, and all text from every shape/text-frame.
   - Speaker notes (if any).
   - Embedded image count per slide.
4. Print a structured Markdown summary:
   - `## Presentation Overview` — file name, slide count, total word count.
   - `## Slide N: <title>` — bullet list of text content for each slide.
   - `## Speaker Notes` — any notes found, keyed by slide number.
5. After printing, offer to answer follow-up questions about the content.

## Example invocations

```
/pptx-read ./deck.pptx
/pptx-read /home/user/documents/Q3_report.pptx
```

## Rules

- Do not modify the file — open it read-only.
- Truncate any single text block longer than 500 characters with `…` and note the full length.
- If the file does not exist, print a clear error and stop.
- Handle password-protected files gracefully: report the protection and exit.
