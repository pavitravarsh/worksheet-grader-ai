# AI Worksheet Grader

A lightweight Flask app for grading handwritten worksheet answers using AI.

## Project Overview

This project accepts a handwritten worksheet image or PDF, extracts the text using the Gemini model, parses the answers into structured question entries, and grades them against an answer key.

## Architecture

- `app.py` - main Flask app, upload handling, validation, grading workflow, PDF report generation
- `gemini.py` - OCR extraction from images and PDF pages using OpenRouter
- `parser.py` - structured answer parsing from raw text with a local heuristic fallback
- `grader.py` - grading prompt logic and response normalization
- `templates/index.html` - front-end user interface
- `static/style.css` - responsive card-based layout and styling
- `tests/` - basic parser and grader tests
- `answer_key.json` - answer key used for comparison
- `.env` - environment variables (API key)

## Flow Diagram (text-based)

1. User uploads JPG / PNG / PDF
2. `app.py` saves file and validates type
3. `gemini.py` extracts handwritten text
4. `parser.py` converts text to `Q1`, `Q2`, ... JSON
5. `grader.py` grades answers and returns structured feedback
6. `app.py` returns grading results and PDF report
7. Frontend displays question cards, score, feedback, and download link

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Add API key in `.env`:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```
4. Run the app:
   ```bash
   python app.py
   ```
5. Open `http://127.0.0.1:5000` in a browser.

## Sample Input / Output

- Input: scanned or photographed handwritten worksheet in JPG, PNG, or PDF format.
- Output:
  - `grading` JSON with keys like `Q1`, `Q2`, score, feedback, missing concepts
  - total score
  - downloadable PDF grading report

## Limitations

- Handwriting accuracy depends on the OCR model ability.
- Complex answer structures may require clearer handwriting.
- The grader prompt relies on the AI response format, which is normalized but may still fail on unexpected outputs.

## Future Improvements

- Add a confidence score for OCR extraction.
- Store report history for each upload.
- Support batch grading of multiple student files.
- Add a settings page for custom rubrics and answer keys.

## Testing

Run tests using Python:

```bash
python -m unittest discover tests
```
