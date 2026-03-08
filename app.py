import streamlit as st
import sqlite3
import pandas as pd
import anthropic
import json
import re
import os
from datetime import datetime

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MediQuery AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
  }

  .main { background-color: #F7F9FC; }

  .stApp {
    background: linear-gradient(135deg, #F0F4FF 0%, #F7F9FC 60%, #EEF8F3 100%);
  }

  h1, h2, h3 {
    font-family: 'DM Serif Display', serif !important;
  }

  .hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.6rem;
    color: #0F1F3D;
    line-height: 1.2;
    margin-bottom: 0.2rem;
  }

  .hero-sub {
    font-size: 1rem;
    color: #556680;
    margin-bottom: 2rem;
  }

  .query-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 2px 12px rgba(15,31,61,0.07);
    border: 1px solid #E2E8F0;
    margin-bottom: 1rem;
  }

  .sql-block {
    background: #0F1F3D;
    color: #7EFFD4;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    font-family: 'Courier New', monospace;
    font-size: 0.88rem;
    line-height: 1.7;
    margin: 0.8rem 0;
    overflow-x: auto;
  }

  .insight-pill {
    background: linear-gradient(135deg, #E8F5E9, #E3F2FD);
    border-radius: 20px;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    color: #1B5E20;
    display: inline-block;
    margin: 0.3rem 0.2rem;
    border: 1px solid #A5D6A7;
  }

  .schema-tag {
    background: #EEF2FF;
    color: #3730A3;
    border-radius: 8px;
    padding: 0.2rem 0.6rem;
    font-size: 0.78rem;
    font-weight: 600;
    display: inline-block;
    margin: 0.15rem;
  }

  .metric-card {
    background: white;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    border-left: 4px solid #3B82F6;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
  }

  .example-btn {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 10px;
    padding: 0.6rem 1rem;
    color: #1D4ED8;
    font-size: 0.84rem;
    cursor: pointer;
    margin: 0.25rem 0;
    width: 100%;
    text-align: left;
  }

  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: #D1FAE5;
    color: #065F46;
    border-radius: 20px;
    padding: 0.3rem 0.8rem;
    font-size: 0.8rem;
    font-weight: 600;
  }

  div[data-testid="stSidebar"] {
    background: #0F1F3D !important;
  }

  div[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
  }

  div[data-testid="stSidebar"] h1,
  div[data-testid="stSidebar"] h2,
  div[data-testid="stSidebar"] h3 {
    color: white !important;
  }

  .stTextArea textarea {
    border-radius: 12px !important;
    border: 2px solid #E2E8F0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
  }

  .stTextArea textarea:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
  }

  .stButton > button {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
  }
