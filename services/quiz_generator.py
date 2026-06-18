import os
import json
import re
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def fallback_quiz(topic: str):
    return {
        "quiz": [
            {
                "question": f"What is the basic meaning of {topic}?",
                "options": [
                    "A study-related concept",
                    "A movie name",
                    "A song type",
                    "A game cheat"
                ],
                "answer": "A study-related concept"
            }
        ],
        "source": "fallback"
    }


def _extract_difficulty(summary: str) -> str:
    text = summary.lower()

    if "difficulty: hard" in text:
        return "Hard"
    if "difficulty: easy" in text:
        return "Easy"
    if "difficulty: medium" in text:
        return "Medium"

    if "hard" in text:
        return "Hard"
    if "easy" in text:
        return "Easy"

    return "Medium"


def _extract_question_count(summary: str) -> int:
    match = re.search(r"number of questions:\s*(\d+)", summary.lower())
    if match:
        return max(5, min(int(match.group(1)), 30))
    return 5


def generate_quiz_with_gemini(topic: str, summary: str):
    if not GEMINI_API_KEY:
        return fallback_quiz(topic)

    difficulty = _extract_difficulty(summary)
    question_count = _extract_question_count(summary)
    unique_id = datetime.now().strftime("%Y%m%d%H%M%S")

    if difficulty == "Easy":
        difficulty_instruction = """
Create EASY questions:
- Basic definitions
- Simple facts
- Beginner-level wording
- Direct answers
- No tricky options
"""
    elif difficulty == "Medium":
        difficulty_instruction = """
Create MEDIUM questions:
- Application-based questions
- Example-based questions
- Moderate thinking
- Options should be slightly similar
- Avoid very basic definition-only questions
"""
    else:
        difficulty_instruction = """
Create HARD questions:
- Advanced reasoning questions
- Tricky conceptual options
- Deeper understanding
- Scenario-based questions
- Avoid simple definition questions
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    prompt = f"""
You are an academic quiz generator.

Generate a completely NEW quiz.

Unique Quiz ID: {unique_id}
Topic: {topic}
Difficulty: {difficulty}
Number of Questions: {question_count}

Context:
{summary}

{difficulty_instruction}

STRICT RULES:
- Generate exactly {question_count} questions.
- Questions must be study-related only.
- Questions must match ONLY the {difficulty} difficulty level.
- Do NOT generate the same questions for Easy, Medium, and Hard.
- Do NOT use generic repeated questions like "What is the main idea?"
- Every question must be specific to the topic: {topic}.

Return ONLY valid JSON. No markdown.

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
        ],
        "generationConfig": {
            "temperature": 0.9,
            "topP": 0.95,
            "topK": 40
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()

        print("QUIZ GEMINI STATUS:", response.status_code)
        print("DIFFICULTY:", difficulty)
        print("QUESTION COUNT:", question_count)

        if "error" in data or "candidates" not in data:
            return fallback_quiz(topic)

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        text = text.replace("```json", "").replace("```", "").strip()

        result = json.loads(text)

        if "quiz" not in result or not result["quiz"]:
            return fallback_quiz(topic)

        result["source"] = "gemini"
        result["difficulty"] = difficulty
        return result

    except Exception as e:
        print("QUIZ ERROR:", str(e))
        return fallback_quiz(topic)