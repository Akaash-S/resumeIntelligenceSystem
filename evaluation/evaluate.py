import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from backend.app.config import logger
from backend.app.database import init_db, list_resumes, get_connection
from backend.app.parser import get_file_hash
from backend.app.analyzer import analyze_resume_text, generate_summary
from backend.app.vector_store import index_resume
from backend.app.matcher import rank_candidates

GOLDEN_RESUMES_DIR = PROJECT_ROOT / "evaluation" / "golden_resumes"
GOLDEN_RESUMES_DIR.mkdir(parents=True, exist_ok=True)

# Define 10 golden profiles to generate
GOLDEN_PROFILES = [
    {
        "filename": "alice_smith_python.txt",
        "name": "Alice Smith",
        "text": """
        ALICE SMITH
        Email: alice.smith@example.com | Phone: 123-456-7890
        
        SUMMARY:
        Results-oriented Python Software Engineer with 5 years of experience building scalable web applications. Expert in FastAPI, Docker, and AWS cloud deployments.
        
        EXPERIENCE:
        Software Engineer at TechCorp (2021 - Present)
        - Developed REST APIs using Python and FastAPI.
        - Containerized applications using Docker.
        - Managed cloud infrastructure on AWS (EC2, S3, RDS).
        
        SKILLS:
        python, fastapi, docker, aws, sql, postgresql, git
        
        EDUCATION:
        BS in Computer Science, State University, 2021
        
        CERTIFICATIONS:
        AWS Certified Solutions Architect
        """
    },
    {
        "filename": "bob_jones_java.txt",
        "name": "Bob Jones",
        "text": """
        BOB JONES
        Email: bob.jones@example.com | Phone: 234-567-8901
        
        SUMMARY:
        Senior Backend Developer specializing in Java, Spring Boot, and cloud architecture. 8 years of experience building high-throughput microservices.
        
        EXPERIENCE:
        Senior Java Developer at CloudSolutions (2018 - Present)
        - Re-architected monolith application to microservices with Java and Spring Boot.
        - Managed Kubernetes clusters and deployments on Google Cloud Platform (GCP).
        
        SKILLS:
        java, spring boot, kubernetes, gcp, docker, maven, postgresql
        
        EDUCATION:
        MS in Computer Science, Tech Institute, 2018
        
        CERTIFICATIONS:
        Google Certified Professional Cloud Architect
        """
    },
    {
        "filename": "charlie_brown_frontend.txt",
        "name": "Charlie Brown",
        "text": """
        CHARLIE BROWN
        Email: charlie.b@example.com
        
        SUMMARY:
        Frontend Web Developer with 2 years of experience specializing in React, TypeScript, and responsive design systems using Tailwind CSS.
        
        EXPERIENCE:
        Frontend Developer at WebLabs (2024 - Present)
        - Built interactive user interfaces using React and TypeScript.
        - Styled components with Tailwind CSS for pixel-perfect designs.
        
        SKILLS:
        react, typescript, tailwind css, javascript, html, css, node.js
        
        EDUCATION:
        BS in Information Technology, City College, 2024
        
        CERTIFICATIONS:
        Meta Front-End Developer Professional Certificate
        """
    },
    {
        "filename": "david_green_data_science.txt",
        "name": "David Green",
        "text": """
        DAVID GREEN, PhD
        Email: david.green@example.com
        
        SUMMARY:
        Data Scientist with 4 years of experience applying machine learning algorithms to complex datasets. Expert in PyTorch, SQL, and pandas.
        
        EXPERIENCE:
        Data Scientist at DataAI Corp (2022 - Present)
        - Developed and deployed deep learning models using PyTorch.
        - Written complex SQL queries for data aggregation.
        - Analyzed structural datasets using pandas and numpy.
        
        SKILLS:
        python, machine learning, pytorch, sql, pandas, numpy, scikit-learn
        
        EDUCATION:
        PhD in Data Science, Research University, 2022
        
        CERTIFICATIONS:
        TensorFlow Developer Certificate
        """
    },
    {
        "filename": "eva_white_pm.txt",
        "name": "Eva White",
        "text": """
        EVA WHITE, PMP
        Email: eva.w@example.com
        
        SUMMARY:
        Senior Project Manager with 10 years of experience leading agile software development teams. Professional Scrum Master and PMP certified.
        
        EXPERIENCE:
        Project Manager at Global Tech (2016 - Present)
        - Managed software delivery cycles using Scrum and Kanban.
        - Used Jira for project tracking and backlog grooming.
        
        SKILLS:
        project management, agile, scrum, jira, pmp, communication, leadership
        
        EDUCATION:
        MBA in Technology Management, Business School, 2016
        
        CERTIFICATIONS:
        PMP - Project Management Professional, Professional Scrum Master (PSM I)
        """
    },
    {
        "filename": "frank_black_embedded.txt",
        "name": "Frank Black",
        "text": """
        FRANK BLACK
        Email: frank.b@example.com
        
        SUMMARY:
        Embedded Systems Engineer with 6 years of experience writing firmware, low-level drivers, and working with real-time operating systems (RTOS).
        
        EXPERIENCE:
        Embedded Engineer at ChipDevices (2020 - Present)
        - Written C++ and C firmware for microcontrollers.
        - Designed and implemented custom drivers using FreeRTOS.
        
        SKILLS:
        c, c++, embedded systems, rtos, firmware, freertos, spi, i2c
        
        EDUCATION:
        BS in Electrical Engineering, Polytechnic, 2020
        
        CERTIFICATIONS:
        Embedded Systems Certified Professional
        """
    },
    {
        "filename": "grace_miller_django.txt",
        "name": "Grace Miller",
        "text": """
        GRACE MILLER
        Email: grace.m@example.com
        
        SUMMARY:
        Full Stack Developer with 3 years of experience. Strong background in Python, Django, PostgreSQL, and basic frontend technologies.
        
        EXPERIENCE:
        Full Stack Developer at SoftGroup (2023 - Present)
        - Maintained Python Django backend applications.
        - Wrote PostgreSQL migrations and queries.
        
        SKILLS:
        python, django, postgresql, html, css, javascript, git
        
        EDUCATION:
        BS in Software Engineering, University of Software, 2023
        """
    },
    {
        "filename": "henry_wilson_golang.txt",
        "name": "Henry Wilson",
        "text": """
        HENRY WILSON
        Email: henry.w@example.com
        
        SUMMARY:
        Systems Engineer with 4 years of experience building high performance microservices using Go, gRPC, and container orchestration.
        
        EXPERIENCE:
        Systems Engineer at ScaledSystems (2022 - Present)
        - Developed Go-based backends utilizing gRPC APIs.
        - Managed Docker container networking.
        
        SKILLS:
        go, golang, grpc, docker, aws, microservices, linux
        
        EDUCATION:
        MS in Software Engineering, Science State, 2022
        
        CERTIFICATIONS:
        Certified Kubernetes Administrator (CKA)
        """
    },
    {
        "filename": "ivy_taylor_security.txt",
        "name": "Ivy Taylor",
        "text": """
        IVY TAYLOR, CISSP
        Email: ivy.t@example.com
        
        SUMMARY:
        Cyber Security Engineer with 7 years of experience securing cloud systems, networks, and deploying firewalls. CISSP certified.
        
        EXPERIENCE:
        Security Engineer at SecureNet (2019 - Present)
        - Configured and monitored corporate firewalls and IDS.
        - Conducted threat modeling on cloud network topologies.
        
        SKILLS:
        cyber security, cissp, firewalls, network security, threat modeling, linux
        
        EDUCATION:
        BS in Cyber Security, Tech College, 2019
        
        CERTIFICATIONS:
        CISSP - Certified Information Systems Security Professional
        """
    },
    {
        "filename": "jack_davis_php.txt",
        "name": "Jack Davis",
        "text": """
        JACK DAVIS
        Email: jack.d@example.com
        
        SUMMARY:
        Junior Web Developer with 1 year of experience building custom PHP and Laravel applications. Enthusiastic self-learner.
        
        EXPERIENCE:
        Web Developer at WebDev Shop (2025 - Present)
        - Developed custom modules in PHP and Laravel.
        - Styled interfaces using Bootstrap.
        
        SKILLS:
        php, laravel, mysql, bootstrap, html, css, javascript
        
        EDUCATION:
        High School Diploma, Self-Taught Developer
        """
    }
]

