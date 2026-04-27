import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

CACHE_FILE = "answer_cache.json"


# ---------------- CACHE ---------------- #

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


# ---------------- CORE GENERATION ---------------- #

def generate_answer_and_keywords(question, retries=2):
    prompt = f"""
You are a school teacher generating an answer key.

For each question:
1. Provide a concise correct answer (2–3 lines)
2. Extract 3–5 important keywords

Rules:
- Keep answer simple and accurate
- Keywords must be meaningful (not filler words)

Return STRICT JSON:
{{
  "answer": "text",
  "keywords": ["k1", "k2", "k3"]
}}

Question:
{question}
"""

    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )

            text = response.choices[0].message.content.strip()

            # -------- CLEANUP -------- #
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]

            if text.endswith("```"):
                text = text[:-3]

            text = text.strip()

            # -------- SAFE JSON PARSE -------- #
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                print("JSON parse failed. Raw output:")
                print(text)

                # fallback: still return usable output
                return {
                    "answer": text,
                    "keywords": []
                }

        except Exception as e:
            print(f"Attempt {attempt+1} failed for question: {question}")
            print(f"Error: {e}")

            if attempt < retries:
                time.sleep(3)  # retry delay
            else:
                return {
                    "answer": "Error generating answer",
                    "keywords": []
                }


# ---------------- MAIN PIPELINE ---------------- #

def generate_answer_key(questions_json):
    cache = load_cache()
    answer_key = {}

    for qid, question in questions_json.items():

        if question in cache:
            print(f"⚡ Using cache for: {question}")
            result = cache[question]
        else:
            result = generate_answer_and_keywords(question)
            cache[question] = result

        answer_key[qid] = result

    save_cache(cache)
    return answer_key