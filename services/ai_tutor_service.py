import os
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def _is_greeting(question: str):
    text = question.lower().strip()
    greetings = [
        "hi", "hello", "hey", "hii", "hiii",
        "good morning", "good afternoon", "good evening",
        "namaste"
    ]
    return text in greetings


def _study_prompt(language: str, question: str):
    return f"""
You are an AI Study Tutor inside an AR Study Companion app.

STRICT RULES:
1. You may reply normally to greetings.
2. You must answer only study-related and academic questions.
3. Study-related means school subjects, college subjects, graduation topics, programming, exams, projects, assignments, research, career learning, and academic concepts.
4. Do not answer movies, songs, celebrities, entertainment, dating, jokes, gaming, gossip, sports, or random personal topics.

If the input is not study-related, reply only:
"I can only help with study-related topics. Please ask a subject, chapter, concept, or academic doubt."

Use the selected language: {language}.
Explain clearly and simply with examples when useful.

Student question:
{question}
"""


def _handle_gemini_response(data):
    if "error" in data:
        error_message = data["error"].get("message", "Gemini error")

        if (
            "high demand" in error_message.lower()
            or "overloaded" in error_message.lower()
            or "quota" in error_message.lower()
        ):
            return {
               "answer": f"Gemini real error: {error_message}",
                "source": "gemini-busy",
            }

        return {
            "answer": error_message,
            "source": "gemini-error",
        }

    try:
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
        return {
            "answer": answer,
            "source": "gemini",
        }
    except Exception:
        return {
            "answer": "AI Tutor could not read the response. Please try again.",
            "source": "error",
        }


def ask_ai_tutor(question: str, language: str):
    if _is_greeting(question):
        return {
            "answer": "Hello! I am your AI Study Tutor. Ask me any study-related question.",
            "source": "greeting",
        }

    if not GEMINI_API_KEY:
        return {
            "answer": "Gemini API key is missing.",
            "source": "error",
        }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    prompt = _study_prompt(language, question)

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
        return _handle_gemini_response(data)

    except Exception as e:
        return {
            "answer": f"AI Tutor connection error: {str(e)}",
            "source": "error",
        }


def ask_ai_tutor_with_image(
    question: str,
    language: str,
    image_base64: str,
    mime_type: str = "image/jpeg",
):
    if not GEMINI_API_KEY:
        return {
            "answer": "Gemini API key is missing.",
            "source": "error",
        }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    if not question.strip():
        question = "Analyze this image and explain the study content clearly."

    prompt = _study_prompt(
        language,
        f"""
The student uploaded an image.

Analyze the image directly.
If it is a textbook page, notes, diagram, chart, question paper, or study material:
- identify the topic
- explain it clearly
- answer any visible academic question if present
- keep it student-friendly

Student instruction:
{question}
""",
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_base64,
                        }
                    },
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=45)
        data = response.json()
        return _handle_gemini_response(data)

    except Exception as e:
        return {
            "answer": f"AI Tutor image analysis error: {str(e)}",
            "source": "error",
        }