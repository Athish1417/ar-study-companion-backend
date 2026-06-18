import os
import json
import re
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
                    "To avoid learning",
                ],
                "answer": "To understand the basic concept",
            },
            {
                "question": f"Why is {topic} important for students?",
                "options": [
                    "It helps in understanding the subject better",
                    "It is unrelated to studies",
                    "It only works for games",
                    "It has no use",
                ],
                "answer": "It helps in understanding the subject better",
            },
            {
                "question": f"Which method is useful for learning {topic}?",
                "options": [
                    "Reading notes and practicing questions",
                    "Ignoring the topic",
                    "Skipping revision",
                    "Guessing randomly",
                ],
                "answer": "Reading notes and practicing questions",
            },
            {
                "question": f"What should a student do after learning {topic}?",
                "options": [
                    "Revise and take a quiz",
                    "Forget the topic",
                    "Close the app",
                    "Avoid practice",
                ],
                "answer": "Revise and take a quiz",
            },
            {
                "question": f"What does this app help with in {topic}?",
                "options": [
                    "Explanation, revision, and quiz practice",
                    "Only entertainment",
                    "Deleting textbook content",
                    "Blocking learning",
                ],
                "answer": "Explanation, revision, and quiz practice",
            },
        ],
        "source": "fallback",
    }


def _extract_difficulty(summary: str) -> str:
    text = summary.lower()

    if "difficulty: hard" in text:
        return "Hard"
    if "difficulty: easy" in text:
        return "Easy"
    if "difficulty: medium" in text:
        return "Medium"
    return "Medium"


def _extract_question_count(summary: str) -> int:
    match = re.search(r"(\d+)\s*(study-related\s*)?questions?", summary.lower())
    if match:
        count = int(match.group(1))
        return max(5, min(count, 30))
    return 5


def generate_quiz_with_gemini(topic: str, summary: str):
    if not GEMINI_API_KEY:
        return fallback_quiz(topic)

    difficulty = _extract_difficulty(summary)
    question_count = _extract_question_count(summary)

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    prompt = f"""
You are an academic quiz generator.

Create exactly {question_count} NEW and UNIQUE multiple choice questions.

The quiz must strongly follow this difficulty: {difficulty}

If Easy: use simple definition-based beginner questions.
If Medium: use application-based questions with moderate thinking.
If Hard: use advanced reasoning and tricky conceptual questions.

Do NOT generate the same questions for Easy, Medium, and Hard.
Do NOT reuse common generic questions.
Each question must be specific to the topic: {topic}.

Topic: {topic}
Context / Summary: {summary}
Difficulty: {difficulty}

STRICT STUDY RULE:
Only generate educational, academic, school, college, exam, programming, science, math, history, geography, English grammar, or study-related questions.
If the topic is not educational, return:
{{"quiz":[]}}

DIFFICULTY RULES:
Easy:
- Ask direct, basic, definition-based questions.
- Use simple wording.
- Options should be clearly different.
- Suitable for beginners.

Medium:
- Ask application-based questions.
- Include moderate thinking.
- Mix definitions, examples, and use-cases.
- Options should need careful reading.

Hard:
- Ask deeper conceptual and reasoning questions.
- Include tricky but fair options.
- Avoid obvious answers.
- Suitable for advanced revision.

IMPORTANT:
Generate questions ONLY at this difficulty level: {difficulty}.
Do not reuse the same question style across different difficulty levels.

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
        result["difficulty"] = difficulty
        result["question_count"] = question_count
        return result

    except Exception as e:
        print("QUIZ ERROR:", str(e))
        return fallback_quiz(topic)