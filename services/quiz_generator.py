import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def fallback_quiz(topic: str):
    return {
        "quiz": [
            {
                "question": f"What is the main idea of {topic}?",
                "options": [
                    "To understand the basic concept",
                    "To delete data",
                    "To damage software",
                    "To avoid learning"
                ],
                "answer": "To understand the basic concept"
            },
            {
                "question": f"Why is {topic} important for students?",
                "options": [
                    "It helps in understanding the subject better",
                    "It is unrelated to studies",
                    "It only works for games",
                    "It has no use"
                ],
                "answer": "It helps in understanding the subject better"
            },
            {
                "question": f"Which method is useful for learning {topic}?",
                "options": [
                    "Reading notes and practicing questions",
                    "Ignoring the topic",
                    "Skipping revision",
                    "Guessing randomly"
                ],
                "answer": "Reading notes and practicing questions"
            },
            {
                "question": f"What should a student do after learning {topic}?",
                "options": [
                    "Revise and take a quiz",
                    "Forget the topic",
                    "Close the app",
                    "Avoid practice"
                ],
                "answer": "Revise and take a quiz"
            },
            {
                "question": f"What does this app help with in {topic}?",
                "options": [
                    "Explanation, revision, and quiz practice",
                    "Only entertainment",
                    "Deleting textbook content",
                    "Blocking learning"
                ],
                "answer": "Explanation, revision, and quiz practice"
            }
        ],
        "source": "fallback"
    }


def generate_quiz_with_gemini(topic: str, summary: str):
    if not GEMINI_API_KEY:
        return fallback_quiz(topic)

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    prompt = f"""
Create 5 multiple choice questions for this topic.

Topic: {topic}
Summary: {summary}

Return ONLY valid JSON. Do not use markdown.

Format:
{{
  "quiz": [
    {{
      "question": "",
      "options": ["", "", "", ""],
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
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()

        print("QUIZ GEMINI STATUS:", response.status_code)
        print("QUIZ GEMINI RESPONSE:", data)

        if "error" in data:
            return fallback_quiz(topic)

        if "candidates" not in data:
            return fallback_quiz(topic)

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        text = text.replace("```json", "").replace("```", "").strip()

        result = json.loads(text)

        if "quiz" not in result or not result["quiz"]:
            return fallback_quiz(topic)

        result["source"] = "gemini"
        return result

    except Exception as e:
        print("QUIZ ERROR:", str(e))
        return fallback_quiz(topic)