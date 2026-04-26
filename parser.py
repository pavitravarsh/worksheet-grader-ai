import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def parse_text_to_json(raw_text):
    """
    Converts raw extracted text into structured JSON using OpenRouter.
    """
    prompt = f"""
Convert the following extracted handwritten text into a structured JSON format where keys are the question numbers (e.g., "Q1", "Q2") and values are the corresponding answers.
Do not include any markdown formatting like ```json or extra text, just return the raw JSON object.

Extracted Text:
{raw_text}
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
            print("Quota exceeded in parser, retrying after 8 seconds...")
            time.sleep(8)
            response = client.chat.completions.create(
                model="google/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000
            )
        else:
            raise e
            
    response_text = response.choices[0].message.content.strip()
    
    # Cleanup markdown if model returns it despite instructions
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    elif response_text.startswith("```"):
        response_text = response_text[3:]
        
    if response_text.endswith("```"):
        response_text = response_text[:-3]
        
    return json.loads(response_text.strip())
