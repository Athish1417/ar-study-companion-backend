import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def ask_gemini_for_topic(ocr_text: str):
    if not GEMINI_API_KEY:
        return {
            "subject": "Unknown",
            "topic": "API Key Missing",
            "summary": "Gemini API key is not configured in .env file.",
            "confidence": 0,
            "source": "error"
        }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
         f"gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}"
    )

    prompt = f"""
Analyze the following OCR text from a student's textbook or notes.

Return ONLY valid JSON. Do not use markdown.

OCR Text:
{ocr_text}

JSON format:
{{
  "subject": "subject name",
  "topic": "topic name",
  "summary": "short simple explanation",
  "confidence": 85
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
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()

        print("GEMINI STATUS:", response.status_code)
        print("GEMINI RESPONSE:", data)

        if "error" in data:
            return {
                "subject": "Unknown",
                "topic": "Gemini API Error",
                "summary": data["error"].get("message", "Unknown Gemini error"),
                "confidence": 0,
                "source": "gemini-error"
            }

        if "candidates" not in data:
            return {
                "subject": "Unknown",
                "topic": "No Gemini Candidates",
                "summary": "Gemini did not return a valid candidate response.",
                "confidence": 0,
                "source": "gemini-error"
            }

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        text = text.replace("```json", "").replace("```", "").strip()

        result = json.loads(text)

        return {
            "subject": result.get("subject", "Unknown"),
            "topic": result.get("topic", "Unknown Topic"),
            "summary": result.get("summary", "No summary available."),
            "confidence": int(result.get("confidence", 70)),
            "source": "gemini"
        }

    except Exception as e:
        print("GEMINI EXCEPTION:", str(e))

        return {
            "subject": "Unknown",
            "topic": "Gemini Error",
            "summary": f"Could not process with Gemini: {str(e)}",
            "confidence": 0,
            "source": "error"
        }