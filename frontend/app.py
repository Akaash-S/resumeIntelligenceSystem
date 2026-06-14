import streamlit as st
import requests
import json
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="NexusFDE — Resume Intelligence System",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Dark Glassmorphism Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Apply globally */
    * {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* Main Container background */
    .stApp {
        background-color: #0d0f1a;
        background-image: 
            radial-gradient(at 10% 20%, rgba(99, 102, 241, 0.05) 0px, transparent 50%),
            radial-gradient(at 90% 10%, rgba(168, 85, 247, 0.05) 0px, transparent 50%);
        color: #e2e8f0;
    }

    /* Sidebar glassmorphic styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(22, 24, 47, 0.9) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
    }
    
    /* Glassmorphic card styling */
    .glass-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        transition: all 0.3s ease-in-out;
    }
    
    .glass-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.08);
        transform: translateY(-2px);
    }
    
    /* Metrics cards styling */
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        font-family: 'Outfit', sans-serif !important;
        background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-label {
        font-size: 14px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        background-color: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    
    .badge-cert {
        background-color: rgba(168, 85, 247, 0.15);
        color: #e9d5ff;
        border-color: rgba(168, 85, 247, 0.2);
    }

    /* Score badges */
    .score-circle {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 54px;
        height: 54px;
        border-radius: 50%;
        font-weight: 700;
        font-size: 16px;
        font-family: 'Outfit', sans-serif !important;
    }
    
    .score-high {
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 2px solid #22c55e;
        box-shadow: 0 0 15px rgba(34, 197, 94, 0.2);
    }

    .score-medium {
        background: rgba(234, 179, 8, 0.15);
        color: #fde047;
        border: 2px solid #eab308;
        box-shadow: 0 0 15px rgba(234, 179, 8, 0.2);
    }

    .score-low {
        background: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        border: 2px solid #ef4444;
    }

    /* Pulsing Green Indicator */
    .pulse-green {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #22c55e;
        box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7);
        animation: pulse 1.6s infinite;
        vertical-align: middle;
        margin-right: 8px;
    }

    .pulse-red {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #ef4444;
        box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
        animation: pulse-r 1.6s infinite;
        vertical-align: middle;
        margin-right: 8px;
    }
    
    @keyframes pulse {
        0% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7);
        }
        70% {
            transform: scale(1);
            box-shadow: 0 0 0 6px rgba(34, 197, 94, 0);
        }
        100% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(34, 197, 94, 0);
        }
    }

    @keyframes pulse-r {
        0% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
        }
        70% {
            transform: scale(1);
            box-shadow: 0 0 0 6px rgba(239, 68, 68, 0);
        }
        100% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
        }
    }