</style>
""", unsafe_allow_html=True)

# ─── DB Setup ────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE patients (
        patient_id INTEGER PRIMARY KEY,
        first_name TEXT, last_name TEXT,
        age INTEGER, gender TEXT,
        blood_type TEXT, city TEXT,
        insurance TEXT, admitted_date TEXT
    );
    CREATE TABLE diagnoses (
        diagnosis_id INTEGER PRIMARY KEY,
        patient_id INTEGER, icd_code TEXT,
        condition_name TEXT, severity TEXT,
        diagnosed_date TEXT, diagnosed_by TEXT
    );
    CREATE TABLE medications (
        med_id INTEGER PRIMARY KEY,
        patient_id INTEGER, drug_name TEXT,
        dosage TEXT, frequency TEXT,
        start_date TEXT, end_date TEXT,
        prescribed_by TEXT
    );
    CREATE TABLE lab_results (
        lab_id INTEGER PRIMARY KEY,
        patient_id INTEGER, test_name TEXT,
        result_value REAL, unit TEXT,
        reference_low REAL, reference_high REAL,
        test_date TEXT, status TEXT
    );
    CREATE TABLE appointments (
        appt_id INTEGER PRIMARY KEY,
        patient_id INTEGER, doctor_name TEXT,
        department TEXT, appt_date TEXT,
        appt_type TEXT, status TEXT, notes TEXT
    );
    """)

    import random
    random.seed(42)
    conditions = [("Hypertension","I10","Moderate"),("Type 2 Diabetes","E11","Moderate"),
                  ("Asthma","J45","Mild"),("COPD","J44","Severe"),("Heart Failure","I50","Severe"),
                  ("Pneumonia","J18","Moderate"),("Depression","F32","Mild"),("Anxiety","F41","Mild"),
                  ("Chronic Kidney Disease","N18","Severe"),("Migraine","G43","Mild")]
    drugs = ["Metformin","Lisinopril","Atorvastatin","Omeprazole","Amlodipine",
             "Albuterol","Furosemide","Sertraline","Gabapentin","Warfarin"]
    tests = [("HbA1c",4.0,5.6,"%"),("Blood Glucose",70,100,"mg/dL"),
             ("Creatinine",0.6,1.2,"mg/dL"),("Hemoglobin",12,17,"g/dL"),
             ("WBC",4.5,11.0,"K/uL"),("eGFR",60,120,"mL/min")]
    cities = ["Toronto","Sudbury","Ottawa","Hamilton","London","Barrie","Windsor","Kingston"]
    insurances = ["OHIP","Blue Cross","Sun Life","Manulife","Green Shield"]
    depts = ["Cardiology","Endocrinology","Pulmonology","Nephrology","General Practice","Neurology"]
    doctors = ["Dr. Singh","Dr. Chen","Dr. Patel","Dr. Williams","Dr. Okonkwo","Dr. Tremblay"]
    first_names = ["James","Maria","Robert","Linda","David","Sarah","Michael","Emma","John","Olivia",
                   "Priya","Arjun","Fatima","Wei","Carlos","Sofia","Ahmed","Yuki","Amara","Lucas"]
    last_names = ["Smith","Johnson","Brown","Garcia","Wilson","Taylor","Anderson","Martin","Lee","Kumar"]

    for i in range(1, 201):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        age = random.randint(18, 90)
        gender = random.choice(["Male","Female","Other"])
        bt = random.choice(["A+","A-","B+","B-","O+","O-","AB+","AB-"])
        city = random.choice(cities)
        ins = random.choice(insurances)
        yr = random.randint(2020,2024)
        mo = random.randint(1,12)
        dy = random.randint(1,28)
        admitted = f"{yr}-{mo:02d}-{dy:02d}"
        cur.execute("INSERT INTO patients VALUES (?,?,?,?,?,?,?,?,?)",
                    (i,fn,ln,age,gender,bt,city,ins,admitted))

        # 1-3 diagnoses
        for _ in range(random.randint(1,3)):
            cond = random.choice(conditions)
            cur.execute("INSERT INTO diagnoses(patient_id,icd_code,condition_name,severity,diagnosed_date,diagnosed_by) VALUES (?,?,?,?,?,?)",
                (i,cond[1],cond[0],cond[2],admitted,random.choice(doctors)))

        # 1-3 meds
        for _ in range(random.randint(1,3)):
            cur.execute("INSERT INTO medications(patient_id,drug_name,dosage,frequency,start_date,end_date,prescribed_by) VALUES (?,?,?,?,?,?,?)",
                (i,random.choice(drugs),f"{random.choice([5,10,20,25,50,100])}mg",
                 random.choice(["Once daily","Twice daily","As needed"]),
                 admitted, f"{yr+1}-{mo:02d}-{dy:02d}", random.choice(doctors)))

        # 2-4 lab results
        for _ in range(random.randint(2,4)):
            t = random.choice(tests)
            val = round(random.uniform(t[1]*0.7, t[2]*1.4), 2)
            status = "Normal" if t[1] <= val <= t[2] else ("High" if val > t[2] else "Low")
            cur.execute("INSERT INTO lab_results(patient_id,test_name,result_value,unit,reference_low,reference_high,test_date,status) VALUES (?,?,?,?,?,?,?,?)",
                (i,t[0],val,t[3],t[1],t[2],admitted,status))

        # 1-2 appointments
        for _ in range(random.randint(1,2)):
            cur.execute("INSERT INTO appointments(patient_id,doctor_name,department,appt_date,appt_type,status,notes) VALUES (?,?,?,?,?,?,?)",
                (i,random.choice(doctors),random.choice(depts),admitted,
                 random.choice(["Follow-up","Initial","Emergency","Routine"]),
                 random.choice(["Completed","Scheduled","Cancelled"]),
                 "Routine check"))

    conn.commit()
    return conn

