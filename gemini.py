import os
import fitz  # PyMuPDF
from PIL import Image
import base64
from io import BytesIO
from openai import OpenAI
from dotenv import load_dotenv
import time

# Load .env
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
print("OPENROUTER API KEY LOADED:", "YES" if API_KEY else "NO")  # debug

# Configure OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

def image_to_base64(img: Image.Image) -> str:
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def extract_text(file_path):
    """
    Extract handwritten text from image or PDF using OpenRouter (Google Gemini model)
    """
    prompt = "Extract all readable handwritten text clearly. Maintain structure. Separate answers like Q1, Q2 if possible."

    images = []

    # If PDF → convert pages to images
    if file_path.lower().endswith(".pdf"):
        doc = fitz.open(file_path)

        for page in doc:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)

        doc.close()

    # If image
    else:
        img = Image.open(file_path).convert("RGB")
        images.append(img)

    # OpenAI format expects content like this
    content = [{"type": "text", "text": prompt}]

    for img in images:
        base64_image = image_to_base64(img)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })

    try:
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ],
            max_tokens=4000
        )
    except Exception as e:
        if "429" in str(e):
            print("Quota exceeded, retrying after 8 seconds...")
            time.sleep(8)
            response = client.chat.completions.create(
                model="google/gemini-2.5-flash",
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=4000
            )
        else:
            raise e
            
    if not response or not response.choices or not response.choices[0].message.content:
        return "NO_TEXT_EXTRACTED"
        
    extracted_text = response.choices[0].message.content
    print("Extracted Text:", extracted_text)
    return extracted_text