def generate_golden_resumes():
    logger.info("Generating 10 golden resume files...")
    for profile in GOLDEN_PROFILES:
        filepath = GOLDEN_RESUMES_DIR / profile["filename"]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(profile["text"].strip())
    logger.info("Golden resumes generated successfully.")

def ingest_golden_resumes():
    logger.info("Ingesting golden resumes directly into database and ChromaDB...")
    
    # Empty existing DB values to run a clean evaluation
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM resumes")
    conn.commit()
    conn.close()
    
    # Delete all items in vector store collection
    from backend.app.vector_store import collection
    try:
        collection.delete()
    except Exception:
        pass
        
    for profile in GOLDEN_PROFILES:
        filename = profile["filename"]
        raw_text = profile["text"].strip()
        file_hash = get_file_hash(raw_text.encode("utf-8"))
        
        logger.info(f"Ingesting profile: {profile['name']}...")
        
        # We simulate the extraction results
        structured_profile = analyze_resume_text(raw_text)
        
        from backend.app.database import save_resume
        resume_id = save_resume(
            filename=filename,
            resume_hash=file_hash,
            candidate_name=profile["name"],
            experience_years=structured_profile.get("experience_years", 0),
            skills=structured_profile.get("skills", []),
            education=structured_profile.get("education", []),
            certifications=structured_profile.get("certifications", []),
            projects=structured_profile.get("projects", []),
            parse_status="success",
            raw_text=raw_text,
            summary=None
        )
        
        index_resume(
            resume_id=resume_id,
            filename=filename,
            candidate_name=profile["name"],
            raw_text=raw_text
        )
        
        # Add a placeholder summary
        from backend.app.database import update_resume_summary
        update_resume_summary(resume_id, f"Summary placeholder for {profile['name']}")
        
    logger.info("All 10 golden resumes ingested.")

