import os
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def ask_ai_tutor(question: str, language: str):
    if not GEMINI_API_KEY:
        return {
            "answer": "Gemini API key is missing.",
            "source": "error",
        }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    prompt = f"""
You are an AI study tutor for students.

Answer the question clearly and simply.
Use the selected language: {language}.
If the question is academic, explain with examples.
Keep the answer student-friendly.

Question:
{question}
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
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()

        if "error" in data:
            error_message = data["error"].get("message", "Gemini error")

            if (
                "high demand" in error_message.lower()
                or "overloaded" in error_message.lower()
                or "quota" in error_message.lower()
            ):
                return {
                    "answer": "AI Tutor is busy right now due to high demand. Please try again in a few seconds.",
                    "source": "gemini-busy",
                }

            return {
                "answer": error_message,
                "source": "gemini-error",
            }

        answer = data["candidates"][0]["content"]["parts"][0]["text"]

        return {
            "answer": answer,
            "source": "gemini",
        }

    except Exception as e:
        return {
            "answer": f"AI Tutor connection error: {str(e)}",
            "source": "error",
        }