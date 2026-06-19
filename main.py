from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import os
from pathlib import Path
from dotenv import load_dotenv
from services.flashcard_generator import generate_flashcards

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

from services.gemini_service import ask_gemini_for_topic
from services.quiz_generator import generate_quiz_with_gemini
from database.db import (
    create_tables,
    save_scan,
    get_scan_history,
    save_quiz_score,
    get_quiz_history,
    get_analytics,
)
from services.ai_tutor_service import (
    ask_ai_tutor,
    ask_ai_tutor_with_image,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()


class OCRRequest(BaseModel):
    ocr_text: str


class FlashcardRequest(BaseModel):
    topic: str
    summary: str

class QuizRequest(BaseModel):
    topic: str
    summary: str


class SaveScanRequest(BaseModel):
    user_id: str
    subject: str
    topic: str
    summary: str
    confidence: int
    source: str


class SaveQuizScoreRequest(BaseModel):
    user_id: str
    topic: str
    score: int
    total_questions: int


class AITutorRequest(BaseModel):
    question: str
    language: str


class AIImageRequest(BaseModel):
    question: str
    language: str
    image_base64: str
    mime_type: str = "image/jpeg"


@app.get("/")
def home():
    return {"message": "AR Study Companion Backend Running"}


@app.post("/detect-topic")
def detect_topic(request: OCRRequest):
    return ask_gemini_for_topic(request.ocr_text)


@app.post("/generate-quiz")
def generate_quiz(request: QuizRequest):
    return generate_quiz_with_gemini(
        request.topic,
        request.summary,
    )


@app.post("/save-scan")
def save_scan_api(request: SaveScanRequest):
    save_scan(
        request.user_id,
        request.subject,
        request.topic,
        request.summary,
        request.confidence,
        request.source,
    )
    return {"message": "Scan saved successfully"}


@app.get("/scan-history/{user_id}")
def scan_history_api(user_id: str):
    return {"history": get_scan_history(user_id)}


@app.post("/save-quiz-score")
def save_quiz_score_api(request: SaveQuizScoreRequest):
    save_quiz_score(
        request.user_id,
        request.topic,
        request.score,
        request.total_questions,
    )
    return {"message": "Quiz score saved successfully"}


@app.get("/quiz-history/{user_id}")
def quiz_history_api(user_id: str):
    return {"history": get_quiz_history(user_id)}


@app.get("/analytics/{user_id}")
def analytics_api(user_id: str):
    return get_analytics(user_id)


@app.post("/ask-ai")
def ask_ai(request: AITutorRequest):
    return ask_ai_tutor(
        request.question,
        request.language,
    )


@app.post("/ask-ai-image")
def ask_ai_image(request: AIImageRequest):
    return ask_ai_tutor_with_image(
        request.question,
        request.language,
        request.image_base64,
        request.mime_type,
    )
    
@app.post("/generate-flashcards")
def generate_flashcards_api(request: FlashcardRequest):
    return generate_flashcards(
        request.topic,
        request.summary,
    )