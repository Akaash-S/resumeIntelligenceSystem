import json
import httpx
from loguru import logger
from backend.app.config import settings
from backend.app.vector_store import query_vector_store
from backend.services.domain.knowledge_retriever import retrieve_company_knowledge
from backend.services.context.context_builder import build_context
from backend.services.prompt.prompt_builder import build_prompt

def ask_domain_agent(query_text: str) -> dict:
    """
    Orchestrates the Domain Intelligence Layer pipeline:
    Query -> Retrieve Resumes + Company Knowledge -> Context Fusion -> Prompt Builder -> Ollama -> Response
    """
    logger.bind(stage="DOMAIN").info(f"Processing query via Domain Agent: '{query_text}'")
    
    # 1. Retrieve Resumes
    try:
        resume_chunks = query_vector_store(query_text, n_results=10)
    except Exception as e:
        logger.bind(stage="DOMAIN").error(f"Failed to retrieve resumes: {e}")
        resume_chunks = []
        
    # 2. Retrieve Company Knowledge
    try:
        company_chunks = retrieve_company_knowledge(query_text, n_results=5)
    except Exception as e:
        logger.bind(stage="DOMAIN").error(f"Failed to retrieve company knowledge (Knowledge Timeout): {e}")
        company_chunks = []
        
    if not resume_chunks and not company_chunks:
        return {
            "answer": {"error": "Low Context: Could not find relevant resumes or company knowledge. Please ask the user to refine the query."},
            "sources": []
        }
        
    if not company_chunks:
        logger.bind(stage="DOMAIN").warning("No Knowledge retrieved. Falling back to Resume Only.")
        
    # 3. Build Context
    merged_context = build_context(resume_chunks, company_chunks)
    
    # 4. Build Prompt
    prompt = build_prompt(query_text, merged_context)
    
    # 5. Call Ollama
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        logger.bind(stage="DOMAIN").info("Calling Ollama without a timeout limit (waiting indefinitely)...")
        response = httpx.post(url, json=payload, timeout=None)
        response.raise_for_status()
        result_text = response.json().get("response", "{}")
        
        try:
            answer_json = json.loads(result_text)
        except json.JSONDecodeError:
            logger.bind(stage="DOMAIN").error("Failed to decode Ollama JSON response.")
            answer_json = {"raw_response": result_text}
            
    except Exception as e:
        logger.bind(stage="DOMAIN").error(f"Ollama generation failed: {e}")
        answer_json = {"error": "Failed to generate response from Ollama."}
        
    # Collect sources
    sources = []
    for c in company_chunks:
        sources.append({"type": "company_rule", "source": c.get("source"), "similarity": c.get("similarity")})
    for r in resume_chunks:
        sources.append({"type": "resume", "candidate": r.get("candidate"), "similarity": r.get("similarity")})
        
    return {
        "answer": answer_json,
        "sources": sources
    }
