import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def generate_flashcards(topic: str, summary: str):
    if not GEMINI_API_KEY:
        return {
            "flashcards": []
        }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    )

    prompt = f"""
You are an educational flashcard generator.

Topic:
{topic}

Summary:
{summary}

Create exactly 10 flashcards.

Rules:
- Study related only
- Short question
- Short answer
- Easy to revise
- Suitable for students

Return ONLY JSON.

Format:

{{
  "flashcards": [
    {{
      "question": "",
      "answer": ""
    }}
  ]
}}
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=30,
        )

        data = response.json()

        if "error" in data:
            return {"flashcards": []}

        text = data["candidates"][0]["content"]["parts"][0]["text"]

        text = (
            text.replace("```json", "")
            .replace("```", "")
            .strip()
        )

        result = json.loads(text)

        if "flashcards" not in result:
            return {"flashcards": []}

        return result

    except Exception as e:
        print("FLASHCARD ERROR:", e)
        return {"flashcards": []}