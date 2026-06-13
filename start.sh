#!/bin/bash
# Start backend
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
# Start frontend
streamlit run frontend/app.py --server.port 8501
