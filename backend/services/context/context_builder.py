from loguru import logger
from backend.services.context.context_filter import filter_and_trim_chunks
from backend.services.context.context_merger import merge_contexts

def build_context(resume_chunks: list, company_chunks: list, max_tokens: int = 4000) -> str:
    """
    Algorithm:
    Retrieve Resume Chunks + Retrieve Company Chunks ->
    Score -> Sort -> Merge -> Trim -> Return
    """
    logger.bind(stage="CONTEXT").info(f"Building context: {len(resume_chunks)} resume chunks, {len(company_chunks)} company chunks")
    
    # In a full implementation, we might re-score here. For now, they are pre-scored by ChromaDB similarity.
    
    # Sort and filter
    filtered_resume_chunks = filter_and_trim_chunks(resume_chunks, max_tokens // 2)
    filtered_company_chunks = filter_and_trim_chunks(company_chunks, max_tokens // 2)
    
    merged_context = merge_contexts(filtered_resume_chunks, filtered_company_chunks)
    
    # Basic token approximation (1 token ~= 4 chars)
    if len(merged_context) > max_tokens * 4:
        logger.bind(stage="CONTEXT").info(f"Trimming merged context to {max_tokens} tokens limit.")
        merged_context = merged_context[:max_tokens * 4]
        
    logger.bind(stage="CONTEXT").info(f"merged={len(filtered_resume_chunks) + len(filtered_company_chunks)}")
    return merged_context
