from loguru import logger
from backend.app.vector_store import get_embedding, company_collection

def retrieve_company_knowledge(query_text: str, n_results: int = 5) -> list:
    """Retrieves relevant company knowledge chunks for a given query."""
    logger.bind(stage="RETRIEVE").info(f"Querying company knowledge for: '{query_text}'")
    try:
        query_emb = get_embedding(query_text)
        
        results = company_collection.query(
            query_embeddings=[query_emb],
            n_results=n_results
        )
        
        matches = []
        if not results or not results["ids"] or not results["ids"][0]:
            logger.bind(stage="RETRIEVE").info("No company knowledge chunks retrieved.")
            return matches
            
        ids = results["ids"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]
        documents = results["documents"][0]
        
        for i in range(len(ids)):
            distance = distances[i]
            similarity = 1.0 - distance
            
            matches.append({
                "chunk_id": ids[i],
                "source": metadatas[i].get("source", "unknown"),
                "type": metadatas[i].get("type", "unknown"),
                "text": documents[i],
                "similarity": similarity
            })
            
        logger.bind(stage="RETRIEVE").info(f"Retrieved {len(matches)} company knowledge chunks.")
        return matches
    except Exception as e:
        logger.bind(stage="RETRIEVE").error(f"Error querying company knowledge: {e}")
        return []