# ─── Schema ──────────────────────────────────────────────────────────────────
SCHEMA = """
DATABASE SCHEMA (Healthcare System — 200 patients, Ontario Canada):

TABLE: patients
  patient_id (PK), first_name, last_name, age (int), gender, blood_type,
  city (Toronto/Sudbury/Ottawa/etc.), insurance (OHIP/Blue Cross/Sun Life/Manulife/Green Shield),
  admitted_date

TABLE: diagnoses
  diagnosis_id (PK), patient_id (FK), icd_code, condition_name
  (Hypertension/Type 2 Diabetes/Asthma/COPD/Heart Failure/Pneumonia/Depression/Anxiety/Chronic Kidney Disease/Migraine),
  severity (Mild/Moderate/Severe), diagnosed_date, diagnosed_by

TABLE: medications
  med_id (PK), patient_id (FK), drug_name, dosage, frequency, start_date, end_date, prescribed_by

TABLE: lab_results
  lab_id (PK), patient_id (FK), test_name (HbA1c/Blood Glucose/Creatinine/Hemoglobin/WBC/eGFR),
  result_value (real), unit, reference_low, reference_high, test_date, status (Normal/High/Low)

TABLE: appointments
  appt_id (PK), patient_id (FK), doctor_name, department, appt_date,
  appt_type (Follow-up/Initial/Emergency/Routine), status (Completed/Scheduled/Cancelled), notes
"""

EXAMPLES = [
    "How many patients have severe COPD?",
    "Which city has the most patients with Heart Failure?",
    "List all patients over 65 with abnormal HbA1c results",
    "What is the average age of diabetic patients by gender?",
    "Which doctor has prescribed Metformin the most?",
    "Show me patients with both Hypertension and Chronic Kidney Disease",
    "What percentage of appointments were cancelled last year?",
    "Which insurance provider covers the most patients with severe conditions?",
]

# ─── NL→SQL via Claude ───────────────────────────────────────────────────────
def generate_sql(question: str, client: anthropic.Anthropic) -> dict:
    prompt = f"""You are a healthcare data analyst. Convert the natural language question into a SQLite SQL query.

{SCHEMA}

Rules:
- Use only tables and columns listed above
- Always use table aliases for clarity
- Limit results to 100 rows max unless asked otherwise
- Use proper JOINs when crossing tables
- Return ONLY a JSON object with keys: "sql" (string), "explanation" (1 sentence), "insight_type" (one of: Count, Trend, Comparison, List, Aggregate)

Question: {question}

JSON response:"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)


def generate_insight(question: str, df: pd.DataFrame, client: anthropic.Anthropic) -> str:
    if df.empty:
        return "No data returned for this query."
    summary = df.head(10).to_string(index=False)
    prompt = f"""You are a clinical data analyst. Given this question and query results, write a 2-sentence business insight.
Be specific with numbers. Focus on what matters clinically or operationally.

Question: {question}
Data sample:
{summary}
Total rows: {len(df)}

