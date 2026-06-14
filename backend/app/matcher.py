from loguru import logger
from backend.app.config import settings
from backend.app.database import get_resume, save_search
from backend.app.vector_store import query_vector_store
from backend.app.analyzer import parse_search_query

def calculate_skills_score(query_skills: list, candidate_skills: list) -> float:
    if not query_skills:
        return 100.0
    if not candidate_skills:
        return 0.0
        
    matches = 0
    c_skills_flat = " ".join(candidate_skills).lower()
    
    for q_skill in query_skills:
        if q_skill.lower() in c_skills_flat:
            matches += 1
            
    return (matches / len(query_skills)) * 100.0

def calculate_experience_score(query_exp: int, candidate_exp: int) -> float:
    if query_exp <= 0:
        return 100.0
    if candidate_exp >= query_exp:
        return 100.0
    if candidate_exp <= 0:
        return 0.0
        
    return (candidate_exp / query_exp) * 100.0

def calculate_projects_score(query_skills: list, candidate_projects: list) -> float:
    if not query_skills:
        return 100.0
    if not candidate_projects:
        return 0.0
        
    matches = 0
    projects_flat = " ".join(candidate_projects).lower()
    
    for q_skill in query_skills:
        if q_skill.lower() in projects_flat:
            matches += 1
            
    return (matches / len(query_skills)) * 100.0

def calculate_certifications_score(query_certs: list, candidate_certs: list) -> float:
    if not query_certs:
        return 100.0
    if not candidate_certs:
        return 0.0
        
    matches = 0
    c_certs_flat = " ".join(candidate_certs).lower()
    
    for q_cert in query_certs:
        if q_cert.lower() in c_certs_flat:
            matches += 1
            
    return (matches / len(query_certs)) * 100.0

def rank_candidates(query_text: str, threshold: float = 40.0) -> list:
    logger.bind(stage="RANK").info(f"Ranking candidates for query: '{query_text}'")
    
    # 1. Retrieve top 100 chunks from vector store
    matched_chunks = query_vector_store(query_text, n_results=100)
    
    # 2. Parse search query using LLM
    parsed_query = parse_search_query(query_text)
    
    # Group matching chunks by candidate doc_id
    candidate_chunks = {}
    for chunk in matched_chunks:
        doc_id = chunk["doc_id"]
        if doc_id not in candidate_chunks:
            candidate_chunks[doc_id] = []
        candidate_chunks[doc_id].append(chunk)
        
    ranked_candidates = []
    
    for doc_id, chunks in candidate_chunks.items():
        # Fetch candidate full profile
        candidate = get_resume(doc_id)
        if not candidate:
            logger.bind(stage="RANK").warning(f"Resume ID {doc_id} found in vector store but missing from SQLite database.")
            continue
            
        # Calculate sub-scores
        
        # a. Skills Match (55%)
        skills_score = calculate_skills_score(parsed_query["skills"], candidate["skills"])
        
        # b. Semantic Score (25%) - take max similarity among candidate's matching chunks
        max_similarity = max(chunk["similarity"] for chunk in chunks)
        # Normalize semantic score to 0 - 100 scale
        semantic_score = max(0.0, min(1.0, max_similarity)) * 100.0
        
        # c. Experience Score (10%)
        experience_score = calculate_experience_score(parsed_query["experience_years"], candidate["experience_years"])
        
        # d. Projects Score (5%)
        projects_score = calculate_projects_score(parsed_query["skills"], candidate["projects"])
        
        # e. Certifications Score (5%)
        certifications_score = calculate_certifications_score(parsed_query["certifications"], candidate["certifications"])
        
        # Total Weighted Score
        total_score = (
            (skills_score * 0.55) +
            (semantic_score * 0.25) +
            (experience_score * 0.10) +
            (projects_score * 0.05) +
            (certifications_score * 0.05)
        )
        
        # Round scores for clean presentation
        total_score = round(total_score, 1)
        skills_score = round(skills_score, 1)
        semantic_score = round(semantic_score, 1)
        experience_score = round(experience_score, 1)
        projects_score = round(projects_score, 1)
        certifications_score = round(certifications_score, 1)
        
        # Log breakdown
        logger.bind(stage="RANK").debug(
            f"Candidate: {candidate['candidate_name']} | "
            f"Total: {total_score} | Skills: {skills_score} | Semantic: {semantic_score} | "
            f"Exp: {experience_score} | Projects: {projects_score} | Certs: {certifications_score}"
        )
        
        # Add explanation object for front-end rendering
        ranked_candidates.append({
            "candidate_id": doc_id,
            "candidate_name": candidate["candidate_name"] or "Unknown Candidate",
            "filename": candidate["filename"],
            "experience_years": candidate["experience_years"],
            "skills": candidate["skills"],
            "education": candidate["education"],
            "certifications": candidate["certifications"],
            "projects": candidate["projects"],
            "upload_time": candidate["upload_time"],
            "total_score": total_score,
            "score_breakdown": {
                "skills_score": skills_score,
                "semantic_score": semantic_score,
                "experience_score": experience_score,
                "projects_score": projects_score,
                "certifications_score": certifications_score
            },
            "summary": candidate["summary"]
        })
        
    # Filter by threshold (40/100 as per specification)
    filtered_candidates = [c for c in ranked_candidates if c["total_score"] >= threshold]
    
    # Sort candidates using weights and tie-breaker:
    # 1. Total Score (descending)
    # 2. Skills Score (descending)
    # 3. Upload Time (descending)
    filtered_candidates.sort(
        key=lambda x: (x["total_score"], x["score_breakdown"]["skills_score"], x["upload_time"]),
        reverse=True
    )
    
    # Log search query
    save_search(query_text, len(filtered_candidates))
    
    logger.bind(stage="RANK").info(f"Found {len(filtered_candidates)} candidates exceeding threshold of {threshold}.")
    return filtered_candidates
