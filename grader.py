import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def grade_answers(student_answers_json, answer_key_json, retries=2):
    """
    Semantic grading with fallback safety
    """

    # SAFETY: ensure non-empty answers
    for qid in student_answers_json:
        if not student_answers_json[qid] or len(student_answers_json[qid].strip()) < 10:
            print(f"Empty/weak answer detected for {qid}, using fallback")
            student_answers_json[qid] = "No meaningful answer provided."

    prompt = f"""
You are an expert evaluator.

IMPORTANT:
- Accept different wording if concept is correct
- Focus on meaning, not exact keywords
- Use keywords only as guidance

CRITICAL:
- Answers may include explanation + steps → treat as ONE answer
- Do NOT penalize for formatting differences

SCORING RULES:
- Full explanation with steps → 4–5 marks
- Partial but correct → 3–4 marks
- Minimal → 1–2 marks
- Empty/irrelevant → 0

Student Answers:
{json.dumps(student_answers_json, indent=2)}

Answer Key:
{json.dumps(answer_key_json, indent=2)}

Return STRICT JSON:
{{
  "Q1": {{
    "score": 4,
    "confidence": 0.85,
    "feedback": "Reason",
    "missing_points": []
  }},
  "total_score": 4
}}

Rules:
- Only JSON
- No markdown
"""

    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=4000
            )

            text = response.choices[0].message.content.strip()

            # cleanup
            if text.startswith("```"):
                text = text.split("```")[1]
            if text.endswith("```"):
                text = text[:-3]

            text = text.strip()

            try:
                data = json.loads(text)

                # ensure total score
                if "total_score" not in data:
                    total = sum(
                        v.get("score", 0)
                        for k, v in data.items()
                        if k.startswith("Q")
                    )
                    data["total_score"] = total

                return data

            except:
                print("Grader JSON failed:")
                print(text)

        except Exception as e:
            print(f"Grader error: {e}")
            time.sleep(3)

    return {
        "error": "Grading failed"
    }