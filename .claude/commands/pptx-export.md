Export a PowerPoint (.pptx) file to PDF or PNG images.

## Usage
```
/pptx-export <path-to-file.pptx> [pdf|png] [output-dir]
```

## What this does

1. Parse `$ARGUMENTS`:
   - Arg 1: path to the `.pptx` source file.
   - Arg 2 (optional): format — `pdf` (default) or `png`.
   - Arg 3 (optional): output directory (defaults to the same directory as the source file).

### PDF export
2. Check for LibreOffice (`soffice`): `which soffice`.
3. If found, run:
   ```
   soffice --headless --convert-to pdf --outdir <output-dir> <file.pptx>
   ```
4. If LibreOffice is not available, try `unoconv`:
   ```
   unoconv -f pdf -o <output-dir> <file.pptx>
   ```
5. Print the path of the generated PDF.

### PNG export (one image per slide)
6. Check for LibreOffice and `convert` (ImageMagick).
7. Export to PDF first (step 3–4), then split to PNGs at 150 dpi:
   ```
   convert -density 150 file.pdf -quality 90 slide-%02d.png
   ```
8. Print the list of generated PNG paths.

## Example invocations

```
/pptx-export ./deck.pptx
/pptx-export ./deck.pptx pdf ./exports/
/pptx-export ./deck.pptx png ./slides/
```

## Rules

- Never modify the source `.pptx` file.
- If neither LibreOffice nor unoconv is available, print clear installation instructions and exit.
- Report the file size of each exported artifact.
- If exporting PNG and the slide count exceeds 50, warn the user before proceeding (large output).
