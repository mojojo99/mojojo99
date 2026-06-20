Create a PowerPoint (.pptx) presentation from a topic or outline.

## Usage
```
/pptx-create <topic or outline>
```

## What this does

1. Parse `$ARGUMENTS` to determine the topic, number of slides, and any structural hints (bullet points, sections, etc.).
2. Install `python-pptx` if not present (`pip install python-pptx`).
3. Write a Python script using `python-pptx` that builds the presentation:
   - Title slide with the main topic and today's date.
   - Content slides (one per major section / bullet point).
   - A closing "Thank You / Q&A" slide.
   - Consistent theme: dark title bar, clean body layout, 24pt body font.
4. Save the file as `<slugified-topic>.pptx` in the current working directory.
5. Print the absolute path of the generated file.

## Example invocations

```
/pptx-create Introduction to Machine Learning
/pptx-create Q3 Sales Review: Revenue, Pipeline, Forecast, Risks
```

## Rules

- Use `python-pptx` exclusively — do not shell out to LibreOffice or Word.
- Each slide must have a title and at least two body bullet points.
- If the argument contains colons or commas, treat each segment as a separate slide section.
- After saving, verify the file exists with `os.path.exists()` and report its size in KB.
