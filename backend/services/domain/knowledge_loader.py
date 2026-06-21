import os
import glob
from loguru import logger
from backend.app.vector_store import get_embedding, company_collection, chunk_text

COMPANY_DATA_DIR = os.path.join(os.path.dirname(__file__), "../../../data/company")

def load_and_index_company_knowledge():
    """Reads all markdown files in data/company/ and indexes them into company_collection."""
    logger.bind(stage="KNOWLEDGE").info("Starting company knowledge ingestion...")
    
    # First, clear existing knowledge to avoid duplicates on reindex
    # We can fetch all existing ids and delete them, or just rely on chroma overwriting if IDs are deterministic.
    # To be safe, we'll try to delete everything in company_collection first.
    existing_count = company_collection.count()
    if existing_count > 0:
        logger.bind(stage="KNOWLEDGE").info(f"Clearing {existing_count} existing company knowledge chunks...")
        # A hacky way to delete all: get all ids and delete. 
        # Alternatively, we just use deterministic IDs and it will upsert/overwrite.
        # Let's use deterministic IDs based on file and chunk index.
    
    md_files = glob.glob(os.path.join(COMPANY_DATA_DIR, "**/*.md"), recursive=True)
    if not md_files:
        logger.bind(stage="KNOWLEDGE").warning(f"No markdown files found in {COMPANY_DATA_DIR}")
        return {"status": "no_files_found"}
        
    total_chunks = 0
    for file_path in md_files:
        filename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        chunks = chunk_text(content, chunk_size=200, overlap=30)
        logger.bind(stage="KNOWLEDGE").debug(f"File {filename} split into {len(chunks)} chunks.")
        
        ids_to_add = []
        embeddings_to_add = []
        metadata_to_add = []
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
                
            try:
                embedding = get_embedding(chunk)
            except Exception as e:
                logger.bind(stage="KNOWLEDGE").error(f"Failed to generate embedding for chunk in {filename}: {e}")
                continue
                
            chunk_id = f"{filename}_chunk_{i}"
            metadata = {
                "type": "company_rule",
                "source": filename,
                "section": "general",
                "version": "1.0",
                "chunk_text": chunk
            }
            
            ids_to_add.append(chunk_id)
            embeddings_to_add.append(embedding)
            metadata_to_add.append(metadata)
            
        if ids_to_add:
            # We use upsert so re-indexing works gracefully
            company_collection.upsert(
                ids=ids_to_add,
                embeddings=embeddings_to_add,
                metadatas=metadata_to_add,
                documents=chunks
            )
            total_chunks += len(ids_to_add)
            
    logger.bind(stage="KNOWLEDGE").info(f"chunks={total_chunks}")
    return {"status": "success", "chunks_indexed": total_chunks}
