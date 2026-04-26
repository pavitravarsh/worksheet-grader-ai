import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def grade_answers(student_answers_json, answer_key_json):
    """
    Semantically grades student answers against the answer key using a rubric.
    """
    prompt = f"""
You are an expert evaluator. Compare the student's answers with the correct answer key. 
Do not use exact keyword matching. Evaluate meaning based on the following rubric:
1. Concept Correctness: Is the core idea right?
2. Key Terms: Did they use appropriate terminology?
3. Explanation Depth: Is the explanation sufficient?

Student Answers:
{json.dumps(student_answers_json)}

Correct Answer Key:
{json.dumps(answer_key_json)}

For each question present in the student answers, assign a score out of 5 based on the rubric.

Return a JSON object strictly following this structure:
{{
  "Q1": {{
    "score": 4,
    "feedback": "Explain why they got this score based on the rubric",
    "missing_points": ["missing point 1", "missing point 2"]
  }},
  "total_score": <sum of all scores>
}}

Do not include any markdown formatting like ```json, just return the raw JSON string.
"""
    try:
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000
        )
    except Exception as e:
        import time
        if "429" in str(e):
            print("Quota exceeded in grader, retrying after 8 seconds...")
            time.sleep(8)
            response = client.chat.completions.create(
                model="google/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000
            )
        else:
            raise e
            
    response_text = response.choices[0].message.content.strip()
    
    # Cleanup markdown if model returns it
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    elif response_text.startswith("```"):
        response_text = response_text[3:]
        
    if response_text.endswith("```"):
        response_text = response_text[:-3]
        
    return json.loads(response_text.strip())