# 5 standard queries
EVAL_QUERIES = [
    {
        "query": "Python developer with experience in FastAPI and AWS, Docker",
        "expected_top": "Alice Smith"
    },
    {
        "query": "Senior Java Developer with GCP or Kubernetes",
        "expected_top": "Bob Jones"
    },
    {
        "query": "Data scientist who knows PyTorch and Machine Learning",
        "expected_top": "David Green"
    },
    {
        "query": "Project Manager with PMP certification",
        "expected_top": "Eva White"
    },
    {
        "query": "Cybersecurity expert with CISSP certification",
        "expected_top": "Ivy Taylor"
    }
]

def run_evaluation() -> bool:
    logger.info("Starting query evaluation...")
    passes = 0
    total = len(EVAL_QUERIES)
    
    for idx, q_item in enumerate(EVAL_QUERIES):
        query_text = q_item["query"]
        expected = q_item["expected_top"]
        
        start_time = time.time()
        results = rank_candidates(query_text)
        latency = time.time() - start_time
        
        logger.info(f"Query {idx + 1}: '{query_text}'")
        logger.info(f"Latency: {latency:.4f} seconds")
        
        if not results:
            logger.error(f"FAIL: No candidates returned. Expected: {expected}")
            continue
            
        top_candidate = results[0]["candidate_name"]
        top_score = results[0]["total_score"]
        
        logger.info(f"Top Returned candidate: {top_candidate} (Score: {top_score})")
        
        # Check if the expected candidate is the top candidate
        # (or in case of equal scores, expected is within the top candidates)
        matched = False
        if top_candidate.lower() == expected.lower():
            matched = True
        else:
            # Check if there is a score tie and the expected candidate matches the tie score
            tied_matches = [c for c in results if c["total_score"] == top_score]
            for c in tied_matches:
                if c["candidate_name"].lower() == expected.lower():
                    matched = True
                    break
                    
        # Check latency threshold
        latency_ok = latency < 3.0
        
        if matched and latency_ok:
            logger.info(f"PASS: Query {idx + 1} succeeded.")
            passes += 1
        else:
            if not matched:
                logger.error(f"FAIL: Wrong ranking. Top returned: {top_candidate}, expected: {expected}")
            if not latency_ok:
                logger.error(f"FAIL: Search took {latency:.2f}s, exceeding 3.0s limit.")
                
        logger.info("-" * 40)
        
    logger.info(f"Evaluation finished: {passes}/{total} queries passed.")
    
    # Pass criteria: at least 4 out of 5 queries succeed
    success = (passes >= 4)
    if success:
        logger.info("SUCCESS CRITERIA MET (>= 4/5 queries passed).")
    else:
        logger.error("SUCCESS CRITERIA FAILED (< 4/5 queries passed).")
        
    return success

def main():
    logger.info("Initializing Evaluation Environment...")
    init_db()
    
    generate_golden_resumes()
    
    try:
        ingest_golden_resumes()
        success = run_evaluation()
        sys.exit(0 if success else 1)
    except ConnectionError:
        logger.error("Failed to run evaluation because Ollama connection is offline.")
        logger.error("Please run the local Ollama backend before running this script.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error running evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
