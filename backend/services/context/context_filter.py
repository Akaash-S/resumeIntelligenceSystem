def filter_and_trim_chunks(chunks: list, max_tokens: int) -> list:
    """
    Filters chunks by similarity (if desired) and trims them so they fit within the allocated token budget.
    We approximate 1 token to 4 characters.
    """
    # Sort chunks by similarity descending
    sorted_chunks = sorted(chunks, key=lambda x: x.get('similarity', 0), reverse=True)
    
    selected_chunks = []
    current_tokens = 0
    
    for chunk in sorted_chunks:
        text = chunk.get('text', '')
        approx_tokens = len(text) // 4
        
        if current_tokens + approx_tokens <= max_tokens:
            selected_chunks.append(chunk)
            current_tokens += approx_tokens
        else:
            break
            
    return selected_chunks
