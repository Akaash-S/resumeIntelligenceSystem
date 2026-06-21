def merge_contexts(resume_chunks: list, company_chunks: list) -> str:
    """Merges resume and company chunks into a formatted context string."""
    
    context_lines = ["CONTEXT\n"]
    
    context_lines.append("Company Knowledge:")
    for chunk in company_chunks:
        source = chunk.get('source', 'Unknown')
        context_lines.append(f"Source: {source}")
        context_lines.append(chunk.get('text', ''))
        context_lines.append("")
        
    context_lines.append("Candidate Resumes:")
    for chunk in resume_chunks:
        candidate = chunk.get('candidate', 'Unknown')
        section = chunk.get('section', 'Unknown')
        context_lines.append(f"Candidate: {candidate} | Section: {section}")
        context_lines.append(chunk.get('text', ''))
        context_lines.append("")
        
    return "\n".join(context_lines)
