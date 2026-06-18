import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "ar_study_companion.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            summary TEXT NOT NULL,
            confidence INTEGER,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add user_id column if tables already existed before
    try:
        cursor.execute("ALTER TABLE scan_history ADD COLUMN user_id TEXT DEFAULT 'old_user'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE quiz_history ADD COLUMN user_id TEXT DEFAULT 'old_user'")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def save_scan(user_id, subject, topic, summary, confidence, source):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO scan_history
        (user_id, subject, topic, summary, confidence, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, subject, topic, summary, confidence, source))

    conn.commit()
    conn.close()


def get_scan_history(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM scan_history
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def save_quiz_score(user_id, topic, score, total_questions):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO quiz_history
        (user_id, topic, score, total_questions)
        VALUES (?, ?, ?, ?)
    """, (user_id, topic, score, total_questions))

    conn.commit()
    conn.close()


def get_quiz_history(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM quiz_history
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_analytics(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as total_scans
        FROM scan_history
        WHERE user_id = ?
    """, (user_id,))
    total_scans = cursor.fetchone()["total_scans"]

    cursor.execute("""
        SELECT COUNT(*) as total_quizzes
        FROM quiz_history
        WHERE user_id = ?
    """, (user_id,))
    total_quizzes = cursor.fetchone()["total_quizzes"]

    cursor.execute("""
        SELECT AVG(score * 100.0 / total_questions) as average_score
        FROM quiz_history
        WHERE user_id = ?
    """, (user_id,))
    avg_row = cursor.fetchone()
    average_score = avg_row["average_score"] if avg_row["average_score"] else 0

    cursor.execute("""
        SELECT MAX(score) as best_score
        FROM quiz_history
        WHERE user_id = ?
    """, (user_id,))
    best_row = cursor.fetchone()
    best_score = best_row["best_score"] if best_row["best_score"] else 0

    conn.close()

    return {
        "total_scans": total_scans,
        "total_quizzes": total_quizzes,
        "average_score": round(average_score, 2),
        "best_score": best_score,
    }