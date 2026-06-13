from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import traceback

from backend.app.config import settings
from backend.app.database import (
    init_db, save_resume, delete_resume, get_resume_by_hash,
    list_resumes, get_resume, get_stats, update_resume_summary
)
from backend.app.parser import extract_text, get_file_hash
from backend.app.analyzer import analyze_resume_text, generate_summary
from backend.app.vector_store import index_resume, delete_resume_vectors, collection
from backend.app.matcher import rank_candidates

app = FastAPI(
    title="NexusFDE — Resume Intelligence System Backend",
    version="3.0"
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.bind(stage="REQUEST").info("Starting FastAPI backend...")
    init_db()

class SearchRequest(BaseModel):
    query_text: str

class CompareRequest(BaseModel):
    candidate_ids: list[str]

@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    logger.bind(stage="REQUEST").info(f"Received upload request for file: {file.filename}")
    try:
        # 1. Read bytes
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")
            
        # 2. Check duplicate hash
        file_hash = get_file_hash(file_bytes)
        existing = get_resume_by_hash(file_hash)
        if existing:
            logger.bind(stage="PARSE").info(f"File {file.filename} already indexed (Hash match). Returning existing record.")
            return {
                "status": "already_exists",
                "resume_id": existing["resume_id"],
                "candidate_name": existing["candidate_name"],
                "message": "Resume already exists in the system database."
            }
            
        # 3. Extract raw text
        raw_text = extract_text(file_bytes, file.filename)
        
        # 4. LLM structured analysis
        structured_profile = analyze_resume_text(raw_text)
        candidate_name = structured_profile.get("candidate_name") or "Unknown Candidate"
        
        # 5. Insert candidate record in SQLite
        resume_id = save_resume(
            filename=file.filename,
            resume_hash=file_hash,
            candidate_name=candidate_name,
            experience_years=structured_profile.get("experience_years", 0),
            skills=structured_profile.get("skills", []),
            education=structured_profile.get("education", []),
            certifications=structured_profile.get("certifications", []),
            projects=structured_profile.get("projects", []),
            parse_status="success",
            raw_text=raw_text,
            summary=None  # We will generate summary next
        )
        
        # 6. Index in ChromaDB Vector Store
        index_resume(
            resume_id=resume_id,
            filename=file.filename,
            candidate_name=candidate_name,
            raw_text=raw_text
        )
        
        # 7. Generate Summary (with timeout protection inside the call)
        summary = generate_summary(raw_text, structured_profile)
        update_resume_summary(resume_id, summary)
        
        logger.bind(stage="RESPONSE").info(f"Successfully ingested resume: {file.filename} (ID: {resume_id})")
        return {
            "status": "success",
            "resume_id": resume_id,
            "candidate_name": candidate_name,
            "summary": summary
        }
        
    except ValueError as e:
        logger.bind(stage="RESPONSE").error(f"Value error processing upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.bind(stage="RESPONSE").error(f"Unexpected error processing upload: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Ingestion pipeline failed: {str(e)}")

@app.delete("/resume/{resume_id}")
async def delete_candidate(resume_id: str):
    logger.bind(stage="REQUEST").info(f"Received request to delete resume ID: {resume_id}")
    try:
        # Check if exists
        cand = get_resume(resume_id)
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate not found.")
            
        # Delete from SQLite and ChromaDB
        delete_resume(resume_id)
        delete_resume_vectors(resume_id)
        
        logger.bind(stage="RESPONSE").info(f"Successfully deleted candidate ID: {resume_id}")
        return {"status": "success", "message": f"Successfully deleted candidate {cand['candidate_name']}"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.bind(stage="RESPONSE").error(f"Error deleting candidate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_candidates(req: SearchRequest):
    logger.bind(stage="REQUEST").info(f"Received search request for: '{req.query_text}'")
    try:
        results = rank_candidates(req.query_text)
        
        # Double check and dynamically generate summaries if missing
        for cand in results:
            if not cand["summary"] or "timeout" in cand["summary"].lower():
                logger.bind(stage="LLM").info(f"Summary missing or placeholder for {cand['candidate_name']}, regenerating...")
                # Re-fetch raw text and profile details from database
                db_cand = get_resume(cand["candidate_id"])
                if db_cand:
                    summary = generate_summary(db_cand["raw_text"], db_cand)
                    update_resume_summary(cand["candidate_id"], summary)
                    cand["summary"] = summary
                    
        return {"results": results}
    except Exception as e:
        logger.bind(stage="RESPONSE").error(f"Error matching candidates: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare")
async def compare_candidates(req: CompareRequest):
    logger.bind(stage="REQUEST").info(f"Received compare request for candidates: {req.candidate_ids}")
    try:
        candidates = []
        for cid in req.candidate_ids:
            cand = get_resume(cid)
            if cand:
                candidates.append(cand)
        return {"candidates": candidates}
    except Exception as e:
        logger.bind(stage="RESPONSE").error(f"Error fetching comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resumes")
async def get_all_resumes():
    logger.bind(stage="REQUEST").debug("Received request to list all resumes.")
    try:
        resumes = list_resumes()
        # Remove raw_text to keep payload small
        for r in resumes:
            r.pop("raw_text", None)
        return {"resumes": resumes}
    except Exception as e:
        logger.bind(stage="RESPONSE").error(f"Error listing resumes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard")
async def get_system_dashboard():
    logger.bind(stage="REQUEST").debug("Received request for dashboard stats.")
    try:
        stats = get_stats()
        return stats
    except Exception as e:
        logger.bind(stage="RESPONSE").error(f"Error generating stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    logger.bind(stage="REQUEST").debug("Received health check.")
    sqlite_ok = False
    chroma_ok = False
    ollama_ok = False
    
    # Check SQLite
    try:
        list_resumes()
        sqlite_ok = True
    except Exception as e:
        logger.bind(stage="SYSTEM").error(f"Health check: SQLite error: {e}")
        
    # Check ChromaDB
    try:
        collection.count()
        chroma_ok = True
    except Exception as e:
        logger.bind(stage="SYSTEM").error(f"Health check: ChromaDB error: {e}")
        
    # Check Ollama
    try:
        import httpx
        url = f"{settings.OLLAMA_BASE_URL}/api/tags"
        res = httpx.get(url, timeout=2.0)
        if res.status_code == 200:
            ollama_ok = True
    except Exception as e:
        logger.bind(stage="SYSTEM").error(f"Health check: Ollama error: {e}")
        
    status_code = 200 if (sqlite_ok and chroma_ok and ollama_ok) else 503
    
    return {
        "status": "healthy" if status_code == 200 else "degraded",
        "services": {
            "sqlite": "ok" if sqlite_ok else "failed",
            "chromadb": "ok" if chroma_ok else "failed",
            "ollama": "ok" if ollama_ok else "failed"
        }
    }
