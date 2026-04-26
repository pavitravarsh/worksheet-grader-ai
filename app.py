import os
import json
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from gemini import extract_text
from parser import parse_text_to_json
from grader import grade_answers

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load answer key
with open("answer_key.json", "r") as f:
    ANSWER_KEY = json.load(f)

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
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # 1. Extract raw text
            raw_text = extract_text(filepath)
            
            if raw_text == "NO_TEXT_EXTRACTED":
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({"error": "Could not extract text properly. Try a clearer image."}), 400
                
            # 2. Parse to structured JSON
            student_answers = parse_text_to_json(raw_text)
            
            # 3. Grade the answers
            graded_results = grade_answers(student_answers, ANSWER_KEY)
            
            # Cleanup uploaded file
            os.remove(filepath)
            
            return jsonify({
                "extracted_text": raw_text,
                "student_answers": student_answers,
                "grading": graded_results
            })
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
