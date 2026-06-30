import os
import json
import re
import random
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


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
    match = re.search(r"number of questions:\s*(\d+)", summary.lower())
    if match:
        return max(5, min(int(match.group(1)), 30))
    return 5


def fallback_quiz(topic: str, difficulty: str = "Medium", count: int = 5):
    easy = [
        f"What is {topic} mainly about?",
        f"Which statement best describes {topic}?",
        f"Why do students learn {topic}?",
        f"What is the basic use of {topic}?",
        f"Which is a simple example related to {topic}?",
        f"What should you understand first in {topic}?",
    ]

    medium = [
        f"How can {topic} be applied in a real example?",
        f"Which situation best shows the use of {topic}?",
        f"What happens if a learner misunderstands {topic}?",
        f"How is {topic} connected to other concepts?",
        f"Which option shows correct practical use of {topic}?",
        f"What is the best way to revise {topic} effectively?",
    ]

    hard = [
        f"Which deeper concept is most important in {topic}?",
        f"What is a tricky misunderstanding about {topic}?",
        f"Which option requires reasoning about {topic}?",
        f"How would you solve an advanced problem in {topic}?",
        f"Which statement is most accurate for advanced {topic}?",
        f"What conclusion can be drawn from a complex case of {topic}?",
    ]

    pool = easy if difficulty == "Easy" else hard if difficulty == "Hard" else medium
    random.shuffle(pool)

    quiz = []
    for question in pool[:count]:
        quiz.append({
            "question": question,
            "options": [
                "The correct study-related explanation",
                "An unrelated entertainment idea",
                "A random guess without logic",
                "A wrong and confusing answer",
            ],
            "answer": "The correct study-related explanation",
        })

    return {
        "quiz": quiz,
        "source": "fallback",
        "difficulty": difficulty,
    }


def generate_quiz_with_gemini(topic: str, summary: str):
    difficulty = _extract_difficulty(summary)
    question_count = _extract_question_count(summary)
    unique_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))

    if not GEMINI_API_KEY:
        return fallback_quiz(topic, difficulty, question_count)

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    prompt = f"""
You are a strict academic quiz generator.

Create EXACTLY {question_count} NEW multiple choice questions.

Unique Quiz ID: {unique_id}
Topic: {topic}
Difficulty: {difficulty}

Context:
{summary}

Rules:
- Every quiz attempt must generate new questions.
- Do not repeat previous/common questions.
- Do not ask generic questions like "What is the main idea?"
- All questions must be specific to: {topic}
- Return only study-related questions.
- Create exactly 4 options for each question.
- The answer must exactly match one of the options.

Difficulty style:
Easy = simple, basic, definition-level, beginner-friendly.
Medium = application-based, example-based, moderate thinking.
Hard = advanced reasoning, tricky concepts, deeper understanding.

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
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 1.0,
            "topP": 0.95,
            "topK": 40,
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()

        print("QUIZ GEMINI STATUS:", response.status_code)
        print("DIFFICULTY:", difficulty)
        print("QUESTION COUNT:", question_count)

        if "error" in data or "candidates" not in data:
            return fallback_quiz(topic, difficulty, question_count)

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        text = text.replace("```json", "").replace("```", "").strip()

        result = json.loads(text)
        quiz = result.get("quiz", [])

        if not quiz or len(quiz) < question_count:
            return fallback_quiz(topic, difficulty, question_count)

        random.shuffle(quiz)

        return {
            "quiz": quiz[:question_count],
            "source": "gemini",
            "difficulty": difficulty,
        }

    except Exception as e:
        print("QUIZ ERROR:", str(e))
        return fallback_quiz(topic, difficulty, question_count)