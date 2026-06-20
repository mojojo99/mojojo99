Edit one or more slides in an existing PowerPoint (.pptx) file.

## Usage
```
/pptx-edit <path-to-file.pptx> -- <instruction>
```

## What this does

1. Parse `$ARGUMENTS`:
   - Everything before ` -- ` is the file path.
   - Everything after ` -- ` is the edit instruction in plain English.
2. Install `python-pptx` if not present (`pip install python-pptx`).
3. Interpret the edit instruction and apply the corresponding change using `python-pptx`:

   | Instruction pattern | Action |
   |---|---|
   | `slide N: set title to "..."` | Replace the title placeholder text on slide N. |
   | `slide N: replace "old" with "new"` | Find-and-replace text in all shapes on slide N. |
   | `slide N: add bullet "..."` | Append a bullet to the first content placeholder on slide N. |
   | `slide N: delete` | Remove slide N from the presentation. |
   | `add slide: title "..." body "..."` | Append a new slide at the end. |
   | `replace all "old" with "new"` | Global find-and-replace across every slide. |

4. Save the modified presentation **in place** (overwrite the original file).
5. Print a concise diff of what changed (slide numbers and field names).

## Example invocations

```
/pptx-edit ./deck.pptx -- slide 3: set title to "Updated Roadmap"
/pptx-edit ./deck.pptx -- replace all "Q3" with "Q4"
/pptx-edit ./deck.pptx -- add slide: title "Appendix" body "Additional data available on request."
```

## Rules

- Create a `.bak` copy of the original file before saving (e.g. `deck.pptx.bak`) so changes are reversible.
- If the slide number is out of range, print an error and abort without saving.
- Preserve all existing formatting (fonts, colours, sizes) when replacing text — only update the `text` property of runs, not the paragraph style.
- After saving, run `/pptx-read` logic on the edited slide to confirm the change is reflected.
