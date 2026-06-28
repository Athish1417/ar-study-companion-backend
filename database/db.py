import sqlite3
import json
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flashcard_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            summary TEXT NOT NULL,
            flashcards TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
CREATE TABLE IF NOT EXISTS ats_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    resume_name TEXT NOT NULL,
    job_role TEXT NOT NULL,
    result TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    feedback TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

    try:
        cursor.execute("ALTER TABLE scan_history ADD COLUMN user_id TEXT DEFAULT 'old_user'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE quiz_history ADD COLUMN user_id TEXT DEFAULT 'old_user'")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS community_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        username TEXT NOT NULL,
        subject TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS community_replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id TEXT NOT NULL,
        username TEXT NOT NULL,
        reply TEXT NOT NULL,
        likes INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(post_id) REFERENCES community_posts(id)
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS community_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        reply_id INTEGER,
        reported_by TEXT NOT NULL,
        reason TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL UNIQUE,
        username TEXT NOT NULL UNIQUE,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

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


def save_flashcards(user_id, topic, summary, flashcards):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO flashcard_history
        (user_id, topic, summary, flashcards)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        topic,
        summary,
        json.dumps(flashcards),
    ))

    conn.commit()
    conn.close()


def get_flashcard_history(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, topic, summary, created_at
        FROM flashcard_history
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_flashcards_by_id(user_id, flashcard_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM flashcard_history
        WHERE user_id = ? AND id = ?
    """, (user_id, flashcard_id))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    data = dict(row)
    data["flashcards"] = json.loads(data["flashcards"])
    return data


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
        SELECT COUNT(*) as total_flashcards
        FROM flashcard_history
        WHERE user_id = ?
    """, (user_id,))
    total_flashcards = cursor.fetchone()["total_flashcards"]

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
        "total_flashcards": total_flashcards,
        "average_score": round(average_score, 2),
        "best_score": best_score,
    }
    
def create_community_post(user_id, username, subject, title, description):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO community_posts
        (user_id, username, subject, title, description)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, username, subject, title, description))

    conn.commit()
    conn.close()


def get_community_posts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            p.*,
            (
                SELECT COUNT(*)
                FROM community_replies r
                WHERE r.post_id = p.id
            ) as reply_count
        FROM community_posts p
        ORDER BY p.created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def create_community_reply(post_id, user_id, username, reply):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO community_replies
        (post_id, user_id, username, reply)
        VALUES (?, ?, ?, ?)
    """, (post_id, user_id, username, reply))

    conn.commit()
    conn.close()


def get_community_replies(post_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM community_replies
        WHERE post_id = ?
        ORDER BY created_at ASC
    """, (post_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def report_community_post(post_id, reported_by, reason):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO community_reports
        (post_id, reported_by, reason)
        VALUES (?, ?, ?)
    """, (post_id, reported_by, reason))

    conn.commit()
    conn.close()


def report_community_reply(reply_id, reported_by, reason):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO community_reports
        (reply_id, reported_by, reason)
        VALUES (?, ?, ?)
    """, (reply_id, reported_by, reason))

    conn.commit()
    conn.close()
    
def create_or_update_user(user_id, username, email):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (user_id, username, email)
            VALUES (?, ?, ?)
        """, (user_id, username, email))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Username saved successfully"}

    except sqlite3.IntegrityError:
        conn.close()
        return {"success": False, "message": "Username already exists. Please choose another."}


def get_user_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, username, email, created_at
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)

def username_exists(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM users
        WHERE LOWER(username) = LOWER(?)
    """, (username,))

    exists = cursor.fetchone() is not None

    conn.close()

    return exists


def update_username(user_id, username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET username = ?
        WHERE user_id = ?
    """, (username, user_id))

    conn.commit()
    conn.close()

def username_exists_for_other_user(username, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM users
        WHERE LOWER(username) = LOWER(?)
        AND user_id != ?
    """, (username, user_id))

    exists = cursor.fetchone() is not None

    conn.close()
    return exists


def update_username(user_id, username):
    if username_exists_for_other_user(username, user_id):
        return {
            "success": False,
            "message": "Username already exists. Please choose another."
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET username = ?
        WHERE user_id = ?
    """, (username, user_id))

    conn.commit()
    conn.close()
    
    def save_ats_history(user_id, resume_name, job_role, result):
        conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ats_history
        (user_id, resume_name, job_role, result)
        VALUES (?, ?, ?, ?)
    """, (user_id, resume_name, job_role, result))

    conn.commit()
    conn.close()

def get_ats_history(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM ats_history
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def save_interview_history(user_id, role, feedback):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO interview_history
        (user_id, role, feedback)
        VALUES (?, ?, ?)
    """, (user_id, role, feedback))

    conn.commit()
    conn.close()


def get_interview_history(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM interview_history
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

    return {
        "success": True,
        "message": "Username updated successfully"
    }