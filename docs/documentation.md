# NexusFDE — Resume Intelligence System

## 1. Project Overview
NexusFDE is an AI-powered Resume Intelligence System designed to streamline the recruitment process. It allows HR professionals and recruiters to upload candidate resumes, automatically extract structured data using local Large Language Models (LLMs), and query the talent pool using Natural Language (NL) searches.

The system is built on a modern, local-first AI stack ensuring that candidate data remains private and is processed entirely on the host machine without relying on external cloud APIs.

## 2. Architecture & Technology Stack
The application employs a dual-service architecture:

- **Frontend:** Streamlit (Python)
- **Backend:** FastAPI (Python)
- **Database:** SQLite (Local relational storage)
- **AI Engine:** Ollama (Local LLM inference, utilizing `llama3.2:1b` or `llama3`)

### 2.1 Backend Implementation (`backend/`)
The FastAPI backend serves as the core intelligence engine. 
- **`main.py`**: Exposes REST API endpoints (`/upload`, `/search`, `/compare`, `/dashboard`, `/resumes`).
- **`database.py`**: Manages the SQLite database schemas. It stores raw resume text, LLM-extracted structured JSON (skills, education, certifications, projects), parsed status, and recruiter search logs.
- **`analyzer.py`**: Interacts with the local Ollama instance. It takes raw text extracted from uploaded documents and prompts the LLM to return a strictly formatted JSON object containing candidate metadata. It also generates a 2-3 sentence professional summary for quick candidate review.
- **Text Extraction Pipeline**: Supports processing `.pdf`, `.docx`, and `.txt` files, extracting raw text and falling back to OCR if necessary before passing the payload to the LLM.

### 2.2 Frontend Implementation (`frontend/app.py`)
The Streamlit application provides a highly polished, interactive UI featuring glassmorphic design and dynamic light/dark mode theming.
- **Dashboard**: Displays aggregated metrics (Total Resumes, Average Experience), parsed status counts, top database skills, and recent recruiter searches. It also includes a Candidate Directory table for quick actions (like deleting profiles).
- **Upload Resume**: Provides a drag-and-drop interface for bulk ingestion. Real-time indicators show the parsing and LLM-extraction progress.
- **NL Search**: Allows recruiters to type natural language queries (e.g., "Python developer with AWS and 3 years experience"). The backend ranks candidates using a hybrid semantic/keyword scoring system, and the frontend displays matching profiles with visual score badges.
- **Compare Candidates**: A side-by-side matrix allowing recruiters to easily contrast experience, top skills, certifications, education, and AI-generated summaries of shortlisted candidates.

## 3. Setup and Execution

### Prerequisites
1. **Python 3.10+**
2. **Ollama**: Installed and running locally.
3. **Local LLM**: Pulled via Ollama (e.g., `ollama pull llama3.2:1b`).

### Starting the System
The system is orchestrated using a unified startup script:
```bash
python start.py
```
This script spawns two processes:
1. **Uvicorn server** running the FastAPI backend on `http://127.0.0.1:8000`.
2. **Streamlit server** running the frontend on `http://localhost:8501`.

## 4. Output Demonstration

### Dashboard Insights
When accessing the application, the user is greeted by the Dashboard. Metrics automatically calculate the average experience across all successful parses. The "Top 10 Database Skills" progress bars dynamically update based on the frequency of skills extracted across the entire candidate pool.

### AI Extraction & Summary
Upon uploading a resume (e.g., `Candidate_Resume.pdf`):
1. The backend extracts the raw text.
2. Ollama processes the text and extracts: `{"candidate_name": "John Doe", "experience_years": 5, "skills": ["python", "fastapi"]}`.
3. A 2-3 sentence AI summary is generated.
4. The frontend displays: *"Successfully ingested: John Doe"* along with the AI-generated summary box.

### Natural Language Matching
If a recruiter searches for *"Backend engineer with Python"*:
1. The query is sent to the backend and processed by the LLM to extract structural filters.
2. The candidates are scored based on skill overlap, semantic text similarity, and experience requirements.
3. The UI presents cards with match ranks (e.g., `85 Match Rank` in a green circle), showing weight component breakdowns for transparency.

### Comparison Matrix
By clicking "Compare ⚖️" on multiple candidates in the search results, the recruiter can navigate to the Compare tab. Here, candidate data is fetched via the `/compare` endpoint and mapped into side-by-side native Streamlit containers, making it visually effortless to decide who to advance in the hiring pipeline.
