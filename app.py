import os
import json
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename

from gemini import extract_text
from parser import parse_text_to_json
from grader import grade_answers
from answer_generator import generate_answer_key   

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    print("hello")

    try:
        # ---------------- STEP 1: OCR ---------------- #
        raw_text = extract_text(filepath)

        if raw_text == "NO_TEXT_EXTRACTED":
            os.remove(filepath)
            return jsonify({
                "error": "Could not extract text properly. Try a clearer image."
            }), 400

        # ---------------- STEP 2: PARSE ---------------- #
        student_data = parse_text_to_json(raw_text)

        """
        EXPECTED FORMAT AFTER PARSER:

        {
          "Q1": {
            "question": "What is photosynthesis?",
            "answer": "Plants make food..."
          }
        }
        """

        # ---------------- STEP 3: SPLIT (SAFE VERSION) ---------------- #
        questions_json = {}
        student_answers = {}

        for qid, data in student_data.items():

            # Case 1: Proper format (dict)
            if isinstance(data, dict):
                questions_json[qid] = data.get("question", "Unknown question")
                student_answers[qid] = data.get("answer", "")

            # Case 2: Parser returned only answer (string)
            elif isinstance(data, str):
                questions_json[qid] = "Unknown question"
                student_answers[qid] = data

            # Case 3: Unexpected format
            else:
                questions_json[qid] = "Unknown question"
                student_answers[qid] = ""

        # ---------------- STEP 4: GENERATE ANSWER KEY ---------------- #
        answer_key = generate_answer_key(questions_json)

        # ---------------- STEP 5: GRADE ---------------- #
        graded_results = grade_answers(student_answers, answer_key)

        # ---------------- CLEANUP ---------------- #
        os.remove(filepath)

        return jsonify({
            "extracted_text": raw_text,
            "questions": questions_json,
            "generated_answer_key": answer_key, 
            "student_answers": student_answers,
            "grading": graded_results
        })

    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)