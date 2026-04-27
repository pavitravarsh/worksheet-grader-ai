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


def parse_text_to_json(raw_text):
    """
    Converts raw extracted text into structured JSON:
    {
      "Q1": {
        "question": "...",
        "answer": "..."
      }
    }
    """

    prompt = f"""
You are an expert in reading student answer sheets.

IMPORTANT:
- A single answer may contain paragraphs, steps, diagrams
- Do NOT split answers based on formatting (like bullet points or numbering)
- Merge all related content into ONE answer

Return STRICT JSON:
{{
  "Q1": {{
    "question": "Full question text",
    "answer": "Complete answer including all parts"
  }}
}}

Rules:
- Always include BOTH "question" and "answer"
- Do NOT create empty answers
- If question is unclear, still include full answer
- Do NOT include markdown

Extracted Text:
{raw_text}
"""

    for attempt in range(2):
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

                # validate
                for qid, val in data.items():
                    if not isinstance(val, dict):
                        raise ValueError("Invalid format")
                    if "answer" not in val:
                        raise ValueError("Missing answer")

                return data

            except Exception:
                print("Parser JSON failed, raw:")
                print(text)

        except Exception as e:
            print(f"Parser error: {e}")
            time.sleep(3)

    # FALLBACK 
    print("Using fallback parser")
    return {
        "Q1": {
            "question": "Unknown question",
            "answer": raw_text
        }
    }