Insight (2 sentences max):"""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


# ─── App Layout ──────────────────────────────────────────────────────────────
conn = get_db()

# Sidebar
with st.sidebar:
    st.markdown("## 🏥 MediQuery AI")
    st.markdown("*Natural Language → SQL for Healthcare Data*")
    st.markdown("---")

    api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
    st.markdown("---")

    st.markdown("### 📋 Database")
    st.markdown('<span class="schema-tag">patients</span><span class="schema-tag">diagnoses</span><span class="schema-tag">medications</span><span class="schema-tag">lab_results</span><span class="schema-tag">appointments</span>', unsafe_allow_html=True)
    st.markdown("**200** simulated Ontario patients")
    st.markdown("---")

    st.markdown("### 💡 Try These")
    for ex in EXAMPLES:
        if st.button(f"→ {ex[:45]}...", key=ex, use_container_width=True):
            st.session_state["query_input"] = ex

    st.markdown("---")
    st.markdown("**Built with:** Claude API · SQLite · Streamlit")
    st.markdown("**Domain:** Ontario Healthcare Analytics")

# Main area
st.markdown('<p class="hero-title">MediQuery AI</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Ask questions about patient data in plain English — get SQL, results, and clinical insights instantly.</p>', unsafe_allow_html=True)

# Stats row
col1, col2, col3, col4 = st.columns(4)
counts = {
    "Patients": conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
    "Diagnoses": conn.execute("SELECT COUNT(*) FROM diagnoses").fetchone()[0],
    "Lab Results": conn.execute("SELECT COUNT(*) FROM lab_results").fetchone()[0],
    "Appointments": conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
}
colors = ["#3B82F6","#10B981","#F59E0B","#8B5CF6"]
for col, (label, val), color in zip([col1,col2,col3,col4], counts.items(), colors):
    with col:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color:{color}">
          <div style="font-size:1.6rem;font-weight:700;color:{color}">{val:,}</div>
          <div style="font-size:0.82rem;color:#64748B;font-weight:500">{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Query input
default_q = st.session_state.get("query_input", "")
question = st.text_area(
    "Ask a clinical or operational question:",
    value=default_q,
    height=90,
    placeholder="e.g. Which patients over 60 have both diabetes and abnormal kidney function tests?",
    key="main_input"
)

run_col, clear_col, _ = st.columns([1.5, 1, 5])
with run_col:
    run = st.button("⚡ Generate & Run", type="primary", use_container_width=True)
with clear_col:
    if st.button("Clear", use_container_width=True):
        st.session_state["query_input"] = ""
        st.rerun()

# ─── Run Query ───────────────────────────────────────────────────────────────
if run and question.strip():
    if not api_key:
        st.error("⚠️ Please enter your Anthropic API key in the sidebar.")
    else:
        client = anthropic.Anthropic(api_key=api_key)

        with st.spinner("Generating SQL with Claude..."):
            try:
                result = generate_sql(question, client)
                sql = result.get("sql", "")
                explanation = result.get("explanation", "")
                insight_type = result.get("insight_type", "Query")

                st.markdown("---")
                left, right = st.columns([3, 2])

                with left:
                    st.markdown("#### Generated SQL")
                    st.markdown(f'<div class="sql-block">{sql}</div>', unsafe_allow_html=True)
                    st.markdown(f"**Query type:** `{insight_type}` · *{explanation}*")

                with right:
                    st.markdown("#### Query Breakdown")
                    tables_used = [t for t in ["patients","diagnoses","medications","lab_results","appointments"] if t in sql.lower()]
                    st.markdown("**Tables used:**")
                    st.markdown(" ".join([f'<span class="schema-tag">{t}</span>' for t in tables_used]), unsafe_allow_html=True)

                # Execute
                try:
                    df = pd.read_sql_query(sql, conn)
                    st.markdown("---")
                    st.markdown(f"#### Results <span style='font-size:0.85rem;color:#64748B;font-weight:400'>— {len(df)} rows returned</span>", unsafe_allow_html=True)

                    if not df.empty:
                        st.dataframe(df, use_container_width=True, height=min(400, 50 + len(df)*35))

                        # AI Insight
                        with st.spinner("Generating clinical insight..."):
                            insight = generate_insight(question, df, client)
                        st.markdown(f"""
                        <div class="query-card" style="border-left:4px solid #10B981">
                          <div style="font-size:0.78rem;font-weight:700;color:#10B981;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem">🔍 Clinical Insight</div>
                          <div style="color:#1E293B;font-size:0.95rem;line-height:1.6">{insight}</div>
                        </div>""", unsafe_allow_html=True)

                        # Download
                        csv = df.to_csv(index=False).encode()
                        st.download_button("⬇ Download Results as CSV", csv,
                                         f"mediquery_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                         "text/csv")
                    else:
                        st.info("Query ran successfully but returned no results.")

                except Exception as e:
                    st.error(f"SQL execution error: {e}")
                    st.code(sql, language="sql")

            except Exception as e:
                st.error(f"Could not generate SQL: {e}")

elif run:
    st.warning("Please enter a question first.")

# History hint
st.markdown("---")
st.markdown('<div style="text-align:center;color:#94A3B8;font-size:0.8rem">MediQuery AI · Powered by Claude · Built by Rinkesh Patel · Healthcare Analytics Portfolio Project</div>', unsafe_allow_html=True)
