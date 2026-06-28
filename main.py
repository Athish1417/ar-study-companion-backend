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
    save_flashcards,
    get_flashcard_history,
    get_flashcards_by_id,

    create_community_post,
    get_community_posts,
    create_community_reply,
    get_community_replies,
    report_community_post,
    report_community_reply,
    create_or_update_user,
    get_user_profile,
    update_username,
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
    
class SaveFlashcardsRequest(BaseModel):
    user_id: str
    topic: str
    summary: str
    flashcards: list

class CommunityPostRequest(BaseModel):
    user_id: str
    username: str
    subject: str
    title: str
    description: str


class CommunityReplyRequest(BaseModel):
    post_id: int
    user_id: str
    username: str
    reply: str


class CommunityReportRequest(BaseModel):
    reported_by: str
    reason: str

class FlashcardHistoryRequest(BaseModel):
    user_id: str
    
class UserProfileRequest(BaseModel):
    user_id: str
    username: str
    email: str

class UpdateUsernameRequest(BaseModel):
    user_id: str
    username: str


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
    print("MAIN ROUTE HIT:", request.question)

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
    
@app.post("/save-flashcards")
def save_flashcards_api(request: SaveFlashcardsRequest):
    save_flashcards(
        request.user_id,
        request.topic,
        request.summary,
        request.flashcards,
    )

    return {
        "message": "Flashcards saved successfully"
    }


@app.get("/flashcard-history/{user_id}")
def flashcard_history_api(user_id: str):
    return {
        "history": get_flashcard_history(user_id)
    }


@app.get("/flashcards/{user_id}/{flashcard_id}")
def flashcards_by_id_api(
    user_id: str,
    flashcard_id: int,
):
    return get_flashcards_by_id(
        user_id,
        flashcard_id,
    )
    
@app.post("/community/posts")
def create_post(request: CommunityPostRequest):
    create_community_post(
        request.user_id,
        request.username,
        request.subject,
        request.title,
        request.description,
    )

    return {
        "message": "Post created successfully"
    }


@app.get("/community/posts")
def get_posts():
    return {
        "posts": get_community_posts()
    }


@app.post("/community/replies")
def create_reply(request: CommunityReplyRequest):
    create_community_reply(
        request.post_id,
        request.user_id,
        request.username,
        request.reply,
    )

    return {
        "message": "Reply added"
    }


@app.get("/community/replies/{post_id}")
def get_replies(post_id: int):
    return {
        "replies": get_community_replies(post_id)
    }


@app.post("/community/report/post/{post_id}")
def report_post(
    post_id: int,
    request: CommunityReportRequest,
):
    report_community_post(
        post_id,
        request.reported_by,
        request.reason,
    )

    return {
        "message": "Post reported successfully"
    }


@app.post("/community/report/reply/{reply_id}")
def report_reply(
    reply_id: int,
    request: CommunityReportRequest,
):
    report_community_reply(
        reply_id,
        request.reported_by,
        request.reason,
    )

    return {
        "message": "Reply reported successfully"
    }

@app.post("/set-username")
def set_username(request: UserProfileRequest):
    return create_or_update_user(
        request.user_id,
        request.username,
        request.email,
    )

@app.post("/update-username")
def update_username_api(request: UpdateUsernameRequest):
        return update_username(
          request.user_id,
          request.username,
    )

@app.get("/user-profile/{user_id}")
def user_profile(user_id: str):
    profile = get_user_profile(user_id)

    if profile is None:
        return {
            "exists": False,
            "profile": None,
        }

    return {
        "exists": True,
        "profile": profile,
    }
    
    