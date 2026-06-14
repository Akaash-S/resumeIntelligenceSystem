import json
import httpx
from loguru import logger
from backend.app.config import settings

def call_ollama(
    prompt: str,
    system_prompt: str = None,
    json_format: bool = False,
    timeout: float = 30.0
) -> str:
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    
    # Try llama3.2:1b first to prevent OOM errors on standard hardware, fallback to llama3
    models = ["llama3.2:1b", "llama3"]
    
    for model in models:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "seed": 42
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
        if json_format:
            payload["format"] = "json"
            
        try:
            logger.bind(stage="LLM").debug(f"Calling Ollama model {model} (timeout={timeout}s)...")
            response = httpx.post(url, json=payload, timeout=timeout)
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            elif response.status_code == 404:
                logger.bind(stage="LLM").warning(f"Ollama model '{model}' not found locally. Please run: ollama pull {model}")
            else:
                logger.bind(stage="LLM").warning(
                    f"Ollama {model} returned status code {response.status_code}: {response.text}"
                )
        except httpx.ConnectError:
            logger.bind(stage="LLM").error("Ollama connection failed. Is Ollama running?")
            raise ConnectionError("Ollama is offline. Please start Ollama locally.")
        except httpx.TimeoutException:
            logger.bind(stage="LLM").warning(f"Ollama {model} timed out after {timeout} seconds.")
            continue
        except Exception as e:
            logger.bind(stage="LLM").warning(f"Error calling Ollama model {model}: {e}")
            continue
            
    raise RuntimeError("All configured Ollama models failed or timed out. Please ensure Ollama is running and models are pulled (e.g. `ollama pull llama3`).")

def analyze_resume_text(raw_text: str) -> dict:
    logger.bind(stage="LLM").info("Running LLM analysis on raw resume text...")
    
    # Truncate text to avoid huge context processing times on local CPU
    truncated_text = raw_text[:12000]
    
    system_prompt = (
        "You are an expert recruitment parser. Extract candidate details from the resume raw text. "
        "You MUST respond ONLY with a JSON object. Do not include any explanation or markdown wrapping. "
        "Strictly adhere to this JSON format:\n"
        "{\n"
        '  "candidate_name": "Full Name (string)",\n'
        '  "experience_years": 5 (integer, approximate total years of work experience),\n'
        '  "skills": ["skill1", "skill2"] (list of strings, normalized to lowercase/clean text),\n'
        '  "education": ["degree1", "degree2"] (list of strings),\n'
        '  "certifications": ["cert1", "cert2"] (list of strings),\n'
        '  "projects": ["project description 1", "project description 2"] (list of strings)\n'
        "}"
    )
    
    prompt = f"Resume Raw Text:\n\n{truncated_text}\n\nExtract the JSON object:"
    
    try:
        response_str = call_ollama(prompt, system_prompt=system_prompt, json_format=True, timeout=180.0)
        parsed_data = json.loads(response_str)
        
        # Ensure correct types
        if not isinstance(parsed_data.get("skills"), list):
            parsed_data["skills"] = []
        if not isinstance(parsed_data.get("education"), list):
            parsed_data["education"] = []
        if not isinstance(parsed_data.get("certifications"), list):
            parsed_data["certifications"] = []
        if not isinstance(parsed_data.get("projects"), list):
            parsed_data["projects"] = []
            
        parsed_data["skills"] = [str(s).lower().strip() for s in parsed_data["skills"] if s]
        parsed_data["experience_years"] = int(parsed_data.get("experience_years") or 0)
        
        logger.bind(stage="LLM").info(f"Successfully extracted profile for candidate: {parsed_data.get('candidate_name')}")
        return parsed_data
    except Exception as e:
        logger.bind(stage="LLM").error(f"Failed to parse or clean LLM extraction: {e}")
        # Return empty structured schema as fallback
        return {
            "candidate_name": "Unknown Candidate",
            "experience_years": 0,
            "skills": [],
            "education": [],
            "certifications": [],
            "projects": []
        }

def generate_summary(raw_text: str, structured_data: dict) -> str:
    logger.bind(stage="LLM").info("Generating 2-3 sentence AI summary...")
    
    summary_prompt = (
        f"Candidate Name: {structured_data.get('candidate_name')}\n"
        f"Experience: {structured_data.get('experience_years')} years\n"
        f"Key Skills: {', '.join(structured_data.get('skills', [])[:8])}\n"
        f"Education: {', '.join(structured_data.get('education', []))}\n"
        f"Certifications: {', '.join(structured_data.get('certifications', []))}\n\n"
        f"Resume text context (first 2000 chars):\n{raw_text[:2000]}\n\n"
        "Write a concise, professional 2 to 3 sentence recruiter summary highlighting the candidate's core strengths, experience, and suitability. "
        "Do not include greeting, introductory filler, or metadata. Output ONLY the 2-3 sentence summary."
    )
    
    try:
        summary = call_ollama(summary_prompt, json_format=False, timeout=120.0)
        logger.bind(stage="LLM").info("AI summary generated successfully.")
        return summary
    except Exception as e:
        logger.bind(stage="LLM").warning(f"Summary generation timed out or failed: {e}. Falling back to score-only status.")
        return "Score-only status: AI summary generation timed out."

def parse_search_query(query: str) -> dict:
    logger.bind(stage="LLM").info(f"Extracting search parameters from query: '{query}'")
    
    system_prompt = (
        "You are an AI assistant parsing recruiter queries. "
        "Convert the search query into structural filters. Respond ONLY with a JSON object. "
        "No explanation. "
        "Strictly adhere to this format:\n"
        "{\n"
        '  "skills": ["python", "kubernetes"] (list of skills requested, in lowercase),\n'
        '  "experience_years": 3 (integer minimum years of experience, or 0 if not specified),\n'
        '  "certifications": ["aws", "pmp"] (list of certifications requested)\n'
        "}"
    )
    
    prompt = f"Query: \"{query}\"\nExtract structured filters:"
    
    try:
        response_str = call_ollama(prompt, system_prompt=system_prompt, json_format=True, timeout=60.0)
        parsed_query = json.loads(response_str)
        
        parsed_query["skills"] = [str(s).lower().strip() for s in parsed_query.get("skills", []) if s]
        parsed_query["certifications"] = [str(c).lower().strip() for c in parsed_query.get("certifications", []) if c]
        parsed_query["experience_years"] = int(parsed_query.get("experience_years") or 0)
        
        logger.bind(stage="LLM").debug(f"Parsed query requirements: {parsed_query}")
        return parsed_query
    except Exception as e:
        logger.bind(stage="LLM").error(f"Failed to parse query, using empty parameters fallback: {e}")
        return {
            "skills": [],
            "experience_years": 0,
            "certifications": []
        }
