import sqlite3
import json
from datetime import datetime
import uuid
from backend.app.config import sqlite_db_abs, logger

def get_connection():
    conn = sqlite3.connect(str(sqlite_db_abs))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    logger.bind(stage="DATABASE").info("Initializing SQLite database tables...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create resumes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        resume_id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        candidate_name TEXT,
        experience_years INTEGER,
        skills TEXT,
        education TEXT,
        certifications TEXT,
        projects TEXT,
        upload_time TEXT NOT NULL,
        parse_status TEXT NOT NULL,
        resume_hash TEXT UNIQUE NOT NULL,
        raw_text TEXT,
        summary TEXT
    )
    """)
    
    # Create searches table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS searches (
        search_id TEXT PRIMARY KEY,
        query TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        results_count INTEGER NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()
    logger.bind(stage="DATABASE").info("Database tables initialized successfully.")

def save_resume(
    filename: str,
    resume_hash: str,
    candidate_name: str = None,
    experience_years: int = 0,
    skills: list = None,
    education: list = None,
    certifications: list = None,
    projects: list = None,
    parse_status: str = "pending",
    raw_text: str = "",
    summary: str = None,
    resume_id: str = None
) -> str:
    if not resume_id:
        resume_id = str(uuid.uuid4())
        
    conn = get_connection()
    cursor = conn.cursor()
    upload_time = datetime.utcnow().isoformat()
    
    skills_json = json.dumps(skills or [])
    edu_json = json.dumps(education or [])
    certs_json = json.dumps(certifications or [])
    projs_json = json.dumps(projects or [])
    
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO resumes (
                resume_id, filename, candidate_name, experience_years, 
                skills, education, certifications, projects, 
                upload_time, parse_status, resume_hash, raw_text, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resume_id, filename, candidate_name, experience_years,
                skills_json, edu_json, certs_json, projs_json,
                upload_time, parse_status, resume_hash, raw_text, summary
            )
        )
        conn.commit()
        logger.bind(stage="DATABASE").info(f"Saved resume {filename} as ID {resume_id}")
        return resume_id
    except sqlite3.IntegrityError as e:
        logger.bind(stage="DATABASE").error(f"Failed to save resume: Hash constraint failed or integrity issue: {e}")
        raise e
    finally:
        conn.close()

def delete_resume(resume_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM resumes WHERE resume_id = ?", (resume_id,))
        conn.commit()
        logger.bind(stage="DATABASE").info(f"Deleted resume ID {resume_id} from SQLite.")
    finally:
        conn.close()

def get_resume(resume_id: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM resumes WHERE resume_id = ?", (resume_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        res = dict(row)
        res["skills"] = json.loads(res["skills"] or "[]")
        res["education"] = json.loads(res["education"] or "[]")
        res["certifications"] = json.loads(res["certifications"] or "[]")
        res["projects"] = json.loads(res["projects"] or "[]")
        return res
    finally:
        conn.close()

def get_resume_by_hash(resume_hash: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM resumes WHERE resume_hash = ?", (resume_hash,))
        row = cursor.fetchone()
        if not row:
            return None
        
        res = dict(row)
        res["skills"] = json.loads(res["skills"] or "[]")
        res["education"] = json.loads(res["education"] or "[]")
        res["certifications"] = json.loads(res["certifications"] or "[]")
        res["projects"] = json.loads(res["projects"] or "[]")
        return res
    finally:
        conn.close()

def list_resumes() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM resumes ORDER BY upload_time DESC")
        rows = cursor.fetchall()
        res_list = []
        for r in rows:
            res = dict(r)
            res["skills"] = json.loads(res["skills"] or "[]")
            res["education"] = json.loads(res["education"] or "[]")
            res["certifications"] = json.loads(res["certifications"] or "[]")
            res["projects"] = json.loads(res["projects"] or "[]")
            res_list.append(res)
        return res_list
    finally:
        conn.close()

def update_resume_summary(resume_id: str, summary: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE resumes SET summary = ? WHERE resume_id = ?", (summary, resume_id))
        conn.commit()
        logger.bind(stage="DATABASE").info(f"Updated summary for resume ID {resume_id}")
    finally:
        conn.close()

def save_search(query: str, results_count: int) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    search_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    try:
        cursor.execute(
            "INSERT INTO searches (search_id, query, timestamp, results_count) VALUES (?, ?, ?, ?)",
            (search_id, query, timestamp, results_count)
        )
        conn.commit()
        logger.bind(stage="DATABASE").debug(f"Logged search query: '{query}'")
        return search_id
    finally:
        conn.close()

def get_stats() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Total resumes
        cursor.execute("SELECT COUNT(*) FROM resumes")
        total_resumes = cursor.fetchone()[0]
        
        # Parse statuses
        cursor.execute("SELECT parse_status, COUNT(*) FROM resumes GROUP BY parse_status")
        status_counts = {r[0]: r[1] for r in cursor.fetchall()}
        
        # Avg experience
        cursor.execute("SELECT AVG(experience_years) FROM resumes WHERE parse_status = 'success'")
        avg_exp_row = cursor.fetchone()
        avg_experience = round(avg_exp_row[0], 1) if avg_exp_row and avg_exp_row[0] is not None else 0.0
        
        # Top skills aggregation
        cursor.execute("SELECT skills FROM resumes WHERE parse_status = 'success'")
        all_skills = []
        for r in cursor.fetchall():
            skills_list = json.loads(r[0] or "[]")
            all_skills.extend([s.lower().strip() for s in skills_list if s.strip()])
            
        from collections import Counter
        top_skills = dict(Counter(all_skills).most_common(10))
        
        # Recent searches
        cursor.execute("SELECT query, timestamp FROM searches ORDER BY timestamp DESC LIMIT 5")
        recent_searches = [dict(r) for r in cursor.fetchall()]
        
        return {
            "total_resumes": total_resumes,
            "status_counts": status_counts,
            "average_experience": avg_experience,
            "top_skills": top_skills,
            "recent_searches": recent_searches
        }
    finally:
        conn.close()
