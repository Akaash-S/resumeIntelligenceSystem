# NexusFDE — Resume Intelligence System

## WORKING PROTOTYPE BUILD SPECIFICATION (v3.0)

### Status

BUILD READY — PROTOTYPE LOCK

---

# 1. PRODUCT GOAL

Build a fully local AI-powered Resume Intelligence System that allows recruiters to:

* Upload resumes
* Parse and normalize content
* Store searchable embeddings
* Query candidates using natural language
* Rank candidates using explainable scoring
* Compare candidates
* Generate AI summaries
* Operate completely offline

Target:
A recruiter should receive usable candidate recommendations in under 3 seconds (excluding summary generation).

---

# 2. NON-NEGOTIABLE RULES

Priority Order:

1. Working System
2. Retrieval Accuracy
3. Reliability
4. UX
5. Architecture Beauty

Never violate:

* No cloud APIs
* No authentication
* No multi-user
* No admin panel
* No analytics dashboard
* No microservices

Single-machine prototype only.

---

# 3. FINAL ARCHITECTURE

Frontend:
Streamlit

Backend:
FastAPI

Communication:
HTTP (sync)

Storage:
SQLite
ChromaDB

AI:
Ollama

Models:

LLM:
llama3

Fallback:
llama3.2:1b

Embeddings:
nomic-embed-text

OCR:
pytesseract

---

FLOW

Upload

↓

Parse

↓

Normalize

↓

Chunk

↓

Embed

↓

Store

↓

Search

↓

Rank

↓

Summarize

↓

Render

---

# 4. SYSTEM REQUIREMENTS

Install:

Python 3.12

Tesseract

Ollama

Commands:

sudo apt install tesseract-ocr

curl -fsSL https://ollama.com/install.sh | sh

ollama pull llama3
ollama pull llama3.2:1b
ollama pull nomic-embed-text

---

# 5. FOLDER STRUCTURE

resume-intelligence/

backend/

frontend/

data/

runtime/

evaluation/

README.md

requirements.txt

Makefile

start.sh

.env

---

# 6. DATABASE DESIGN

SQLite:

resumes

searches

Columns:

resume_id

filename

candidate_name

experience_years

skills

education

certifications

upload_time

parse_status

resume_hash

---

# 7. RESUME PARSING

Supported:

PDF
DOCX
TXT

Pipeline:

PyPDF2

↓

pdfplumber

↓

OCR

↓

Failure

Extraction:

Name

Skills

Experience

Education

Projects

Certifications

Rules:

skills lowercase

deduplicate

experience integer years

---

# 8. CHUNKING

Section-aware

Sections:

summary

skills

experience

education

projects

certifications

Chunk:

300 tokens

Overlap:

50

---

# 9. VECTOR STORAGE

Store:

chunk

embedding

candidate

section

doc_id

source_file

Use cosine similarity.

---

# 10. SEARCH

Query

↓

Embed

↓

Retrieve top 10

↓

Rank

↓

Filter

↓

Summary

Threshold:

40

Return:

Top candidates only.

---

# 11. RANKING

Weights:

skills:
55

semantic:
25

experience:
10

projects:
5

certifications:
5

Tie:

skills

↓

recent upload

---

# 12. SUMMARY

Generate:

2–3 sentences

Timeout:

8 seconds

Fallback:

Score-only

---

# 13. API

POST /upload

DELETE /resume/{id}

POST /search

POST /compare

GET /dashboard

GET /health

---

# 14. STREAMLIT PAGES

Dashboard

Upload

Search

Compare

---

# 15. ERROR STATES

Unsupported file

Parse failure

Partial parse

No matches

Timeout

Ollama offline

Chroma failure

Backend offline

---

# 16. LOGGING

Loguru

Rich

Stages:

REQUEST

PARSE

CHUNK

EMBED

RETRIEVE

RANK

LLM

RESPONSE

---

# 17. EVALUATION

Golden resumes:

10

Queries:

5

Pass:

4/5

Latency:

<3 sec search

---

# 18. STARTUP

make install

make start

Open:

localhost:8501

---

# 19. SUCCESS CRITERIA

Upload works

Search works

Ranking works

Summary works

Compare works

Evaluation passes

No crashes

Prototype demo succeeds

---

END OF SPEC
