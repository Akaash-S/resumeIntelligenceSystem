from loguru import logger
from backend.services.prompt.system_prompt import SYSTEM_PROMPT_TEMPLATE

def build_prompt(user_query: str, merged_context: str) -> str:
    """Builds the final prompt string to be sent to Ollama."""
    
    prompt = f"""{SYSTEM_PROMPT_TEMPLATE}

Here is the retrieved context:
{merged_context}

User Query: {user_query}

Response (in strict JSON format):
"""
    logger.bind(stage="PROMPT").info(f"tokens={len(prompt)//4}")
    return prompt