</style>
""", unsafe_allow_html=True)

BACKEND_URL = "http://127.0.0.1:8000"

# Sidebar Connection Check
def check_connection():
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5.0)
        if r.status_code in [200, 503]:
            return True, r.json().get("services", {})
        return False, None
    except Exception:
        return False, None

backend_active, services_health = check_connection()

# Sidebar Setup
with st.sidebar:
    st.image("https://img.icons8.com/?size=100&id=114322&format=png", width=64)
    st.markdown("<h2 style='margin-bottom:0px;'>NexusFDE</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; font-size:13px; margin-top:0px;'>Resume Intelligence System</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Navigation Option
    page = st.radio(
        "Navigation",
        [":material/dashboard: Dashboard", ":material/cloud_upload: Upload Resume", ":material/search: NL Search", ":material/compare: Compare Candidates"],
        index=0
    )
    st.markdown("---")
    
    # Health Indicators
    st.markdown("### System Health")
    if backend_active:
        st.markdown(f"<div><span class='pulse-green'></span>Backend Online</div>", unsafe_allow_html=True)
        # Services detail
        st.markdown(f"• SQLite DB: `{services_health.get('sqlite')}`")
        st.markdown(f"• Vector Store: `{services_health.get('chromadb')}`")
        st.markdown(f"• Ollama LLM: `{services_health.get('ollama')}`")
    else:
        st.markdown(f"<div><span class='pulse-red'></span>Backend Offline</div>", unsafe_allow_html=True)
        st.warning("FastAPI backend cannot be reached. Run `make start` in the repository root to boot up.", icon=":material/warning:")

# Initialize Session State
if "compare_list" not in st.session_state:
    st.session_state["compare_list"] = []

# --- PAGE RENDERING ---

if page == ":material/dashboard: Dashboard":
    st.markdown("<h1 style='background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Talent Database Dashboard</h1>", unsafe_allow_html=True)
    st.write("Aggregated overview of uploaded talent data, parsed indicators, and system metrics.")
    
    if not backend_active:
        st.info("System stats are unavailable when backend is offline.")
    else:
        try:
            stats = requests.get(f"{BACKEND_URL}/dashboard").json()
            
            # Row 1: Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class='glass-card'>
                    <div class='metric-label'>Total Resumes</div>
                    <div class='metric-value'>{stats.get('total_resumes', 0)}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class='glass-card'>
                    <div class='metric-label'>Average Experience</div>
                    <div class='metric-value'>{stats.get('average_experience', 0.0)} <span style='font-size:16px; color:#94a3b8;'>Years</span></div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                success_count = stats.get('status_counts', {}).get('success', 0)
                st.markdown(f"""
                <div class='glass-card'>
                    <div class='metric-label'>Successfully Parsed</div>
                    <div class='metric-value'>{success_count}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # Row 2: Skills & Searches
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("### Top 10 Database Skills")
                top_skills = stats.get('top_skills', {})
                if top_skills:
                    max_count = max(top_skills.values()) if top_skills.values() else 1
                    for skill, count in top_skills.items():
                        col_skill, col_progress = st.columns([1, 3])
                        with col_skill:
                            st.write(f"**{skill}**")
                        with col_progress:
                            st.progress(count / max_count, text=f"{count} Resumes")
                else:
                    st.write("No parsed skills found in the database. Upload some resumes first!")
                    
            with col_right:
                st.markdown("### Recent Recruiters Searches")
                recent_searches = stats.get('recent_searches', [])
                if recent_searches:
                    for s in recent_searches:
                        try:
                            # Format time
                            dt = datetime.fromisoformat(s['timestamp'])
                            time_str = dt.strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            time_str = s['timestamp']
                            
                        st.markdown(f"""
                        <div style='background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); border-radius:8px; padding:12px; margin-bottom:8px;'>
                            <div style='display:flex; justify-content:space-between; font-size:12px; color:#64748b;'>
                                <span>{time_str}</span>
                                <span>{s['results_count']} Matches</span>
                            </div>
                            <div style='font-weight:600; font-size:14px; margin-top:4px;'>"{s['query']}"</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write("No search logs recorded yet.")
                    
            # Row 3: Database Candidate Directory
            st.markdown("---")
            st.markdown("### 📋 Database Candidate Directory")
            
            try:
                r_resumes = requests.get(f"{BACKEND_URL}/resumes")
                if r_resumes.status_code == 200:
                    resumes_list = r_resumes.json().get("resumes", [])
                    if resumes_list:
                        # Header columns
                        col_hdr_name, col_hdr_file, col_hdr_exp, col_hdr_act = st.columns([2, 3, 1, 1])
                        with col_hdr_name:
                            st.markdown("**Candidate Name**")
                        with col_hdr_file:
                            st.markdown("**Filename**")
                        with col_hdr_exp:
                            st.markdown("**Experience**")
                        with col_hdr_act:
                            st.markdown("**Action**")
                        st.markdown("<hr style='margin:4px 0 12px 0; border-top:1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
                        
                        for r in resumes_list:
                            col_c_name, col_c_file, col_c_exp, col_c_act = st.columns([2, 3, 1, 1])
                            with col_c_name:
                                st.write(r.get("candidate_name") or "Unknown Candidate")
                            with col_c_file:
                                st.write(r.get("filename"))
                            with col_c_exp:
                                st.write(f"{r.get('experience_years', 0)} years")
                            with col_c_act:
                                if st.button("Delete 🗑️", key=f"del_db_{r['resume_id']}", type="secondary"):
                                    # Call delete route
                                    del_res = requests.delete(f"{BACKEND_URL}/resume/{r['resume_id']}")
                                    if del_res.status_code == 200:
                                        st.success(f"Deleted {r.get('candidate_name')}", icon=":material/check_circle:")
                                        st.rerun()
                                    else:
                                        st.error("Deletion failed.", icon=":material/error:")
                    else:
                        st.write("No resumes uploaded to the directory yet.")
                else:
                    st.error("Failed to query candidate directory from backend.", icon=":material/error:")
            except Exception as e:
                st.error(f"Error connecting to directory database: {e}", icon=":material/error:")
                    
        except Exception as e:
            st.error(f"Error fetching dashboard data: {e}", icon=":material/error:")

elif page == ":material/cloud_upload: Upload Resume":
    st.markdown("<h1 style='background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Upload Candidate Resumes</h1>", unsafe_allow_html=True)
    st.write("Drag and drop candidate files (PDF, DOCX, TXT) here. The system will parse text, fallback to OCR if needed, run structured LLM extraction, and store embeddings offline.")
    
    if not backend_active:
        st.error("Upload is disabled when backend service is offline.", icon=":material/error:")
    else:
        uploaded_files = st.file_uploader(
            "Select Resume Files", 
            type=["pdf", "docx", "txt"], 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button("Start Bulk Ingestion Pipeline", type="primary"):
                for uploaded_file in uploaded_files:
                    st.markdown(f"#### Processing **{uploaded_file.name}**...")
                    
                    status_area = st.empty()
                    status_area.info("Parsing document and running OCR fallback...", icon=":material/hourglass_empty:")
                    
                    try:
                        # Prepare files payload
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        
                        r = requests.post(f"{BACKEND_URL}/upload", files=files)
                        
                        if r.status_code == 200:
                            data = r.json()
                            if data.get("status") == "already_exists":
                                status_area.warning(f"Already processed. Existing candidate profile: **{data.get('candidate_name')}** (ID: `{data.get('resume_id')}`)", icon=":material/warning:")
                            else:
                                status_area.success(f"Successfully ingested: **{data.get('candidate_name')}**", icon=":material/check_circle:")
                                # Display Summary
                                st.markdown(f"""
                                <div class='glass-card'>
                                    <h4 style='margin-top:0px; color:#818cf8;'>AI Summary — Generated by llama3</h4>
                                    <p style='font-style:italic; font-size:14px; line-height:1.6;'>"{data.get('summary')}"</p>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            detail = r.json().get("detail", "Unknown backend parsing error.")
                            status_area.error(f"Failed to parse {uploaded_file.name}: {detail}", icon=":material/error:")
                    except Exception as e:
                        status_area.error(f"Error connecting to backend upload pipeline: {e}", icon=":material/error:")

elif page == ":material/search: NL Search":
    st.markdown("<h1 style='background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Natural Language Candidate Search</h1>", unsafe_allow_html=True)
    st.write("Type a natural language query describing target requirements (e.g. skills, experience years, certifications). The system will compute candidate matches based on a hybrid keyword-semantic ranking.")
    
    if not backend_active:
        st.error("Search is disabled when backend service is offline.", icon=":material/error:")
    else:
        # Search panel
        col_inp, col_th = st.columns([4, 1])
        with col_inp:
            query = st.text_input(
                "Search Query", 
                placeholder="e.g. Python backend developer with 3+ years experience, FastAPI, and AWS certification"
            )
        with col_th:
            threshold = st.slider("Minimum Score Threshold", min_value=10, max_value=90, value=40, step=5)
            
        if query:
            with st.spinner("Analyzing query and scoring database resumes..."):
                try:
                    r = requests.post(f"{BACKEND_URL}/search", json={"query_text": query})
                    if r.status_code == 200:
                        results = r.json().get("results", [])
                        
                        # Apply local frontend score filtering just in case
                        results = [c for c in results if c["total_score"] >= threshold]
                        
                        if not results:
                            st.info("No candidates matched the criteria with a score exceeding the threshold.", icon=":material/info:")
                        else:
                            st.success(f"Found {len(results)} matching candidates (Score ≥ {threshold})", icon=":material/check_circle:")
                            
                            # Render candidates in cards
                            for cand in results:
                                cid = cand["candidate_id"]
                                score = cand["total_score"]
                                
                                # Assign circular badge styling based on score
                                score_class = "score-high" if score >= 80 else "score-medium" if score >= 55 else "score-low"
                                
                                # Custom Card container
                                col_c1, col_c2 = st.columns([6, 1])
                                with col_c1:
                                    st.markdown(f"""
                                    <div style='margin-bottom:0px;'>
                                        <h3 style='margin-bottom: 2px; color:#818cf8;'>{cand['candidate_name']}</h3>
                                        <span style='font-size:12px; color:#64748b;'>Source file: {cand['filename']} | Experience: {cand['experience_years']} years</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Render badges
                                    st.markdown("<div style='margin-top: 8px;'>", unsafe_allow_html=True)
                                    # Skills
                                    for skill in cand["skills"][:10]:
                                        st.markdown(f"<span class='badge'>{skill}</span>", unsafe_allow_html=True)
                                    # Certs
                                    for cert in cand["certifications"]:
                                        st.markdown(f"<span class='badge badge-cert'>{cert}</span>", unsafe_allow_html=True)
                                    st.markdown("</div>", unsafe_allow_html=True)
                                    
                                    # AI Summary
                                    st.markdown(f"""
                                    <div style='margin-top:12px; margin-bottom:12px; border-left:3px solid rgba(168, 85, 247, 0.4); padding-left:14px; font-style:italic; font-size:13.5px; color:#cbd5e1;'>
                                        "{cand['summary']}"
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                with col_c2:
                                    st.markdown(f"""
                                    <div style='text-align: center; margin-top: 10px;'>
                                        <div class='score-circle {score_class}'>{score}</div>
                                        <div style='font-size:10px; color:#94a3b8; font-weight:600; text-transform:uppercase; margin-top:6px;'>Match Rank</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                # Detailed breakdown in expander
                                with st.expander("View Matching Explanations"):
                                    bd = cand["score_breakdown"]
                                    st.markdown("#### Weight Component Breakdowns:")
                                    st.write(f"• **Skills Match (55%)**: {bd.get('skills_score')}% / 100%")
                                    st.progress(bd.get("skills_score", 0.0) / 100.0)
                                    st.write(f"• **Semantic Text Similarity (25%)**: {bd.get('semantic_score')}% / 100%")
                                    st.progress(bd.get("semantic_score", 0.0) / 100.0)
                                    st.write(f"• **Experience Match (10%)**: {bd.get('experience_score')}% / 100%")
                                    st.progress(bd.get("experience_score", 0.0) / 100.0)
                                    st.write(f"• **Projects Keyword Reference (5%)**: {bd.get('projects_score')}% / 100%")
                                    st.progress(bd.get("projects_score", 0.0) / 100.0)
                                    st.write(f"• **Certifications Reference (5%)**: {bd.get('certifications_score')}% / 100%")
                                    st.progress(bd.get("certifications_score", 0.0) / 100.0)
                                
                                # Add/Remove from Comparison list
                                if cid not in st.session_state["compare_list"]:
                                    if st.button("Add to Comparison Matrix", key=f"add_{cid}"):
                                        st.session_state["compare_list"].append(cid)
                                        st.rerun()
                                else:
                                    if st.button("Remove from Comparison Matrix", key=f"rem_{cid}"):
                                        st.session_state["compare_list"].remove(cid)
                                        st.rerun()
                                st.markdown("---")
                                
                except Exception as e:
                    st.error(f"Error executing search query: {e}")

elif page == ":material/compare: Compare Candidates":
    st.markdown("<h1 style='background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Candidate Comparison Matrix</h1>", unsafe_allow_html=True)
    st.write("Compare selected candidates side-by-side. Add candidates from the 'NL Search' page to populate this list.")
    
    if not backend_active:
        st.error("Comparison is disabled when backend service is offline.", icon=":material/error:")
    elif not st.session_state["compare_list"]:
        st.info("No candidates selected for comparison yet. Please search for candidates and click 'Add to Comparison Matrix' to start comparing.", icon=":material/info:")
    else:
        st.markdown(f"Comparing **{len(st.session_state['compare_list'])}** selected candidates.")
        
        # Clear Button
        if st.button("Clear All Selections"):
            st.session_state["compare_list"] = []
            st.rerun()
            
        try:
            r = requests.post(f"{BACKEND_URL}/compare", json={"candidate_ids": st.session_state["compare_list"]})
            if r.status_code == 200:
                candidates = r.json().get("candidates", [])
                
                # Render comparative side-by-side cards using Streamlit columns
                cols = st.columns(len(candidates))
                for idx, col in enumerate(cols):
                    cand = candidates[idx]
                    cid = cand["resume_id"]
                    
                    with col:
                        st.markdown(f"""
                        <div class='glass-card' style='min-height: 550px;'>
                            <h3 style='margin-top:0px; color:#818cf8; text-align:center;'>{cand['candidate_name']}</h3>
                            <p style='font-size:12px; color:#64748b; text-align:center;'>{cand['filename']}</p>
                            <hr style='border-top:1px solid rgba(255,255,255,0.05); margin:12px 0;'>
                            
                            <div style='margin-bottom:12px;'>
                                <strong>Experience:</strong><br>
                                <span style='font-size:18px; font-weight:600; color:#e2e8f0;'>{cand['experience_years']} Years</span>
                            </div>
                            
                            <div style='margin-bottom:12px;'>
                                <strong>Top Skills:</strong><br>
                                <div style='margin-top:6px;'>
                                    {" ".join([f"<span class='badge'>{s}</span>" for s in cand['skills'][:6]])}
                                </div>
                            </div>
                            
                            <div style='margin-bottom:12px;'>
                                <strong>Certifications:</strong><br>
                                <div style='margin-top:6px;'>
                                    {" ".join([f"<span class='badge badge-cert'>{c}</span>" for c in cand['certifications']]) if cand['certifications'] else "<span style='font-size:12px; color:#64748b;'>None</span>"}
                                </div>
                            </div>
                            
                            <div style='margin-bottom:12px;'>
                                <strong>Education:</strong><br>
                                <span style='font-size:13px; color:#cbd5e1;'>{", ".join(cand['education']) if cand['education'] else "Not extracted"}</span>
                            </div>
                            
                            <div style='margin-bottom:12px;'>
                                <strong>AI Summary:</strong><br>
                                <span style='font-size:12.5px; font-style:italic; line-height:1.5; color:#cbd5e1;'>"{cand['summary'] or 'Summary not generated.'}"</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Remove button
                        if st.button("Remove Selections", key=f"comp_rem_{cid}"):
                            st.session_state["compare_list"].remove(cid)
                            st.rerun()
                            
        except Exception as e:
            st.error(f"Error building comparison data: {e}")
