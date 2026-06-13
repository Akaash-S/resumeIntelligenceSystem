import re
import httpx
from loguru import logger
import chromadb
from backend.app.config import chroma_db_abs, settings

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path=str(chroma_db_abs))
collection = chroma_client.get_or_create_collection(
    name="resume_chunks",
    metadata={"hnsw:space": "cosine"}  # Cosine similarity metric
)

def get_embedding(text: str) -> list:
    url = f"{settings.OLLAMA_BASE_URL}/api/embeddings"
    payload = {
        "model": "nomic-embed-text",
        "prompt": text
    }
    try:
        response = httpx.post(url, json=payload, timeout=15.0)
        if response.status_code == 200:
            embedding = response.json().get("embedding")
            if embedding:
                return embedding
            raise ValueError("No embedding vector returned in JSON response.")
        else:
            raise RuntimeError(f"Ollama embeddings returned status {response.status_code}: {response.text}")
    except httpx.ConnectError:
        logger.bind(stage="EMBED").error("Ollama connection failed. Embeddings cannot be generated.")
        raise ConnectionError("Ollama is offline. Start Ollama to generate embeddings.")
    except Exception as e:
        logger.bind(stage="EMBED").error(f"Error generating embedding via Ollama: {e}")
        raise e

def split_sections(text: str) -> dict:
    headings = {
        "summary": ["summary", "profile", "professional summary", "about me", "objective", "career objective"],
        "skills": ["skills", "technical skills", "core competencies", "technologies", "expertise", "skills & tools"],
        "experience": ["experience", "work experience", "employment history", "professional experience", "work history", "history"],
        "education": ["education", "academic background", "academic qualifications", "qualifications", "academic record"],
        "projects": ["projects", "key projects", "academic projects", "personal projects", "recent projects"],
        "certifications": ["certifications", "licenses", "certifications & licenses", "courses", "credentials"]
    }
    
    lines = text.split("\n")
    current_section = "summary"
    sections = {k: [] for k in headings.keys()}
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Check if line is a potential section heading
        found_heading = False
        if len(stripped) < 40:
            stripped_lower = stripped.lower().strip(":-. ")
            for sec_name, keywords in headings.items():
                for kw in keywords:
                    pattern = rf"^\b{re.escape(kw)}\b"
                    if re.match(pattern, stripped_lower):
                        current_section = sec_name
                        found_heading = True
                        break
                if found_heading:
                    break
                    
        if not found_heading:
            sections[current_section].append(line)
            
    # Join text for each section
    return {k: "\n".join(v).strip() for k, v in sections.items() if v}

def chunk_text(text: str, chunk_size: int = 250, overlap: int = 40) -> list:
    words = text.split()
    chunks = []
    if len(words) <= chunk_size:
        return [" ".join(words)]
        
    step = chunk_size - overlap
    if step <= 0:
        step = chunk_size // 2
        
    for i in range(0, len(words), step):
        chunk = words[i:i + chunk_size]
        chunks.append(" ".join(chunk))
        if i + chunk_size >= len(words):
            break
    return chunks

def index_resume(
    resume_id: str,
    filename: str,
    candidate_name: str,
    raw_text: str
):
    logger.bind(stage="CHUNK").info(f"Chunking and indexing resume ID: {resume_id}")
    
    # 1. Section-aware splitting
    sections = split_sections(raw_text)
    
    chunks_to_add = []
    metadata_to_add = []
    ids_to_add = []
    embeddings_to_add = []
    
    chunk_index = 0
    for section_name, section_text in sections.items():
        # 2. Token-approximate chunking
        section_chunks = chunk_text(section_text, chunk_size=250, overlap=40)
        
        logger.bind(stage="CHUNK").debug(
            f"Section '{section_name}' split into {len(section_chunks)} chunks."
        )
        
        for i, chunk in enumerate(section_chunks):
            if not chunk.strip():
                continue
                
            # 3. Generate embedding
            logger.bind(stage="EMBED").debug(
                f"Generating embedding for chunk {chunk_index} (section: {section_name})..."
            )
            embedding = get_embedding(chunk)
            
            chunk_id = f"{resume_id}_chunk_{chunk_index}"
            
            metadata = {
                "doc_id": resume_id,
                "source_file": filename,
                "candidate": candidate_name or "Unknown Candidate",
                "section": section_name,
                "chunk_text": chunk  # store text inside metadata to retrieve it easily if needed
            }
            
            chunks_to_add.append(chunk)
            metadata_to_add.append(metadata)
            ids_to_add.append(chunk_id)
            embeddings_to_add.append(embedding)
            
            chunk_index += 1
            
    if ids_to_add:
        logger.bind(stage="EMBED").info(
            f"Storing {len(ids_to_add)} chunks into ChromaDB for resume {filename}."
        )
        collection.add(
            ids=ids_to_add,
            embeddings=embeddings_to_add,
            metadatas=metadata_to_add,
            documents=chunks_to_add
        )
        logger.bind(stage="EMBED").info(f"Ingestion successful for resume ID {resume_id}.")
    else:
        logger.bind(stage="CHUNK").warning(f"No chunks extracted from resume {filename}.")

def delete_resume_vectors(resume_id: str):
    logger.bind(stage="DATABASE").info(f"Deleting vector chunks for resume ID: {resume_id}")
    # Chroma delete supports filtering by metadata
    collection.delete(where={"doc_id": resume_id})
    logger.bind(stage="DATABASE").info(f"Deleted resume ID {resume_id} chunks from ChromaDB.")

def query_vector_store(query_text: str, n_results: int = 10) -> list:
    logger.bind(stage="RETRIEVE").info(f"Querying vector store for: '{query_text}'")
    query_emb = get_embedding(query_text)
    
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=n_results
    )
    
    matches = []
    if not results or not results["ids"] or not results["ids"][0]:
        logger.bind(stage="RETRIEVE").info("No chunks retrieved.")
        return matches
        
    ids = results["ids"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]
    documents = results["documents"][0]
    
    for i in range(len(ids)):
        # Convert ChromaDB distance (cosine distance) to cosine similarity
        # Cosine distance = 1 - Cosine similarity. Thus, similarity = 1 - distance.
        distance = distances[i]
        similarity = 1.0 - distance
        
        matches.append({
            "chunk_id": ids[i],
            "doc_id": metadatas[i]["doc_id"],
            "source_file": metadatas[i]["source_file"],
            "candidate": metadatas[i]["candidate"],
            "section": metadatas[i]["section"],
            "text": documents[i],
            "similarity": similarity
        })
        
    logger.bind(stage="RETRIEVE").info(f"Retrieved {len(matches)} match chunks from ChromaDB.")
    return matches
