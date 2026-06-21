from loguru import logger

def calculate_domain_alignment(parsed_query: dict, candidate_skills: list, candidate_experience: int) -> float:
    """
    Calculates a domain alignment score (0-100) based on company rules and preferred skills.
    In a full implementation, this could use an LLM or cross-encoder against the retrieved company rules.
    For this prototype, we'll implement a heuristic based on known company preferences 
    (from company_profile.md: Python, FastAPI, Cloud, Vector Databases, etc.)
    """
    logger.bind(stage="RANK").debug("Calculating domain alignment...")
    
    preferred_skills = ["python", "fastapi", "cloud", "vector db", "chromadb", "pinecone", "llm", "ollama", "langgraph"]
    
    if not candidate_skills:
        return 0.0
        
    c_skills_flat = " ".join(candidate_skills).lower()
    
    matches = 0
    for p_skill in preferred_skills:
        if p_skill in c_skills_flat:
            matches += 1
            
    # Max out at 4 matching preferred skills for full domain alignment score (heuristic)
    skill_alignment = min(1.0, matches / 4.0) * 100.0
    
    # "Skills over experience" value: we can add a slight boost if they have high skills alignment
    # regardless of experience.
    
    return round(skill_alignment, 1)
